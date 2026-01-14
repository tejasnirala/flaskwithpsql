"""
Permission Registry
===================
Central registry of all permissions in the RBAC system.

This module defines:
1. Resource enum - Available resources in the system
2. Action enum - Available actions on resources
3. PermissionRegistry - Central list of all permissions with descriptions

Naming Convention:
------------------
Permissions follow the format: {resource}:{action}

Examples:
    users:read      - View user information
    users:create    - Create new users
    users:delete    - Delete users
    roles:assign    - Assign roles to users
    *:*             - Super admin (all permissions)

Design Decisions:
-----------------
1. Centralized Registry
   - All permissions defined in one place
   - Easy to add/remove permissions
   - Self-documenting

2. Enum-based Resources and Actions
   - Type safety
   - IDE autocompletion
   - Prevents typos

3. Description for each permission
   - Clear documentation for admins
   - Shown in admin UI

Usage:
    from app.rbac.permissions import PermissionRegistry, Resources, Actions

    # Get all permission names
    all_perms = PermissionRegistry.all_permissions()

    # Get description
    desc = PermissionRegistry.get_description("users:delete")
"""

from enum import Enum
from typing import Dict, List, Tuple


class Resources(str, Enum):
    """
    Available resources in the system.

    Each resource represents a domain entity that can be accessed/modified.
    Add new resources here as your application grows.
    """

    USERS = "users"
    ROLES = "roles"
    PERMISSIONS = "permissions"

    # Add more resources as needed:
    # POSTS = "posts"
    # COMMENTS = "comments"
    # SETTINGS = "settings"


class Actions(str, Enum):
    """
    Available actions on resources.

    Standard CRUD actions plus special actions.
    """

    # Standard CRUD
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"

    # Special actions
    ASSIGN = "assign"  # For role/permission assignment
    REVOKE = "revoke"  # For role/permission revocation
    LIST = "list"  # For listing resources (separate from read)
    EXPORT = "export"  # For exporting data

    # Wildcard
    ALL = "*"  # All actions on a resource


class PermissionRegistry:
    """
    Central registry of all permissions in the system.

    This class provides:
    1. A complete list of all valid permissions
    2. Descriptions for each permission
    3. Helper methods for working with permissions

    All permissions should be registered here to ensure:
    - Consistency across the codebase
    - Single source of truth
    - Easy auditing
    """

    # =========================================================================
    # PERMISSION DEFINITIONS
    # =========================================================================
    # Format: "resource:action": "Human-readable description"
    #
    # Organize by resource for readability

    PERMISSIONS: Dict[str, str] = {
        # =====================================================================
        # USER PERMISSIONS
        # =====================================================================
        "users:read": "View user profiles and information",
        "users:create": "Create new user accounts",
        "users:update": "Update user profile information",
        "users:delete": "Delete user accounts (soft delete)",
        "users:list": "List all users in the system",
        # =====================================================================
        # ROLE PERMISSIONS
        # =====================================================================
        "roles:read": "View role details and their permissions",
        "roles:create": "Create new roles",
        "roles:update": "Modify role settings and permissions",
        "roles:delete": "Delete roles (non-system roles only)",
        "roles:list": "List all roles in the system",
        "roles:assign": "Assign roles to users",
        "roles:revoke": "Revoke roles from users",
        # =====================================================================
        # PERMISSION MANAGEMENT
        # =====================================================================
        "permissions:read": "View permission details",
        "permissions:list": "List all permissions in the system",
        "permissions:assign": "Assign direct permissions to users",
        "permissions:revoke": "Revoke direct permissions from users",
        # =====================================================================
        # WILDCARD PERMISSIONS
        # =====================================================================
        "*:*": "Full system access (super admin)",
        "users:*": "All permissions on users",
        "roles:*": "All permissions on roles",
        "permissions:*": "All permissions on permissions",
    }

    # =========================================================================
    # DEFAULT ROLES CONFIGURATION
    # =========================================================================
    # These roles will be created when seeding the database
    # Format: role_name: (display_name, description, [permissions], is_system_role)

    DEFAULT_ROLES: Dict[str, Tuple[str, str, List[str], bool]] = {
        "super_admin": (
            "Super Administrator",
            "Full system access with all permissions",
            ["*:*"],
            True,  # is_system_role - cannot be deleted
        ),
        "admin": (
            "Administrator",
            "Administrative access for managing users and roles",
            [
                "users:read",
                "users:create",
                "users:update",
                "users:delete",
                "users:list",
                "roles:read",
                "roles:list",
                "roles:assign",
                "roles:revoke",
                "permissions:read",
                "permissions:list",
            ],
            True,
        ),
        "moderator": (
            "Moderator",
            "Content moderation with limited user management",
            [
                "users:read",
                "users:update",
                "users:list",
            ],
            True,
        ),
        "user": (
            "Regular User",
            "Basic user access with read-only permissions",
            [
                "users:read",  # Can read own profile
            ],
            True,
        ),
    }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @classmethod
    def all_permissions(cls) -> List[str]:
        """
        Get a list of all registered permission names.

        Returns:
            List[str]: List of permission strings

        Example:
            ['users:read', 'users:create', 'users:delete', ...]
        """
        return list(cls.PERMISSIONS.keys())

    @classmethod
    def get_description(cls, permission: str) -> str:
        """
        Get the description for a permission.

        Args:
            permission: Permission string (e.g., "users:delete")

        Returns:
            str: Description or "No description" if not found
        """
        return cls.PERMISSIONS.get(permission, "No description")

    @classmethod
    def is_valid_permission(cls, permission: str) -> bool:
        """
        Check if a permission is registered.

        Args:
            permission: Permission string to validate

        Returns:
            bool: True if permission exists in registry
        """
        return permission in cls.PERMISSIONS

    @classmethod
    def get_resource_permissions(cls, resource: str) -> List[str]:
        """
        Get all permissions for a specific resource.

        Args:
            resource: Resource name (e.g., "users")

        Returns:
            List[str]: Permissions for that resource

        Example:
            get_resource_permissions("users")
            → ['users:read', 'users:create', 'users:update', 'users:delete']
        """
        return [
            perm
            for perm in cls.PERMISSIONS.keys()
            if perm.startswith(f"{resource}:") and not perm.startswith("*")
        ]

    @classmethod
    def get_permissions_by_action(cls, action: str) -> List[str]:
        """
        Get all permissions with a specific action.

        Args:
            action: Action name (e.g., "delete")

        Returns:
            List[str]: Permissions with that action

        Example:
            get_permissions_by_action("delete")
            → ['users:delete', 'roles:delete']
        """
        return [perm for perm in cls.PERMISSIONS.keys() if perm.endswith(f":{action}")]

    @classmethod
    def get_all_with_descriptions(cls) -> List[Dict[str, str]]:
        """
        Get all permissions with their descriptions.

        Returns:
            List of dicts with 'name' and 'description' keys.

        Useful for admin UI lists.
        """
        return [{"name": name, "description": desc} for name, desc in cls.PERMISSIONS.items()]
