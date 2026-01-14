"""
RBAC Decorators
===============
Route protection decorators for Role-Based Access Control.

These decorators wrap Flask routes to enforce access control:
1. @permission_required() - Require specific permissions
2. @role_required() - Require specific roles
3. @admin_required() - Shortcut for admin role

Usage:
------
    from app.rbac import permission_required, role_required

    @app.route("/users/<id>", methods=["DELETE"])
    @permission_required("users:delete")
    def delete_user(id):
        # User must have "users:delete" permission
        pass

    @app.route("/admin/dashboard")
    @role_required("admin", "super_admin")
    def admin_dashboard():
        # User must have "admin" OR "super_admin" role
        pass

    @app.route("/settings")
    @permission_required("settings:read", "settings:update", require_all=True)
    def settings():
        # User must have BOTH permissions
        pass

Design Decisions:
-----------------
1. Decorators handle JWT verification internally
   - No need to stack @jwt_required() with @permission_required()
   - Cleaner code at route level

2. Return error_response for consistency
   - Uses existing standardized response format
   - 401 for authentication failures
   - 403 for authorization failures

3. Support for require_all parameter
   - Default: require ANY of the specified permissions/roles
   - Set require_all=True to require ALL
"""

import logging
from functools import wraps

from flask_jwt_extended import verify_jwt_in_request

from app.auth import get_current_user
from app.rbac.services import RBACService
from app.utils.responses import ErrorCode, error_response

logger = logging.getLogger(__name__)


