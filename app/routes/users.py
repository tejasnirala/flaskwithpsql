"""User routes - CRUD operations for users.

This module uses flask-openapi3's APIBlueprint for automatic OpenAPI generation.
Routes are thin - they handle HTTP concerns and delegate to the UserService.

Key Changes from Regular Flask Blueprint:
1. Blueprint → APIBlueprint
2. @route("/path", methods=["POST"]) → @bp.post("/path")
3. Request body is automatically validated using Pydantic schemas
4. Response schemas define the API contract

Architecture:
    HTTP Request → Route (HTTP handling) → Service (Business Logic) → Model (Data)
"""

import logging
from typing import Any, Dict, List, Optional

from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, Field

from app.schemas import UserCreateSchema, UserLoginSchema, UserResponseSchema, UserUpdateSchema
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

# Module-level logger - follows Python logging best practices
logger = logging.getLogger(__name__)


# =============================================================================
# API Blueprint Setup
# =============================================================================

# Tag for grouping user endpoints in Swagger UI
tag = Tag(
    name="Users",
    description="User management - registration, login, profile CRUD operations",
)

# APIBlueprint replaces Blueprint, enabling automatic OpenAPI documentation
users_bp = APIBlueprint(
    "users",
    __name__,
    url_prefix="/api/users",  # URL prefix is set here, not in register_api()
    abp_tags=[tag],  # All routes in this blueprint get this tag
)


# =============================================================================
# Response Schemas for OpenAPI Documentation
# =============================================================================


class UserDataResponse(StandardSuccessResponse):
    """Single user data response - extends standard success response."""

    data: Optional[Dict[str, Any]] = Field(
        ..., description="User data object containing user information"
    )


class UsersListResponse(StandardSuccessResponse):
    """List of users response - extends standard success response."""

    data: Optional[List[Dict[str, Any]]] = Field(..., description="List of user objects")


class MessageResponse(StandardSuccessResponse):
    """Simple message response for operations like delete."""

    data: Optional[Dict[str, str]] = Field(..., description="Object containing a success message")


# =============================================================================
# Path Parameters Schema
# =============================================================================


class UserPath(BaseModel):
    """Path parameters for user-specific endpoints."""

    user_id: int = Field(..., description="User ID", ge=1)


# =============================================================================
# Query Parameters Schema
# =============================================================================


class UserListQuery(BaseModel):
    """Query parameters for listing users with pagination."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")
    include_deleted: bool = Field(default=False, description="Include soft-deleted users")


# =============================================================================
# CREATE - Register new user
# =============================================================================


@users_bp.post(
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


# =============================================================================
# READ - Login (authenticate user)
# =============================================================================


@users_bp.post(
    "/login",
    summary="User Login",
    description="""
Authenticates a user with email and password.

**Note:** This is a simple login endpoint. In a production system,
you would return a JWT token or session cookie here.
    """,
    responses={
        200: UserDataResponse,
        401: StandardErrorResponse,
        404: StandardErrorResponse,
        422: StandardErrorResponse,
    },
)
def login_user(body: UserLoginSchema):
    """
    Login a user.

    Delegates to UserService for authentication.
    """
    try:
        user = UserService.authenticate(body.email, body.password)
        response_data = UserResponseSchema.model_validate(user)
        return success_response(
            data=response_data.to_dict(),
            message="User logged in successfully",
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


# =============================================================================
# READ - Get all users (with pagination)
# =============================================================================


@users_bp.get(
    "/",
    summary="Get All Users",
    description="Retrieves a paginated list of all users in the system.",
    responses={
        200: UsersListResponse,
    },
)
def get_users(query: UserListQuery):
    """
    Get all users with pagination.

    Supports filtering soft-deleted users and pagination.
    """
    users, total = UserService.get_all(
        include_deleted=query.include_deleted,
        page=query.page,
        per_page=query.per_page,
    )

    # Convert each user to response schema
    users_data = [UserResponseSchema.model_validate(user).to_dict() for user in users]

    # Calculate pagination metadata
    total_pages = (total + query.per_page - 1) // query.per_page  # Ceiling division

    return success_response(
        data=users_data,
        meta={
            "count": len(users_data),
            "total": total,
            "page": query.page,
            "per_page": query.per_page,
            "total_pages": total_pages,
        },
    )


# =============================================================================
# READ - Get single user
# =============================================================================


@users_bp.get(
    "/<int:user_id>",
    summary="Get User by ID",
    description="Retrieves a specific user by their ID.",
    responses={
        200: UserDataResponse,
        404: StandardErrorResponse,
    },
)
def get_user(path: UserPath):
    """
    Get a specific user by ID.

    Uses service layer which excludes soft-deleted users by default.
    """
    try:
        user = UserService.get_by_id_or_404(path.user_id)
        response_data = UserResponseSchema.model_validate(user)
        return success_response(data=response_data.to_dict())
    except UserNotFoundError:
        return error_response(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )


# =============================================================================
# UPDATE - Update user
# =============================================================================


@users_bp.put(
    "/<int:user_id>",
    summary="Update User",
    description="""
Updates an existing user's profile.

**Partial Update:** Only fields provided in the request body will be updated.
At least one field must be provided.
    """,
    responses={
        200: UserDataResponse,
        404: StandardErrorResponse,
        422: StandardErrorResponse,
    },
)
def update_user(path: UserPath, body: UserUpdateSchema):
    """
    Update an existing user.

    Delegates to UserService for business logic.
    """
    try:
        user = UserService.update_user(path.user_id, body)
        response_data = UserResponseSchema.model_validate(user)
        return success_response(
            data=response_data.to_dict(),
            message="User updated successfully",
        )
    except UserNotFoundError:
        return error_response(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )


# =============================================================================
# DELETE - Soft delete user
# =============================================================================


@users_bp.delete(
    "/<int:user_id>",
    summary="Delete User",
    description="""
Soft-deletes a user by setting is_deleted=True.

The user record remains in the database but is marked as deleted.
This allows for potential recovery and maintains referential integrity.
    """,
    responses={
        200: MessageResponse,
        404: StandardErrorResponse,
    },
)
def delete_user(path: UserPath):
    """
    Delete a user (soft delete).

    Uses service layer for proper soft deletion.
    """
    try:
        UserService.soft_delete(path.user_id)
        return success_response(message=f"User {path.user_id} deleted successfully")
    except UserNotFoundError:
        return error_response(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )
