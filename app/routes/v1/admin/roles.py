"""
Role Management Routes (Admin)
==============================
Administrative routes for managing roles and user role assignments.

All routes require admin privileges (roles:* permissions).

Endpoints:
    GET    /admin/roles                    - List all roles
    POST   /admin/roles                    - Create a new role
    GET    /admin/roles/<name>             - Get role details
    PUT    /admin/roles/<name>             - Update a role
    DELETE /admin/roles/<name>             - Delete a role

    GET    /admin/users/<id>/roles         - Get user's roles
    POST   /admin/users/<id>/roles         - Assign role to user
    DELETE /admin/users/<id>/roles/<role>  - Revoke role from user
"""

import logging
from typing import Any, Dict, List, Optional

from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, Field

from app import db
from app.auth import get_current_user
from app.models import Role, User
from app.rbac import RBACService, permission_required
from app.rbac.exceptions import RoleAssignmentError, RoleNotFoundError, SystemRoleError
from app.schemas.rbac import RoleAssignSchema, RoleCreateSchema, RoleListQuery, RoleUpdateSchema
from app.utils.responses import (
    ErrorCode,
    StandardErrorResponse,
    StandardSuccessResponse,
    error_response,
    success_response,
)

logger = logging.getLogger(__name__)

# Blueprint setup
tag = Tag(
    name="Roles Management",
    description="Manage roles and role assignments",
)

roles_bp = APIBlueprint(
    "roles_admin",
    __name__,
    url_prefix="/roles",
    abp_tags=[tag],
)


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class RoleDataResponse(StandardSuccessResponse):
    """Single role response."""

    data: Optional[Dict[str, Any]] = Field(..., description="Role data")


class RolesListResponse(StandardSuccessResponse):
    """List of roles response."""

    data: Optional[List[Dict[str, Any]]] = Field(..., description="List of roles")


class MessageResponse(StandardSuccessResponse):
    """Simple message response."""

    data: Optional[Dict[str, str]] = Field(..., description="Message")


# =============================================================================
# ROLE CRUD ROUTES
# =============================================================================


@roles_bp.get(
    "/",
    summary="List All Roles",
    description="Get a list of all roles in the system.",
    responses={200: RolesListResponse, 403: StandardErrorResponse},
    security=[{"jwt": []}],
)
@permission_required("roles:list", "roles:read")
def list_roles(query: RoleListQuery):
    """List all roles with optional permission details."""
    # Build query
    role_query = Role.query.filter_by(is_deleted=False)

    if not query.include_system:
        role_query = role_query.filter_by(is_system_role=False)

    # Pagination
    total = role_query.count()
    roles = (
        role_query.order_by(Role.name)
        .offset((query.page - 1) * query.per_page)
        .limit(query.per_page)
        .all()
    )

    # Format response
    roles_data = [role.to_dict(include_permissions=query.include_permissions) for role in roles]

    return success_response(
        data=roles_data,
        meta={
            "total": total,
            "page": query.page,
            "per_page": query.per_page,
            "total_pages": (total + query.per_page - 1) // query.per_page,
        },
    )


@roles_bp.post(
    "/",
    summary="Create Role",
    description="Create a new role with specified permissions.",
    responses={
        201: RoleDataResponse,
        400: StandardErrorResponse,
        403: StandardErrorResponse,
    },
    security=[{"jwt": []}],
)
@permission_required("roles:create")
def create_role(body: RoleCreateSchema):
    """Create a new role."""
    try:
        role = RBACService.create_role(
            name=body.name,
            display_name=body.display_name,
            description=body.description,
            permission_names=body.permissions,
            parent_role_name=body.parent_role,
            is_system_role=False,  # User-created roles are not system roles
        )

        logger.info(f"Role '{body.name}' created by user_id={get_current_user().id}")

        return success_response(
            data=role.to_dict(include_permissions=True),
            message=f"Role '{body.name}' created successfully",
            status_code=201,
        )

    except RoleAssignmentError as e:
        return error_response(
            code=ErrorCode.CONFLICT,
            message=str(e),
            status_code=409,
        )
    except RoleNotFoundError as e:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=str(e),
            status_code=404,
        )


class RolePathParam(BaseModel):
    """Path parameter for role name."""

    role_name: str = Field(..., description="Role name")


@roles_bp.get(
    "/<role_name>",
    summary="Get Role Details",
    description="Get detailed information about a specific role.",
    responses={200: RoleDataResponse, 404: StandardErrorResponse},
    security=[{"jwt": []}],
)
@permission_required("roles:read")
def get_role(path: RolePathParam):
    """Get a specific role by name."""
    try:
        role = RBACService.get_role_or_404(role_name=path.role_name)

        # Get all permissions including inherited
        all_permissions = list(role.get_all_permissions())
        direct_permissions = [p.name for p in role.permissions]

        role_data = role.to_dict(include_permissions=True)
        role_data["all_permissions"] = all_permissions
        role_data["inherited_permissions"] = [
            p for p in all_permissions if p not in direct_permissions
        ]

        return success_response(data=role_data)

    except RoleNotFoundError:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"Role '{path.role_name}' not found",
            status_code=404,
        )


