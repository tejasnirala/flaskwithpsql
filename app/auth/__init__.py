"""
JWT Authentication Configuration and Utilities.

This module provides JWT-based authentication using Flask-JWT-Extended.
It handles token generation, validation, and user identity management.

JWT Flow:
---------
1. User logs in with email/password
2. Server validates credentials and returns access_token + refresh_token
3. Client includes access_token in Authorization header for protected routes
4. When access_token expires, client uses refresh_token to get new tokens

Token Types:
-----------
- Access Token: Short-lived (15 min), used for API requests
- Refresh Token: Long-lived (30 days), used to get new access tokens

Security Features:
-----------------
- Tokens are signed with SECRET_KEY (never share this!)
- Tokens include user identity and claims
- Blacklist support for logged-out tokens
- CSRF protection for cookie-based tokens

Usage:
    from app.auth import create_tokens, jwt_required, get_current_user

    @app.route("/protected")
    @jwt_required()
    def protected():
        user = get_current_user()
        return {"message": f"Hello {user.username}"}
"""

import logging
from datetime import timedelta
from functools import wraps
from typing import Dict, Optional

from flask import Flask
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
)
from flask_jwt_extended import jwt_required as _jwt_required
from flask_jwt_extended import verify_jwt_in_request

from app.models.user import User
from app.utils.responses import ErrorCode, error_response

logger = logging.getLogger(__name__)

# Initialize JWT Manager (will be configured in init_jwt)
jwt = JWTManager()

# In-memory token blacklist (use Redis in production)
# This stores JTI (JWT ID) of revoked tokens
_token_blacklist = set()


def init_jwt(app: Flask) -> None:
    """
    Initialize JWT authentication with the Flask app.

    Configures:
    - Token expiration times
    - Token locations (headers, cookies)
    - Error handlers
    - User lookup callback

    Args:
        app: Flask application instance
    """
    # JWT Configuration
    app.config.setdefault("JWT_SECRET_KEY", app.config.get("SECRET_KEY"))
    app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", timedelta(minutes=15))
    app.config.setdefault("JWT_REFRESH_TOKEN_EXPIRES", timedelta(days=30))
    app.config.setdefault("JWT_TOKEN_LOCATION", ["headers"])
    app.config.setdefault("JWT_HEADER_NAME", "Authorization")
    app.config.setdefault("JWT_HEADER_TYPE", "Bearer")

    # Initialize the extension
    jwt.init_app(app)

    # Register callbacks
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """
        Convert user object to identity for token.

        Called when creating a token. Converts User to a simple ID.
        """
        if isinstance(user, User):
            return user.id
        return user

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """
        Load user from the database using token identity.

        Called on each request to protected endpoint.
        Returns the User object for get_current_user().
        """
        identity = jwt_data["sub"]
        return User.query.filter_by(id=identity, is_deleted=False).first()

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """
        Check if a token has been revoked (logged out).

        Uses in-memory blacklist for development.
        Use Redis in production for distributed systems.
        """
        jti = jwt_payload["jti"]
        return jti in _token_blacklist

    # Error handlers for JWT errors
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired tokens."""
        return error_response(
            code=ErrorCode.TOKEN_EXPIRED,
            message="Token has expired",
            status_code=401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid tokens."""
        return error_response(
            code=ErrorCode.TOKEN_INVALID,
            message="Invalid token",
            status_code=401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing tokens."""
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="Authorization token required",
            status_code=401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked (blacklisted) tokens."""
        return error_response(
            code=ErrorCode.TOKEN_INVALID,
            message="Token has been revoked",
            status_code=401,
        )

    logger.info("JWT authentication initialized")


def create_tokens(user: User) -> Dict[str, str]:
    """
    Create access and refresh tokens for a user.

    Args:
        user: The User object to create tokens for

    Returns:
        Dict containing 'access_token' and 'refresh_token'

    Example:
        tokens = create_tokens(user)
        return jsonify({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"]
        })
    """
    # Add custom claims to the token
    additional_claims = {
        "username": user.username,
        "email": user.email,
    }

    access_token = create_access_token(
        identity=user,
        additional_claims=additional_claims,
    )
    refresh_token = create_refresh_token(identity=user)

    logger.info(f"Tokens created for user_id={user.id}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


def revoke_token(jti: str) -> None:
    """
    Revoke a token by adding its JTI to the blacklist.

    Args:
        jti: The JWT ID of the token to revoke
    """
    _token_blacklist.add(jti)
    logger.info(f"Token revoked: jti={jti[:8]}...")


def get_current_user() -> Optional[User]:
    """
    Get the current authenticated user.

    Must be called within a protected route (after @jwt_required).

    Returns:
        User object or None if not authenticated
    """
    from flask_jwt_extended import current_user

    return current_user


def get_current_user_id() -> Optional[int]:
    """
    Get the current authenticated user's ID.

    Faster than get_current_user() as it doesn't hit the database.

    Returns:
        User ID or None
    """
    try:
        return get_jwt_identity()
    except Exception:
        return None


# Re-export jwt_required for convenience
jwt_required = _jwt_required


def admin_required():
    """
    Decorator for routes that require admin privileges.

    Usage:
        @app.route("/admin/users")
        @admin_required()
        def admin_users():
            ...

    Note: This is a placeholder. Implement proper role checking.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if not user:
                return error_response(
                    code=ErrorCode.UNAUTHORIZED,
                    message="Authentication required",
                    status_code=401,
                )
            # TODO: Add proper role checking
            # if not user.is_admin:
            #     return error_response(
            #         code=ErrorCode.FORBIDDEN,
            #         message="Admin privileges required",
            #         status_code=403,
            #     )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
