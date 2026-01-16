"""
Auth Service - Business logic for authentication operations.

This service layer separates authentication business logic from route handlers,
making the code more testable, maintainable, and reusable.

Why AuthService?
----------------
1. **Separation of Concerns**: Routes handle HTTP, services handle business logic
2. **Testability**: Services can be unit tested without HTTP overhead
3. **Reusability**: Same logic can be used from CLI scripts, background jobs, etc.
4. **Consistency**: Same pattern as UserService, RBACService, etc.

Usage:
    from app.services.auth_service import AuthService

    # Login a user
    result = AuthService.login(email, password)

    # Logout (revoke token)
    AuthService.logout(jti)

    # Refresh tokens
    tokens = AuthService.refresh_tokens(user)
"""

import logging
from typing import Any, Dict

from app.auth import create_tokens, revoke_token
from app.models.user import User
from app.schemas.user import UserResponseSchema
from app.services.user_service import InvalidCredentialsError, UserService

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================


class AuthServiceError(Exception):
    """Base exception for auth service errors."""

    pass


class UserNotAuthenticatedError(AuthServiceError):
    """Raised when user is not authenticated or not found."""

    pass


class TokenRevocationError(AuthServiceError):
    """Raised when token revocation fails."""

    pass


# =============================================================================
# Auth Service
# =============================================================================


class AuthService:
    """
    Service class for authentication operations.

    This class encapsulates all business logic related to:
    - User login (authentication + token generation)
    - User logout (token revocation)
    - Token refresh
    - Current user info retrieval

    All methods are static since we don't need instance state.
    The service is stateless - all state is in the database or JWT infrastructure.
    """

    @staticmethod
    def login(email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate a user and generate JWT tokens.

        This method handles the complete login flow:
        1. Authenticate user credentials via UserService
        2. Generate access and refresh tokens
        3. Format user data for response

        Args:
            email: User's email address
            password: User's plaintext password

        Returns:
            Dict containing:
                - access_token: JWT access token
                - refresh_token: JWT refresh token
                - token_type: "Bearer"
                - user: Dict with user information

        Raises:
            InvalidCredentialsError: If email/password combination is invalid
                (same error for user not found OR wrong password to prevent enumeration)

        Example:
            try:
                result = AuthService.login("john@example.com", "password123")
                # result = {
                #     "access_token": "eyJ...",
                #     "refresh_token": "eyJ...",
                #     "token_type": "Bearer",
                #     "user": {"id": 1, "username": "john", ...}
                # }
            except InvalidCredentialsError:
                # Handle invalid credentials
        """
        logger.info("Login attempt initiated")

        # Step 1: Authenticate user (raises InvalidCredentialsError on failure)
        # Note: UserService.authenticate returns same error for user not found
        # AND wrong password to prevent email enumeration attacks
        user = UserService.authenticate(email, password)

        # Step 2: Generate tokens
        tokens = create_tokens(user)

        # Step 3: Format user data
        user_data = UserResponseSchema.model_validate(user).to_dict()

        logger.info(f"Login successful for user_id={user.id}")

        return {
            **tokens,
            "user": user_data,
        }

    @staticmethod
    def logout(jti: str) -> None:
        """
        Logout by revoking (blacklisting) a token.

        The token is added to a blacklist and cannot be used for
        authentication anymore.

        Args:
            jti: The JWT ID (jti claim) of the token to revoke.
                 This is a unique identifier for each JWT.

        Note:
            - Currently uses in-memory blacklist (development only!)
            - In production, should use Redis for distributed systems
            - Client should also discard both access and refresh tokens

        Example:
            from flask_jwt_extended import get_jwt

            jti = get_jwt()["jti"]
            AuthService.logout(jti)
        """
        logger.info("Logout initiated")

        revoke_token(jti)

        logger.info("Logout successful - token revoked")

    @staticmethod
    def refresh_tokens(user: User) -> Dict[str, str]:
        """
        Generate new tokens for a user (token refresh flow).

        This is called when a client uses their refresh token to get
        new access and refresh tokens.

        Args:
            user: The authenticated User object (from refresh token)

        Returns:
            Dict containing:
                - access_token: New JWT access token
                - refresh_token: New JWT refresh token
                - token_type: "Bearer"

        Raises:
            UserNotAuthenticatedError: If user is None

        Example:
            user = get_current_user()
            if user:
                tokens = AuthService.refresh_tokens(user)
        """
        if not user:
            logger.warning("Token refresh failed: user not found")
            raise UserNotAuthenticatedError("User not found")

        logger.info(f"Refreshing tokens for user_id={user.id}")

        tokens = create_tokens(user)

        logger.info(f"Tokens refreshed successfully for user_id={user.id}")

        return tokens

    @staticmethod
    def get_current_user_info(user: User) -> Dict[str, Any]:
        """
        Get formatted user information for the current authenticated user.

        This method formats the user data using the UserResponseSchema,
        ensuring consistent response format.

        Args:
            user: The authenticated User object

        Returns:
            Dict containing user information (id, username, email, etc.)

        Raises:
            UserNotAuthenticatedError: If user is None

        Example:
            user = get_current_user()
            if user:
                user_info = AuthService.get_current_user_info(user)
        """
        if not user:
            logger.warning("Get user info failed: user not found")
            raise UserNotAuthenticatedError("User not found")

        logger.debug(f"Fetching user info for user_id={user.id}")

        return UserResponseSchema.model_validate(user).to_dict()

    @staticmethod
    def register(
        username: str,
        email: str,
        password: str,
        first_name: str,
        middle_name: str = None,
        last_name: str = None,
        bio: str = None,
    ) -> Dict[str, Any]:
        """
        Register a new user account.

        This method wraps UserService.create_user to provide a more
        convenient interface for registration.

        Args:
            username: Unique username (will be lowercased)
            email: Unique email address
            password: Password (will be hashed)
            first_name: User's first name
            middle_name: Optional middle name
            last_name: Optional last name
            bio: Optional user biography

        Returns:
            Dict containing the created user's information

        Raises:
            UserAlreadyExistsError: If username or email already exists

        Note:
            This method delegates to UserService.create_user for the actual
            user creation. We could expand this in the future to:
            - Auto-login after registration
            - Send welcome email
            - Create initial settings
        """
        from app.schemas.user import UserCreateSchema

        logger.info(f"Registration attempt for username={username}")

        # Create schema for validation
        user_data = UserCreateSchema(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            bio=bio,
        )

        # Delegate to UserService
        user = UserService.create_user(user_data)

        logger.info(f"Registration successful for user_id={user.id}")

        return UserResponseSchema.model_validate(user).to_dict()