@roles_bp.put(
    "/<role_name>",
    summary="Update Role",
    description="Update a role's display name, description, or permissions.",
    responses={
        200: RoleDataResponse,
        403: StandardErrorResponse,
        404: StandardErrorResponse,
    },
    security=[{"jwt": []}],
)
@permission_required("roles:update")
def update_role(path: RolePathParam, body: RoleUpdateSchema):
    """Update a role."""
    try:
        role = RBACService.get_role_or_404(role_name=path.role_name)

        # Update fields
        if body.display_name is not None:
            role.display_name = body.display_name

        if body.description is not None:
            role.description = body.description

        # Update permissions if provided
        if body.permissions is not None:
            from app.models import Permission

            role.permissions.clear()
            for perm_name in body.permissions:
                perm = Permission.query.filter_by(name=perm_name, is_deleted=False).first()
                if perm:
                    role.permissions.append(perm)

        # Update parent role if provided
        if body.parent_role is not None:
            if body.parent_role == "":
                role.parent_role_id = None
            else:
                parent = RBACService.get_role_or_404(role_name=body.parent_role)
                role.parent_role_id = parent.id

        db.session.commit()

        logger.info(f"Role '{path.role_name}' updated by user_id={get_current_user().id}")

        return success_response(
            data=role.to_dict(include_permissions=True),
            message=f"Role '{path.role_name}' updated successfully",
        )

    except RoleNotFoundError as e:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=str(e),
            status_code=404,
        )


@roles_bp.delete(
    "/<role_name>",
    summary="Delete Role",
    description="Delete a role. System roles cannot be deleted.",
    responses={
        200: MessageResponse,
        403: StandardErrorResponse,
        404: StandardErrorResponse,
    },
    security=[{"jwt": []}],
)
@permission_required("roles:delete")
def delete_role(path: RolePathParam):
    """Delete a role (soft delete)."""
    try:
        current_user = get_current_user()
        RBACService.delete_role(path.role_name, deleted_by=current_user)

        return success_response(message=f"Role '{path.role_name}' deleted successfully")

    except RoleNotFoundError:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"Role '{path.role_name}' not found",
            status_code=404,
        )
    except SystemRoleError as e:
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message=str(e),
            status_code=403,
        )


# =============================================================================
# USER ROLE ASSIGNMENT ROUTES
# =============================================================================


class UserRolePathParam(BaseModel):
    """Path parameter for user role operations."""

    user_id: int = Field(..., ge=1, description="User ID")


class UserRoleRevokePathParam(BaseModel):
    """Path parameter for revoking role from user."""

    user_id: int = Field(..., ge=1, description="User ID")
    role_name: str = Field(..., description="Role name to revoke")


@roles_bp.get(
    "/users/<int:user_id>",
    summary="Get User Roles",
    description="Get all roles assigned to a specific user.",
    responses={200: RolesListResponse, 404: StandardErrorResponse},
    security=[{"jwt": []}],
)
@permission_required("roles:read", "users:read")
def get_user_roles(path: UserRolePathParam):
    """Get roles for a specific user."""
    user = User.query.filter_by(id=path.user_id, is_deleted=False).first()

    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )

    roles_data = [role.to_dict(include_permissions=True) for role in user.roles]

    return success_response(
        data={
            "user_id": user.id,
            "username": user.username,
            "roles": roles_data,
            "all_permissions": list(user.get_all_permissions()),
        }
    )


@roles_bp.post(
    "/users/<int:user_id>",
    summary="Assign Role to User",
    description="Assign a role to a user.",
    responses={
        200: MessageResponse,
        400: StandardErrorResponse,
        404: StandardErrorResponse,
    },
    security=[{"jwt": []}],
)
@permission_required("roles:assign")
def assign_role_to_user(path: UserRolePathParam, body: RoleAssignSchema):
    """Assign a role to a user."""
    user = User.query.filter_by(id=path.user_id, is_deleted=False).first()

    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )

    try:
        current_user = get_current_user()
        RBACService.assign_role_to_user(
            user=user,
            role_name=body.role_name,
            assigned_by=current_user,
        )

        return success_response(
            message=f"Role '{body.role_name}' assigned to user '{user.username}'"
        )

    except RoleNotFoundError:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"Role '{body.role_name}' not found",
            status_code=404,
        )
    except RoleAssignmentError as e:
        return error_response(
            code=ErrorCode.BAD_REQUEST,
            message=str(e),
            status_code=400,
        )


@roles_bp.delete(
    "/users/<int:user_id>/<role_name>",
    summary="Revoke Role from User",
    description="Revoke a role from a user.",
    responses={
        200: MessageResponse,
        400: StandardErrorResponse,
        404: StandardErrorResponse,
    },
    security=[{"jwt": []}],
)
@permission_required("roles:revoke")
def revoke_role_from_user(path: UserRoleRevokePathParam):
    """Revoke a role from a user."""
    user = User.query.filter_by(id=path.user_id, is_deleted=False).first()

    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )

    try:
        current_user = get_current_user()
        RBACService.revoke_role_from_user(
            user=user,
            role_name=path.role_name,
            revoked_by=current_user,
        )

        return success_response(
            message=f"Role '{path.role_name}' revoked from user '{user.username}'"
        )

    except RoleNotFoundError:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"Role '{path.role_name}' not found",
            status_code=404,
        )
    except RoleAssignmentError as e:
        return error_response(
            code=ErrorCode.BAD_REQUEST,
            message=str(e),
            status_code=400,
        )
