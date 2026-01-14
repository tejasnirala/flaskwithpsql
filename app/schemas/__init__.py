"""
Schemas Package - Pydantic validation schemas for the application.

This package contains all Pydantic models (schemas) used for input validation
across the application. Schemas are organized by domain/model.

Directory Structure:
    schemas/
    ├── __init__.py          # This file - exports all schemas
    ├── base.py              # Base schema with common configuration
    ├── user.py              # User-related validation schemas
    ├── validators.py        # Shared validators (DRY)
    ├── utils.py             # Validation utility functions
    └── rbac.py              # RBAC-related schemas (roles, permissions)

Usage:
    from app.schemas.user import UserCreateSchema, UserLoginSchema
    from app.schemas.utils import validate_request, validate_with_schema

    # Option 1: Manual validation
    result = validate_request(UserCreateSchema)
    if isinstance(result, tuple):
        return result  # Error response
    validated_data = result

    # Option 2: Decorator (recommended)
    @validate_with_schema(UserCreateSchema)
    def create_user(validated_data):
        ...
"""

# Import all schemas for easy access
from app.schemas.base import BaseSchema
from app.schemas.rbac import (
    DirectPermissionGrantSchema,
    DirectPermissionRevokeSchema,
    PermissionListQuery,
    PermissionResponseSchema,
    RoleAssignSchema,
    RoleCreateSchema,
    RoleListQuery,
    RolePath,
    RoleResponseSchema,
    RoleRevokeSchema,
    RoleUpdateSchema,
    UserPermissionsResponseSchema,
    UserRolePath,
)
from app.schemas.user import UserCreateSchema, UserLoginSchema, UserResponseSchema, UserUpdateSchema
from app.schemas.utils import format_validation_errors, validate_request, validate_with_schema
from app.schemas.validators import normalize_name, normalize_username, validate_password_strength

__all__ = [
    # Base
    "BaseSchema",
    # User schemas
    "UserCreateSchema",
    "UserLoginSchema",
    "UserUpdateSchema",
    "UserResponseSchema",
    # RBAC schemas
    "RoleCreateSchema",
    "RoleUpdateSchema",
    "RoleResponseSchema",
    "RoleListQuery",
    "RolePath",
    "RoleAssignSchema",
    "RoleRevokeSchema",
    "PermissionResponseSchema",
    "PermissionListQuery",
    "DirectPermissionGrantSchema",
    "DirectPermissionRevokeSchema",
    "UserPermissionsResponseSchema",
    "UserRolePath",
    # Utilities
    "validate_request",
    "validate_with_schema",
    "format_validation_errors",
    # Validators
    "normalize_name",
    "normalize_username",
    "validate_password_strength",
]
