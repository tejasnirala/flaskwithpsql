"""
RBAC Schemas
============
Pydantic schemas for RBAC operations.

These schemas handle:
1. Request validation (input)
2. Response formatting (output)
3. API documentation (OpenAPI)

Naming Convention:
------------------
- *CreateSchema: For creating new resources
- *UpdateSchema: For updating resources
- *ResponseSchema: For API responses
- *Query: For query parameters
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# =============================================================================
# PERMISSION SCHEMAS
# =============================================================================


class PermissionResponseSchema(BaseModel):
    """Schema for permission in API responses."""

    id: int = Field(..., description="Permission ID")
    name: str = Field(..., description="Permission name (e.g., 'users:delete')")
    resource: str = Field(..., description="Resource part (e.g., 'users')")
    action: str = Field(..., description="Action part (e.g., 'delete')")
    description: Optional[str] = Field(None, description="Permission description")

    model_config = ConfigDict(from_attributes=True)  # Enable ORM mode for SQLAlchemy models


class PermissionListQuery(BaseModel):
    """Query parameters for listing permissions."""

    resource: Optional[str] = Field(None, description="Filter by resource")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=50, ge=1, le=100, description="Items per page")


# =============================================================================
# ROLE SCHEMAS
# =============================================================================


class RoleCreateSchema(BaseModel):
    """Schema for creating a new role."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Unique role identifier (lowercase)",
        examples=["editor", "viewer", "analyst"],
    )
    display_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Human-friendly display name",
        examples=["Content Editor", "Report Viewer"],
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Role description",
    )
    permissions: List[str] = Field(
        default=[],
        description="List of permission names to assign",
        examples=[["users:read", "users:update"]],
    )
    parent_role: Optional[str] = Field(
        None,
        description="Parent role name for inheritance",
        examples=["user"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure role name is lowercase and valid format."""
        v = v.lower().strip()
        if not v.replace("_", "").isalnum():
            raise ValueError("Role name must contain only letters, numbers, and underscores")
        return v


class RoleUpdateSchema(BaseModel):
    """Schema for updating a role."""

    display_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Human-friendly display name",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Role description",
    )
    permissions: Optional[List[str]] = Field(
        None,
        description="List of permission names (replaces existing)",
    )
    parent_role: Optional[str] = Field(
        None,
        description="Parent role name for inheritance",
    )


class RoleResponseSchema(BaseModel):
    """Schema for role in API responses."""

    id: int = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Role description")
    is_system_role: bool = Field(..., description="Whether this is a protected system role")
    parent_role_id: Optional[int] = Field(None, description="Parent role ID")
    parent_role_name: Optional[str] = Field(None, description="Parent role name")
    permissions: Optional[List[str]] = Field(None, description="List of permission names")

    model_config = ConfigDict(from_attributes=True)


class RoleListQuery(BaseModel):
    """Query parameters for listing roles."""

    include_permissions: bool = Field(
        default=False,
        description="Include permission list for each role",
    )
    include_system: bool = Field(
        default=True,
        description="Include system roles in results",
    )
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")


# =============================================================================
# USER ROLE ASSIGNMENT SCHEMAS
# =============================================================================


class RoleAssignSchema(BaseModel):
    """Schema for assigning a role to a user."""

    role_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name of the role to assign",
        examples=["moderator", "admin"],
    )


class RoleRevokeSchema(BaseModel):
    """Schema for revoking a role from a user."""

    role_name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Name of the role to revoke",
    )


# =============================================================================
# DIRECT PERMISSION SCHEMAS
# =============================================================================


class DirectPermissionGrantSchema(BaseModel):
    """Schema for granting a direct permission to a user."""

    permission: str = Field(
        ...,
        description="Permission to grant (e.g., 'users:delete')",
        examples=["users:delete", "reports:export"],
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for granting (for audit trail)",
        examples=["Temporary access for project X cleanup"],
    )

    @field_validator("permission")
    @classmethod
    def validate_permission(cls, v: str) -> str:
        """Ensure permission follows resource:action format."""
        if ":" not in v:
            raise ValueError("Permission must be in 'resource:action' format")
        return v.lower().strip()


class DirectPermissionRevokeSchema(BaseModel):
    """Schema for revoking a direct permission from a user."""

    permission: str = Field(
        ...,
        description="Permission to revoke",
    )


# =============================================================================
# USER PERMISSIONS RESPONSE
# =============================================================================


class UserPermissionsResponseSchema(BaseModel):
    """Schema for user's complete permission information."""

    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    roles: List[str] = Field(..., description="List of assigned role names")
    role_permissions: List[str] = Field(
        ...,
        description="Permissions from roles (including inherited)",
    )
    direct_permissions: List[str] = Field(
        ...,
        description="Permissions assigned directly to user",
    )
    effective_permissions: List[str] = Field(
        ...,
        description="All effective permissions (role + direct)",
    )


# =============================================================================
# BULK OPERATIONS
# =============================================================================


class BulkRoleAssignSchema(BaseModel):
    """Schema for assigning roles to multiple users."""

    user_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of user IDs to assign the role to",
    )
    role_name: str = Field(
        ...,
        description="Role name to assign",
    )


class BulkPermissionAssignSchema(BaseModel):
    """Schema for assigning permissions to a role."""

    permissions: List[str] = Field(
        ...,
        min_length=1,
        description="List of permissions to assign",
    )


# =============================================================================
# PATH PARAMETERS
# =============================================================================


class RolePath(BaseModel):
    """Path parameters for role-specific endpoints."""

    role_name: str = Field(..., description="Role name")


class UserRolePath(BaseModel):
    """Path parameters for user role endpoints."""

    user_id: int = Field(..., ge=1, description="User ID")