def permission_required(
    *permissions: str,
    require_all: bool = False,
    message: str = None,
):
    """
    Decorator to require specific permissions for a route.

    Automatically handles:
    1. JWT token verification
    2. User authentication
    3. Permission checking

    Args:
        *permissions: One or more permission strings (e.g., "users:delete")
        require_all: If True, ALL permissions required. If False (default), ANY works.
        message: Custom error message (optional)

    Returns:
        Decorated function

    Usage Examples:
        # Single permission
        @permission_required("users:delete")
        def delete_user():
            pass

        # Multiple permissions (ANY)
        @permission_required("users:update", "admin:update")
        def update_user():
            # User needs EITHER permission
            pass

        # Multiple permissions (ALL)
        @permission_required("users:read", "audit:read", require_all=True)
        def view_user_audit():
            # User needs BOTH permissions
            pass

        # Custom error message
        @permission_required("users:delete", message="Only admins can delete users")
        def delete_user():
            pass

    Flow:
        Request → Verify JWT → Get User → Check Permission(s) → Execute Route
                    ↓              ↓               ↓
                 401 Error     401 Error       403 Error (if fails)
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Step 1: Verify JWT token
            try:
                verify_jwt_in_request()
            except Exception as e:
                logger.warning(f"JWT verification failed: {e}")
                return error_response(
                    code=ErrorCode.UNAUTHORIZED,
                    message="Authentication required",
                    status_code=401,
                )

            # Step 2: Get current user
            user = get_current_user()
            if user is None:
                return error_response(
                    code=ErrorCode.UNAUTHORIZED,
                    message="User not found or inactive",
                    status_code=401,
                )

            # Step 3: Check if user is active
            if not user.is_active:
                return error_response(
                    code=ErrorCode.FORBIDDEN,
                    message="User account is deactivated",
                    status_code=403,
                )

            # Step 4: Check permissions
            if require_all:
                has_access = RBACService.user_has_all_permissions(user, list(permissions))
            else:
                has_access = RBACService.user_has_any_permission(user, list(permissions))

            if not has_access:
                logger.info(
                    f"Permission denied for user_id={user.id}: "
                    f"required={list(permissions)}, require_all={require_all}"
                )
                return error_response(
                    code=ErrorCode.FORBIDDEN,
                    message=message or "Insufficient permissions",
                    details={
                        "required_permissions": list(permissions),
                        "require_all": require_all,
                    },
                    status_code=403,
                )

            # Step 5: Execute the route handler
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def role_required(
    *roles: str,
    require_all: bool = False,
    message: str = None,
):
    """
    Decorator to require specific roles for a route.

    By default, user needs ANY of the specified roles.
    Set require_all=True if ALL roles are required.

    Args:
        *roles: One or more role names (e.g., "admin", "moderator")
        require_all: If True, ALL roles required. If False (default), ANY works.
        message: Custom error message (optional)

    Returns:
        Decorated function

    Usage Examples:
        # Single role
        @role_required("admin")
        def admin_panel():
            pass

        # Multiple roles (ANY)
        @role_required("admin", "moderator", "support")
        def moderation_panel():
            # User needs ANY of these roles
            pass

        # Multiple roles (ALL)
        @role_required("verified", "premium", require_all=True)
        def premium_feature():
            # User needs BOTH roles
            pass

    Flow:
        Request → Verify JWT → Get User → Check Role(s) → Execute Route
                    ↓              ↓            ↓
                 401 Error     401 Error    403 Error (if fails)
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Step 1: Verify JWT token
            try:
                verify_jwt_in_request()
            except Exception as e:
                logger.warning(f"JWT verification failed: {e}")
                return error_response(
                    code=ErrorCode.UNAUTHORIZED,
                    message="Authentication required",
                    status_code=401,
                )

            # Step 2: Get current user
            user = get_current_user()
            if user is None:
                return error_response(
                    code=ErrorCode.UNAUTHORIZED,
                    message="User not found or inactive",
                    status_code=401,
                )

            # Step 3: Check if user is active
            if not user.is_active:
                return error_response(
                    code=ErrorCode.FORBIDDEN,
                    message="User account is deactivated",
                    status_code=403,
                )

            # Step 4: Check roles
            if require_all:
                has_access = user.has_all_roles(*roles)
            else:
                has_access = user.has_any_role(*roles)

            if not has_access:
                logger.info(
                    f"Role denied for user_id={user.id}: "
                    f"required={list(roles)}, require_all={require_all}"
                )
                return error_response(
                    code=ErrorCode.FORBIDDEN,
                    message=message or "Insufficient role privileges",
                    details={
                        "required_roles": list(roles),
                        "require_all": require_all,
                    },
                    status_code=403,
                )

            # Step 5: Execute the route handler
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(message: str = None):
    """
    Shortcut decorator for admin-only routes.

    Equivalent to: @role_required("admin", "super_admin")

    Args:
        message: Custom error message (optional)

    Usage:
        @admin_required()
        def admin_dashboard():
            pass
    """
    return role_required("admin", "super_admin", message=message or "Admin access required")


def super_admin_required(message: str = None):
    """
    Shortcut decorator for super admin-only routes.

    Equivalent to: @role_required("super_admin")

    Args:
        message: Custom error message (optional)

    Usage:
        @super_admin_required()
        def system_settings():
            pass
    """
    return role_required("super_admin", message=message or "Super admin access required")


# =============================================================================
# PROGRAMMATIC PERMISSION CHECK (for use in route handlers)
# =============================================================================
def check_permission(permission: str) -> bool:
    """
    Check if the current user has a specific permission.

    Use this inside route handlers when you need conditional logic
    based on permissions, rather than all-or-nothing access.

    Args:
        permission: Permission string to check

    Returns:
        bool: True if current user has the permission

    Usage:
        @app.route("/users/<id>")
        @jwt_required()
        def get_user(id):
            user_data = get_user_data(id)

            # Only show sensitive info if user has permission
            if check_permission("users:view_sensitive"):
                user_data["ssn"] = get_sensitive_data(id)

            return user_data
    """
    user = get_current_user()
    if user is None:
        return False
    return RBACService.user_has_permission(user, permission)


def check_role(role: str) -> bool:
    """
    Check if the current user has a specific role.

    Args:
        role: Role name to check

    Returns:
        bool: True if current user has the role
    """
    user = get_current_user()
    if user is None:
        return False
    return RBACService.user_has_role(user, role)
