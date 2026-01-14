"""
Permission Management Routes (Admin)
=====================================
Administrative routes for managing permissions and user direct permissions.

All routes require admin privileges.

Endpoints:
    GET    /admin/permissions                     - List all permissions
    GET    /admin/permissions/<name>              - Get permission details

    GET    /admin/users/<id>/permissions          - Get user's permissions
    POST   /admin/users/<id>/permissions          - Grant direct permission
    DELETE /admin/users/<id>/permissions/<perm>   - Revoke direct permission
"""

import logging
from typing import Any, Dict, List, Optional

from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.models import Permission, User
from app.rbac import RBACService, permission_required
from app.rbac.exceptions import DirectPermissionError, PermissionNotFoundError
from app.schemas.rbac import DirectPermissionGrantSchema, PermissionListQuery
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
    name="Permissions Management",
    description="View permissions and manage direct user permissions",
)

permissions_bp = APIBlueprint(
    "permissions_admin",
    __name__,
    url_prefix="/permissions",
    abp_tags=[tag],
)


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class PermissionDataResponse(StandardSuccessResponse):
    """Single permission response."""

    data: Optional[Dict[str, Any]] = Field(..., description="Permission data")


class PermissionsListResponse(StandardSuccessResponse):
    """List of permissions response."""

    data: Optional[List[Dict[str, Any]]] = Field(..., description="List of permissions")


class UserPermissionsResponse(StandardSuccessResponse):
    """User permissions response."""

    data: Optional[Dict[str, Any]] = Field(..., description="User permissions data")


class MessageResponse(StandardSuccessResponse):
    """Simple message response."""

    data: Optional[Dict[str, str]] = Field(..., description="Message")


# =============================================================================
# PERMISSION LIST ROUTES
# =============================================================================


@permissions_bp.get(
    "/",
    summary="List All Permissions",
    description="Get a list of all permissions in the system.",
    responses={200: PermissionsListResponse},
    security=[{"jwt": []}],
)
@permission_required("permissions:list", "permissions:read")
def list_permissions(query: PermissionListQuery):
    """List all permissions."""
    # Build query
    perm_query = Permission.query.filter_by(is_deleted=False)

    if query.resource:
        perm_query = perm_query.filter_by(resource=query.resource)

    # Pagination
    total = perm_query.count()
    permissions = (
        perm_query.order_by(Permission.resource, Permission.action)
        .offset((query.page - 1) * query.per_page)
        .limit(query.per_page)
        .all()
    )

    # Format response
    permissions_data = [perm.to_dict() for perm in permissions]

    return success_response(
        data=permissions_data,
        meta={
            "total": total,
            "page": query.page,
            "per_page": query.per_page,
            "total_pages": (total + query.per_page - 1) // query.per_page,
        },
    )


class PermissionPathParam(BaseModel):
    """Path parameter for permission name."""

    permission_name: str = Field(..., description="Permission name (e.g., 'users:delete')")


@permissions_bp.get(
    "/<permission_name>",
    summary="Get Permission Details",
    description="Get detailed information about a specific permission.",
    responses={200: PermissionDataResponse, 404: StandardErrorResponse},
    security=[{"jwt": []}],
)
@permission_required("permissions:read")
def get_permission(path: PermissionPathParam):
    """Get a specific permission by name."""
    perm = Permission.query.filter_by(name=path.permission_name, is_deleted=False).first()

    if not perm:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"Permission '{path.permission_name}' not found",
            status_code=404,
        )

    return success_response(data=perm.to_dict())


# =============================================================================
# USER DIRECT PERMISSION ROUTES
# =============================================================================


class UserPermissionPathParam(BaseModel):
    """Path parameter for user permission operations."""

    user_id: int = Field(..., ge=1, description="User ID")


class UserPermissionRevokePathParam(BaseModel):
    """Path parameter for revoking permission from user."""

    user_id: int = Field(..., ge=1, description="User ID")
    permission_name: str = Field(..., description="Permission name to revoke")


@permissions_bp.get(
    "/users/<int:user_id>",
    summary="Get User Permissions",
    description="Get all permissions for a user (role-based and direct).",
    responses={200: UserPermissionsResponse, 404: StandardErrorResponse},
    security=[{"jwt": []}],
)
@permission_required("permissions:read", "users:read")
def get_user_permissions(path: UserPermissionPathParam):
    """Get all permissions for a user."""
    user = User.query.filter_by(id=path.user_id, is_deleted=False).first()

    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )

    # Get permissions breakdown
    role_permissions = set()
    for role in user.roles:
        role_permissions.update(role.get_all_permissions())

    direct_permissions = {perm.name for perm in user.direct_permissions}
    all_permissions = role_permissions.union(direct_permissions)

    return success_response(
        data={
            "user_id": user.id,
            "username": user.username,
            "roles": [role.name for role in user.roles],
            "role_permissions": sorted(role_permissions),
            "direct_permissions": sorted(direct_permissions),
            "effective_permissions": sorted(all_permissions),
        }
    )


@permissions_bp.post(
    "/users/<int:user_id>",
    summary="Grant Direct Permission",
    description="""
Grant a direct permission to a user.

Direct permissions are granted directly to a user (not through roles).
Use sparingly - most permissions should come from roles.
    """,
    responses={
        200: MessageResponse,
        400: StandardErrorResponse,
        404: StandardErrorResponse,
    },
    security=[{"jwt": []}],
)
@permission_required("permissions:assign")
def grant_direct_permission(path: UserPermissionPathParam, body: DirectPermissionGrantSchema):
    """Grant a direct permission to a user."""
    user = User.query.filter_by(id=path.user_id, is_deleted=False).first()

    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )

    try:
        current_user = get_current_user()
        RBACService.grant_direct_permission(
            user=user,
            permission_name=body.permission,
            granted_by=current_user,
            reason=body.reason,
        )

        return success_response(
            message=f"Permission '{body.permission}' granted to user '{user.username}'"
        )

    except PermissionNotFoundError:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"Permission '{body.permission}' not found",
            status_code=404,
        )
    except DirectPermissionError as e:
        return error_response(
            code=ErrorCode.BAD_REQUEST,
            message=str(e),
            status_code=400,
        )


@permissions_bp.delete(
    "/users/<int:user_id>/<permission_name>",
    summary="Revoke Direct Permission",
    description="Revoke a direct permission from a user.",
    responses={
        200: MessageResponse,
        400: StandardErrorResponse,
        404: StandardErrorResponse,
    },
    security=[{"jwt": []}],
)
@permission_required("permissions:revoke")
def revoke_direct_permission(path: UserPermissionRevokePathParam):
    """Revoke a direct permission from a user."""
    user = User.query.filter_by(id=path.user_id, is_deleted=False).first()

    if not user:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"User with id={path.user_id} not found",
            status_code=404,
        )

    try:
        current_user = get_current_user()
        RBACService.revoke_direct_permission(
            user=user,
            permission_name=path.permission_name,
            revoked_by=current_user,
        )

        return success_response(
            message=f"Permission '{path.permission_name}' revoked from user '{user.username}'"
        )

    except PermissionNotFoundError:
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message=f"Permission '{path.permission_name}' not found",
            status_code=404,
        )
    except DirectPermissionError as e:
        return error_response(
            code=ErrorCode.BAD_REQUEST,
            message=str(e),
            status_code=400,
        )
