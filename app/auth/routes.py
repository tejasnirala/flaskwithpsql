"""
Authentication Routes - Login, Logout, Token Refresh.

These routes handle JWT-based authentication:
- POST /auth/login     - Get tokens with email/password
- POST /auth/logout    - Revoke current token
- POST /auth/refresh   - Get new access token using refresh token
- GET  /auth/me        - Get current user info
"""

import logging
from typing import Any, Dict, Optional

from flask_jwt_extended import get_jwt, jwt_required
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, EmailStr, Field

from app.auth import create_tokens, get_current_user, revoke_token
from app.schemas import UserResponseSchema
from app.services import InvalidCredentialsError, UserNotFoundError, UserService
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

tag = Tag(name="Authentication", description="JWT authentication endpoints")

auth_bp = APIBlueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
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


# =============================================================================
# Routes
# =============================================================================


@auth_bp.post(
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


@auth_bp.post(
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


@auth_bp.post(
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


@auth_bp.get(
    "/me",
    summary="Get Current User",
    description="Get the currently authenticated user's information.",
    responses={
        200: UserInfoResponse,
        401: StandardErrorResponse,
    },
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
