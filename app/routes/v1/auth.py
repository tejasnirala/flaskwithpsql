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

Architecture Note:
    These routes follow the thin-controller pattern:
    - Routes handle HTTP concerns (request/response, status codes)
    - AuthService handles business logic (authentication, token management)
    - This separation makes the code testable and reusable
"""

import logging
from typing import Any, Dict, Optional

from flask_jwt_extended import get_jwt, jwt_required
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, EmailStr, Field

from app.auth import get_current_user
from app.schemas import UserCreateSchema, UserResponseSchema
from app.services import (
    AuthService,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotAuthenticatedError,
)
from app.utils.rate_limiter import api_limit, auth_limit
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
# Version prefix (/api/v1) is added during registration in app/routes/v1/__init__.py
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

    Delegates to AuthService.register for business logic.
    """
    try:
        user_data = AuthService.register(
            username=body.username,
            email=body.email,
            password=body.password,
            first_name=body.first_name,
            middle_name=body.middle_name,
            last_name=body.last_name,
            bio=body.bio,
        )
        return success_response(
            data=user_data,
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

**Rate Limit:** 5 requests per minute (to prevent brute-force attacks)
    """,
    responses={
        200: TokenResponse,
        401: StandardErrorResponse,
        429: StandardErrorResponse,
    },
)
@auth_limit
def login(body: LoginRequest):
    """
    Login and get JWT tokens.

    Delegates to AuthService.login for business logic.
    Rate limited to prevent brute-force attacks.
    """
    try:
        result = AuthService.login(body.email, body.password)
        return success_response(
            data=result,
            message="Login successful",
        )
    except InvalidCredentialsError:
        # Security: Same error for user not found AND wrong password
        # prevents email enumeration
        return error_response(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="Invalid email or password",
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

    Delegates to AuthService.logout for business logic.
    """
    jti = get_jwt()["jti"]
    AuthService.logout(jti)

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

    Delegates to AuthService.refresh_tokens for business logic.
    """
    try:
        user = get_current_user()
        tokens = AuthService.refresh_tokens(user)
        return success_response(
            data=tokens,
            message="Token refreshed",
        )
    except UserNotAuthenticatedError:
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="User not found",
            status_code=401,
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

    Delegates to AuthService.get_current_user_info for business logic.
    """
    try:
        user = get_current_user()
        user_data = AuthService.get_current_user_info(user)
        return success_response(data=user_data)
    except UserNotAuthenticatedError:
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="User not found",
            status_code=401,
        )
