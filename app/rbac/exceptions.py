"""
RBAC Exceptions
===============
Custom exception classes for Role-Based Access Control.

Exception Hierarchy:
    RBACError (base)
    ├── PermissionDeniedError    - User lacks required permission
    ├── RoleNotFoundError        - Role doesn't exist
    ├── PermissionNotFoundError  - Permission doesn't exist
    ├── RoleAssignmentError      - Error assigning/revoking role
    └── SystemRoleError          - Attempted operation on system role

These exceptions are caught by global error handlers and converted
to appropriate HTTP responses (403, 404, etc.).
"""


class RBACError(Exception):
    """
    Base exception for all RBAC-related errors.

    All RBAC exceptions should inherit from this class.
    This allows catching all RBAC errors with a single except clause.

    Attributes:
        message: Human-readable error message
        code: Machine-readable error code
    """

    def __init__(self, message: str, code: str = "RBAC_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class PermissionDeniedError(RBACError):
    """
    Raised when a user lacks the required permission.

    This is converted to a 403 Forbidden HTTP response.

    Usage:
        if not user.has_permission("users:delete"):
            raise PermissionDeniedError(
                permission="users:delete",
                message="You don't have permission to delete users"
            )
    """

    def __init__(
        self,
        permission: str = None,
        message: str = None,
        required_permissions: list = None,
    ):
        self.permission = permission
        self.required_permissions = required_permissions or ([permission] if permission else [])

        if message is None:
            if permission:
                message = f"Permission denied: {permission}"
            else:
                message = "Permission denied"

        super().__init__(message, code="PERMISSION_DENIED")


class RoleNotFoundError(RBACError):
    """
    Raised when a requested role doesn't exist.

    This is converted to a 404 Not Found HTTP response.

    Usage:
        role = Role.query.filter_by(name="admin").first()
        if not role:
            raise RoleNotFoundError(role_name="admin")
    """

    def __init__(self, role_name: str = None, role_id: int = None, message: str = None):
        self.role_name = role_name
        self.role_id = role_id

        if message is None:
            if role_name:
                message = f"Role not found: {role_name}"
            elif role_id:
                message = f"Role not found: id={role_id}"
            else:
                message = "Role not found"

        super().__init__(message, code="ROLE_NOT_FOUND")


class PermissionNotFoundError(RBACError):
    """
    Raised when a requested permission doesn't exist.

    This is converted to a 404 Not Found HTTP response.

    Usage:
        perm = Permission.query.filter_by(name="users:delete").first()
        if not perm:
            raise PermissionNotFoundError(permission_name="users:delete")
    """

    def __init__(self, permission_name: str = None, permission_id: int = None, message: str = None):
        self.permission_name = permission_name
        self.permission_id = permission_id

        if message is None:
            if permission_name:
                message = f"Permission not found: {permission_name}"
            elif permission_id:
                message = f"Permission not found: id={permission_id}"
            else:
                message = "Permission not found"

        super().__init__(message, code="PERMISSION_NOT_FOUND")


class RoleAssignmentError(RBACError):
    """
    Raised when there's an error assigning or revoking a role.

    This is converted to a 400 Bad Request HTTP response.

    Usage:
        if user.has_role("admin"):
            raise RoleAssignmentError(
                message="User already has the admin role",
                user_id=user.id,
                role_name="admin"
            )
    """

    def __init__(
        self,
        message: str,
        user_id: int = None,
        role_name: str = None,
    ):
        self.user_id = user_id
        self.role_name = role_name
        super().__init__(message, code="ROLE_ASSIGNMENT_ERROR")


class SystemRoleError(RBACError):
    """
    Raised when attempting an invalid operation on a system role.

    System roles (is_system_role=True) have restrictions:
    - Cannot be deleted
    - Some modifications may be restricted

    This is converted to a 403 Forbidden HTTP response.

    Usage:
        if role.is_system_role:
            raise SystemRoleError(
                role_name="admin",
                message="Cannot delete system role 'admin'"
            )
    """

    def __init__(self, role_name: str, message: str = None):
        self.role_name = role_name

        if message is None:
            message = f"Cannot modify system role: {role_name}"

        super().__init__(message, code="SYSTEM_ROLE_ERROR")


class DirectPermissionError(RBACError):
    """
    Raised when there's an error with direct permission assignment.

    This is converted to a 400 Bad Request HTTP response.

    Usage:
        if user has permission already:
            raise DirectPermissionError(
                message="User already has this permission",
                user_id=user.id,
                permission_name="users:delete"
            )
    """

    def __init__(
        self,
        message: str,
        user_id: int = None,
        permission_name: str = None,
    ):
        self.user_id = user_id
        self.permission_name = permission_name
        super().__init__(message, code="DIRECT_PERMISSION_ERROR")
