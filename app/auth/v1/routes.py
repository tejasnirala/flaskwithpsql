"""
Authentication Routes - Login, Logout, Token Refresh (API v1).

These routes handle JWT-based authentication:
- POST /api/v1/auth/register  - Create new user account
- POST /api/v1/auth/login     - Get tokens with email/password
- POST /api/v1/auth/logout    - Revoke current token
- POST /api/v1/auth/refresh   - Get new access token using refresh token
- GET  /api/v1/auth/me        - Get current user info

Version: 1
Prefix: /api/v1/auth
"""

import logging
from typing import Any, Dict, Optional

from flask_jwt_extended import get_jwt, jwt_required
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, EmailStr, Field

from app.auth import create_tokens, get_current_user, revoke_token
from app.schemas import UserCreateSchema, UserResponseSchema
from app.services import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
)
from app.utils.rate_limiter import api_limit
from app.utils.responses import (
    ErrorCode,
    StandardErrorResponse,
    StandardSuccessResponse,
    error_response,
    success_response,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Blueprint Setup
# =============================================================================

tag = Tag(name="Authentication (v1)", description="JWT authentication endpoints - Version 1")

# APIBlueprint with just the resource prefix
# Version prefix (/api/v1) is added during registration in app/__init__.py
auth_bp_v1 = APIBlueprint(
    "auth_v1",  # Unique name for v1
    __name__,
    url_prefix="/auth",  # Just the resource - version added at registration
    abp_tags=[tag],
)


# =============================================================================
# Request/Response Schemas
# =============================================================================


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")


class TokenResponse(StandardSuccessResponse):
    """Token response schema."""

    class TokenData(BaseModel):
        access_token: str = Field(..., description="JWT access token")
        refresh_token: str = Field(..., description="JWT refresh token")
        token_type: str = Field(default="Bearer", description="Token type")
        user: Optional[Dict[str, Any]] = Field(None, description="User information")

    data: Optional[TokenData] = Field(..., description="Token data")


class UserInfoResponse(StandardSuccessResponse):
    """Current user info response."""

    data: Optional[Dict[str, Any]] = Field(..., description="User information")


class UserDataResponse(StandardSuccessResponse):
    """Single user data response - extends standard success response."""

    data: Optional[Dict[str, Any]] = Field(
        ..., description="User data object containing user information"
    )


# =============================================================================
# Routes
# =============================================================================


@auth_bp_v1.post(
    "/register",
    summary="Register New User",
    description="""
Creates a new user account.

**Validation Rules:**
- Username: 3-80 characters, alphanumeric and underscore only
- Email: Must be valid email format
- Password: 8-128 characters, must contain uppercase, lowercase, and digit
- First name: Required, 1-50 characters
- Middle name: Optional, max 50 characters
- Last name: Optional, max 50 characters
- Bio: Optional, max 500 characters

**Automatic Transformations:**
- Username is converted to lowercase
- Names are converted to title case
    """,
    responses={
        201: UserDataResponse,
        409: StandardErrorResponse,
        422: StandardErrorResponse,
    },
)
@api_limit
def register_user(body: UserCreateSchema):
    """
    Create a new user.

    Delegates to UserService for business logic.
    """
    try:
        user = UserService.create_user(body)
        response_data = UserResponseSchema.model_validate(user)
        return success_response(
            data=response_data.to_dict(),
            message="User created successfully",
            status_code=201,
        )
    except UserAlreadyExistsError as e:
        return error_response(
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message=f"{e.field.title()} already exists",
            status_code=409,
        )


@auth_bp_v1.post(
    "/login",
    summary="Login",
    description="""
Authenticate with email and password to receive JWT tokens.

Returns:
- **access_token**: Short-lived token for API requests (15 min default)
- **refresh_token**: Long-lived token for getting new access tokens (30 days default)

Usage:
Include the access_token in the Authorization header for protected routes:
```
Authorization: Bearer <access_token>
```
    """,
    responses={
        200: TokenResponse,
        401: StandardErrorResponse,
        404: StandardErrorResponse,
    },
)
def login(body: LoginRequest):
    """
    Login and get JWT tokens.
    """
    try:
        user = UserService.authenticate(body.email, body.password)
        tokens = create_tokens(user)

        # Include user info in response
        user_data = UserResponseSchema.model_validate(user).to_dict()

        return success_response(
            data={
                **tokens,
                "user": user_data,
            },
            message="Login successful",
        )
    except UserNotFoundError:
        return error_response(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="User not found",
            status_code=404,
        )
    except InvalidCredentialsError:
        return error_response(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="Invalid password",
            status_code=401,
        )


@auth_bp_v1.post(
    "/logout",
    summary="Logout",
    description="""
Revoke the current access token.

The token will be added to a blacklist and cannot be used again.
Client should also discard the refresh token.
    """,
    responses={
        200: StandardSuccessResponse,
        401: StandardErrorResponse,
    },
    security=[{"jwt": []}],  # Requires JWT authentication
)
@jwt_required()
def logout():
    """
    Logout and revoke current token.
    """
    jti = get_jwt()["jti"]
    revoke_token(jti)

    logger.info("User logged out successfully")

    return success_response(message="Logout successful")


@auth_bp_v1.post(
    "/refresh",
    summary="Refresh Token",
    description="""
Get a new access token using a valid refresh token.

Include the refresh_token in the Authorization header:
```
Authorization: Bearer <refresh_token>
```
    """,
    responses={
        200: TokenResponse,
        401: StandardErrorResponse,
    },
    security=[{"jwt": []}],  # Requires JWT (refresh token)
)
@jwt_required(refresh=True)
def refresh():
    """
    Get new access token using refresh token.
    """
    user = get_current_user()
    if not user:
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="User not found",
            status_code=401,
        )

    tokens = create_tokens(user)

    return success_response(
        data=tokens,
        message="Token refreshed",
    )


@auth_bp_v1.get(
    "/me",
    summary="Get Current User",
    description="Get the currently authenticated user's information.",
    responses={
        200: UserInfoResponse,
        401: StandardErrorResponse,
    },
    security=[{"jwt": []}],  # Requires JWT authentication
)
@jwt_required()
def get_me():
    """
    Get current user info.
    """
    user = get_current_user()
    if not user:
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="User not found",
            status_code=401,
        )

    user_data = UserResponseSchema.model_validate(user).to_dict()

    return success_response(data=user_data)
