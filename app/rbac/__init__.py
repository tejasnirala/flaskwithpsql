"""
RBAC Module
===========
Role-Based Access Control for Flask applications.

This module provides a complete RBAC implementation with:
1. Permission-based access control
2. Role-based access control
3. Role inheritance (hierarchical roles)
4. Direct user permissions (exceptions/overrides)

Quick Start:
------------
    from app.rbac import permission_required, role_required

    # Require specific permission
    @app.route("/users/<id>", methods=["DELETE"])
    @permission_required("users:delete")
    def delete_user(id):
        pass

    # Require specific role
    @app.route("/admin")
    @role_required("admin")
    def admin_panel():
        pass

Components:
-----------
- decorators.py: Route protection decorators
- services.py: Business logic for RBAC operations
- permissions.py: Central permission registry
- exceptions.py: Custom RBAC exceptions

Architecture:
-------------
    ┌─────────┐    has    ┌─────────┐    has    ┌─────────────────┐
    │  User   │ ────────▶ │  Role   │ ────────▶ │   Permission    │
    └─────────┘           └─────────┘           └─────────────────┘
         │                     │
         │                     │ inherits from
         │                     ▼
         │               ┌───────────┐
         │               │Parent Role│
         │               └───────────┘
         │
         │  direct       ┌─────────────────┐
         └─────────────▶ │   Permission    │
           (extra)       └─────────────────┘

Usage Examples:
---------------
See individual module docstrings for detailed usage.
"""

# =============================================================================
# DECORATORS (Route Protection)
# =============================================================================
from app.rbac.decorators import (
    admin_required,
    check_permission,
    check_role,
    permission_required,
    role_required,
    super_admin_required,
)

# =============================================================================
# EXCEPTIONS
# =============================================================================
from app.rbac.exceptions import (
    DirectPermissionError,
    PermissionDeniedError,
    PermissionNotFoundError,
    RBACError,
    RoleAssignmentError,
    RoleNotFoundError,
    SystemRoleError,
)

# =============================================================================
# PERMISSIONS REGISTRY
# =============================================================================
from app.rbac.permissions import Actions, PermissionRegistry, Resources

# =============================================================================
# SERVICE (Business Logic)
# =============================================================================
from app.rbac.services import RBACService

# =============================================================================
# PUBLIC API
# =============================================================================
__all__ = [
    # Decorators
    "permission_required",
    "role_required",
    "admin_required",
    "super_admin_required",
    "check_permission",
    "check_role",
    # Service
    "RBACService",
    # Exceptions
    "RBACError",
    "PermissionDeniedError",
    "RoleNotFoundError",
    "PermissionNotFoundError",
    "RoleAssignmentError",
    "SystemRoleError",
    "DirectPermissionError",
    # Registry
    "PermissionRegistry",
    "Resources",
    "Actions",
]
