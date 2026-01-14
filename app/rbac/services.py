"""
RBAC Service
============
Business logic layer for Role-Based Access Control operations.

This service handles:
1. Permission checking (has_permission, has_role)
2. Role management (assign, revoke, create, update, delete)
3. Direct permission management (grant, revoke)
4. Caching (optional, for performance)

Design Principles:
------------------
- Single Responsibility: Only handles RBAC operations
- Separation of Concerns: Business logic separate from routes/models
- DRY: Common operations in reusable methods
- Testable: Pure functions, easy to mock dependencies

Usage:
    from app.rbac.services import RBACService

    # Check permissions
    if RBACService.user_has_permission(user, "users:delete"):
        # Allow action
        pass

    # Assign role
    RBACService.assign_role_to_user(user, "moderator", assigned_by=admin)
"""

import logging
from typing import List, Optional, Set, Tuple

from app import db
from app.models import Permission, Role, User
from app.rbac.exceptions import (
    DirectPermissionError,
    PermissionDeniedError,
    PermissionNotFoundError,
    RoleAssignmentError,
    RoleNotFoundError,
    SystemRoleError,
)
from app.rbac.permissions import PermissionRegistry

logger = logging.getLogger(__name__)


class RBACService:
    """
    Service class for Role-Based Access Control operations.

    All methods are static/class methods for stateless operation.
    This makes the service easy to use and test.
    """

    # =========================================================================
    # PERMISSION CHECKING
    # =========================================================================

    @staticmethod
    def user_has_permission(user: User, permission: str) -> bool:
        """
        Check if a user has a specific permission.

        Checks:
        1. Direct permissions assigned to the user
        2. Permissions from assigned roles (including inherited)
        3. Wildcard permissions (*:* and resource:*)

        Args:
            user: The User object to check
            permission: Permission string (e.g., "users:delete")

        Returns:
            bool: True if user has the permission

        Example:
            if RBACService.user_has_permission(user, "users:delete"):
                # User can delete users
                pass
        """
        if user is None:
            return False

        return user.has_permission(permission)

    @staticmethod
    def user_has_role(user: User, role_name: str) -> bool:
        """
        Check if a user has a specific role.

        Args:
            user: The User object to check
            role_name: Role name (e.g., "admin")

        Returns:
            bool: True if user has the role
        """
        if user is None:
            return False

        return user.has_role(role_name)

    @staticmethod
    def user_has_any_permission(user: User, permissions: List[str]) -> bool:
        """
        Check if user has ANY of the specified permissions.

        Args:
            user: The User object to check
            permissions: List of permission strings

        Returns:
            bool: True if user has at least one permission
        """
        if user is None:
            return False

        return any(user.has_permission(perm) for perm in permissions)

    @staticmethod
    def user_has_all_permissions(user: User, permissions: List[str]) -> bool:
        """
        Check if user has ALL of the specified permissions.

        Args:
            user: The User object to check
            permissions: List of permission strings

        Returns:
            bool: True if user has all permissions
        """
        if user is None:
            return False

        return all(user.has_permission(perm) for perm in permissions)

    @staticmethod
    def get_user_permissions(user: User) -> Set[str]:
        """
        Get all effective permissions for a user.

        Returns set of permission strings from:
        - All assigned roles (including inherited)
        - Direct permissions

        Args:
            user: The User object

        Returns:
            Set[str]: Set of permission strings
        """
        if user is None:
            return set()

        return user.get_all_permissions()

    @staticmethod
    def get_user_roles(user: User) -> List[Role]:
        """
        Get all roles assigned to a user.

        Args:
            user: The User object

        Returns:
            List[Role]: List of Role objects
        """
        if user is None:
            return []

        return list(user.roles)

    # =========================================================================
    # ROLE MANAGEMENT
    # =========================================================================

    @staticmethod
    def get_role_by_name(role_name: str) -> Optional[Role]:
        """
        Get a role by its name.

        Args:
            role_name: The role name (e.g., "admin")

        Returns:
            Role object or None if not found
        """
        return Role.query.filter_by(name=role_name, is_deleted=False).first()

    @staticmethod
    def get_role_by_id(role_id: int) -> Optional[Role]:
        """
        Get a role by its ID.

        Args:
            role_id: The role ID

        Returns:
            Role object or None if not found
        """
        return Role.query.filter_by(id=role_id, is_deleted=False).first()

    @staticmethod
    def get_role_or_404(role_name: str = None, role_id: int = None) -> Role:
        """
        Get a role or raise RoleNotFoundError.

        Args:
            role_name: The role name
            role_id: The role ID (alternative to name)

        Returns:
            Role object

        Raises:
            RoleNotFoundError: If role doesn't exist
        """
        role = None

        if role_name:
            role = RBACService.get_role_by_name(role_name)
        elif role_id:
            role = RBACService.get_role_by_id(role_id)

        if role is None:
            raise RoleNotFoundError(role_name=role_name, role_id=role_id)

        return role

    @staticmethod
    def assign_role_to_user(user: User, role_name: str, assigned_by: Optional[User] = None) -> Role:
        """
        Assign a role to a user.

        Args:
            user: The User to assign the role to
            role_name: The name of the role to assign
            assigned_by: The admin user who is assigning (for audit)

        Returns:
            The assigned Role object

        Raises:
            RoleNotFoundError: If role doesn't exist
            RoleAssignmentError: If user already has the role
        """
        role = RBACService.get_role_or_404(role_name=role_name)

        # Check if user already has this role
        if user.has_role(role_name):
            raise RoleAssignmentError(
                message=f"User already has role '{role_name}'",
                user_id=user.id,
                role_name=role_name,
            )

        # Assign the role
        user.roles.append(role)
        db.session.commit()

        logger.info(
            f"Role '{role_name}' assigned to user_id={user.id} "
            f"by user_id={assigned_by.id if assigned_by else 'system'}"
        )

        return role

    @staticmethod
    def revoke_role_from_user(
        user: User, role_name: str, revoked_by: Optional[User] = None
    ) -> Role:
        """
        Revoke a role from a user.

        Args:
            user: The User to revoke the role from
            role_name: The name of the role to revoke
            revoked_by: The admin user who is revoking (for audit)

        Returns:
            The revoked Role object

        Raises:
            RoleNotFoundError: If role doesn't exist
            RoleAssignmentError: If user doesn't have the role
        """
        role = RBACService.get_role_or_404(role_name=role_name)

        # Check if user has this role
        if not user.has_role(role_name):
            raise RoleAssignmentError(
                message=f"User doesn't have role '{role_name}'",
                user_id=user.id,
                role_name=role_name,
            )

        # Revoke the role
        user.roles.remove(role)
        db.session.commit()

        logger.info(
            f"Role '{role_name}' revoked from user_id={user.id} "
            f"by user_id={revoked_by.id if revoked_by else 'system'}"
        )

        return role

    @staticmethod
    def create_role(
        name: str,
        display_name: str,
        description: Optional[str] = None,
        permission_names: Optional[List[str]] = None,
        parent_role_name: Optional[str] = None,
        is_system_role: bool = False,
    ) -> Role:
        """
        Create a new role.

        Args:
            name: Unique role identifier (lowercase)
            display_name: Human-friendly display name
            description: Role description
            permission_names: List of permission names to assign
            parent_role_name: Name of parent role for inheritance
            is_system_role: If True, role cannot be deleted

        Returns:
            The created Role object

        Raises:
            RoleAssignmentError: If role name already exists
            RoleNotFoundError: If parent role doesn't exist
            PermissionNotFoundError: If a permission doesn't exist
        """
        # Check if role already exists
        existing = Role.query.filter_by(name=name).first()
        if existing:
            raise RoleAssignmentError(
                message=f"Role '{name}' already exists",
                role_name=name,
            )

        # Get parent role if specified
        parent_role = None
        if parent_role_name:
            parent_role = RBACService.get_role_or_404(role_name=parent_role_name)

        # Create the role
        role = Role(
            name=name,
            display_name=display_name,
            description=description,
            is_system_role=is_system_role,
            parent_role_id=parent_role.id if parent_role else None,
        )

        # Assign permissions
        if permission_names:
            for perm_name in permission_names:
                perm = Permission.query.filter_by(name=perm_name, is_deleted=False).first()
                if perm is None:
                    raise PermissionNotFoundError(permission_name=perm_name)
                role.permissions.append(perm)

        db.session.add(role)
        db.session.commit()

        logger.info(f"Created role '{name}' with {len(permission_names or [])} permissions")

        return role

    @staticmethod
    def delete_role(role_name: str, deleted_by: Optional[User] = None) -> Role:
        """
        Delete a role (soft delete).

        Args:
            role_name: The name of the role to delete
            deleted_by: The admin user who is deleting (for audit)

        Returns:
            The deleted Role object

        Raises:
            RoleNotFoundError: If role doesn't exist
            SystemRoleError: If trying to delete a system role
        """
        role = RBACService.get_role_or_404(role_name=role_name)

        # Check if system role
        if role.is_system_role:
            raise SystemRoleError(
                role_name=role_name,
                message=f"Cannot delete system role '{role_name}'",
            )

        # Soft delete
        role.soft_delete()
        db.session.commit()

        logger.info(
            f"Role '{role_name}' deleted by user_id={deleted_by.id if deleted_by else 'system'}"
        )

        return role

    # =========================================================================
    # DIRECT PERMISSION MANAGEMENT
    # =========================================================================

    @staticmethod
    def get_permission_by_name(permission_name: str) -> Optional[Permission]:
        """
        Get a permission by its name.

        Args:
            permission_name: The permission name (e.g., "users:delete")

        Returns:
            Permission object or None if not found
        """
        return Permission.query.filter_by(name=permission_name, is_deleted=False).first()

    @staticmethod
    def get_permission_or_404(permission_name: str) -> Permission:
        """
        Get a permission or raise PermissionNotFoundError.

        Args:
            permission_name: The permission name

        Returns:
            Permission object

        Raises:
            PermissionNotFoundError: If permission doesn't exist
        """
        perm = RBACService.get_permission_by_name(permission_name)

        if perm is None:
            raise PermissionNotFoundError(permission_name=permission_name)

        return perm

    @staticmethod
    def grant_direct_permission(
        user: User,
        permission_name: str,
        granted_by: Optional[User] = None,
        reason: Optional[str] = None,
    ) -> Permission:
        """
        Grant a direct permission to a user.

        Direct permissions are assigned directly to a user (not through roles).
        Use sparingly - most permissions should come from roles.

        Args:
            user: The User to grant the permission to
            permission_name: The permission to grant
            granted_by: The admin user who is granting (for audit)
            reason: Reason for granting (for audit trail)

        Returns:
            The granted Permission object

        Raises:
            PermissionNotFoundError: If permission doesn't exist
            DirectPermissionError: If user already has this direct permission
        """
        perm = RBACService.get_permission_or_404(permission_name)

        # Check if user already has this direct permission
        if perm in user.direct_permissions:
            raise DirectPermissionError(
                message=f"User already has direct permission '{permission_name}'",
                user_id=user.id,
                permission_name=permission_name,
            )

        # Grant the permission
        user.direct_permissions.append(perm)
        db.session.commit()

        logger.info(
            f"Direct permission '{permission_name}' granted to user_id={user.id} "
            f"by user_id={granted_by.id if granted_by else 'system'}, reason={reason}"
        )

        return perm

    @staticmethod
    def revoke_direct_permission(
        user: User,
        permission_name: str,
        revoked_by: Optional[User] = None,
    ) -> Permission:
        """
        Revoke a direct permission from a user.

        Args:
            user: The User to revoke the permission from
            permission_name: The permission to revoke
            revoked_by: The admin user who is revoking (for audit)

        Returns:
            The revoked Permission object

        Raises:
            PermissionNotFoundError: If permission doesn't exist
            DirectPermissionError: If user doesn't have this direct permission
        """
        perm = RBACService.get_permission_or_404(permission_name)

        # Check if user has this direct permission
        if perm not in user.direct_permissions:
            raise DirectPermissionError(
                message=f"User doesn't have direct permission '{permission_name}'",
                user_id=user.id,
                permission_name=permission_name,
            )

        # Revoke the permission
        user.direct_permissions.remove(perm)
        db.session.commit()

        logger.info(
            f"Direct permission '{permission_name}' revoked from user_id={user.id} "
            f"by user_id={revoked_by.id if revoked_by else 'system'}"
        )

        return perm

    @staticmethod
    def get_user_direct_permissions(user: User) -> List[Permission]:
        """
        Get all direct permissions for a user.

        Args:
            user: The User object

        Returns:
            List[Permission]: List of direct Permission objects
        """
        if user is None:
            return []

        return list(user.direct_permissions)

    # =========================================================================
    # AUTHORIZATION HELPERS
    # =========================================================================

    @staticmethod
    def require_permission(user: User, permission: str) -> None:
        """
        Require that a user has a specific permission.

        Raises PermissionDeniedError if the user doesn't have the permission.
        Useful in service methods that need to enforce authorization.

        Args:
            user: The User object to check
            permission: Permission string required

        Raises:
            PermissionDeniedError: If user lacks the permission

        Example:
            def delete_user(admin_user, user_id):
                RBACService.require_permission(admin_user, "users:delete")
                # If we get here, user has permission
                User.query.get(user_id).soft_delete()
        """
        if not RBACService.user_has_permission(user, permission):
            raise PermissionDeniedError(permission=permission)

    @staticmethod
    def require_any_permission(user: User, permissions: List[str]) -> None:
        """
        Require that a user has at least one of the specified permissions.

        Args:
            user: The User object to check
            permissions: List of permission strings (user needs at least one)

        Raises:
            PermissionDeniedError: If user lacks all permissions
        """
        if not RBACService.user_has_any_permission(user, permissions):
            raise PermissionDeniedError(
                message=f"Requires one of: {', '.join(permissions)}",
                required_permissions=permissions,
            )

    @staticmethod
    def require_all_permissions(user: User, permissions: List[str]) -> None:
        """
        Require that a user has all of the specified permissions.

        Args:
            user: The User object to check
            permissions: List of permission strings (user needs all)

        Raises:
            PermissionDeniedError: If user lacks any permission
        """
        if not RBACService.user_has_all_permissions(user, permissions):
            raise PermissionDeniedError(
                message=f"Requires all of: {', '.join(permissions)}",
                required_permissions=permissions,
            )

    # =========================================================================
    # SEEDING
    # =========================================================================

    @staticmethod
    def seed_permissions() -> Tuple[int, int]:
        """
        Seed all permissions from the registry to the database.

        If a permission already exists, it's skipped.

        Returns:
            Tuple of (created_count, skipped_count)
        """
        created = 0
        skipped = 0

        for perm_name, description in PermissionRegistry.PERMISSIONS.items():
            # Check if permission exists
            existing = Permission.query.filter_by(name=perm_name).first()
            if existing:
                skipped += 1
                continue

            # Parse resource:action
            if ":" in perm_name:
                resource, action = perm_name.split(":", 1)
            else:
                resource = perm_name
                action = "*"

            # Create permission
            perm = Permission(
                name=perm_name,
                resource=resource,
                action=action,
                description=description,
            )
            db.session.add(perm)
            created += 1

        db.session.commit()
        logger.info(f"Seeded permissions: {created} created, {skipped} skipped")

        return created, skipped

    @staticmethod
    def seed_roles() -> Tuple[int, int]:
        """
        Seed default roles from the registry to the database.

        If a role already exists, it's skipped.
        Requires permissions to be seeded first!

        Returns:
            Tuple of (created_count, skipped_count)
        """
        created = 0
        skipped = 0

        for role_name, (
            display_name,
            description,
            permission_names,
            is_system,
        ) in PermissionRegistry.DEFAULT_ROLES.items():
            # Check if role exists
            existing = Role.query.filter_by(name=role_name).first()
            if existing:
                skipped += 1
                continue

            # Create role
            role = Role(
                name=role_name,
                display_name=display_name,
                description=description,
                is_system_role=is_system,
            )

            # Assign permissions
            for perm_name in permission_names:
                perm = Permission.query.filter_by(name=perm_name).first()
                if perm:
                    role.permissions.append(perm)

            db.session.add(role)
            created += 1

        db.session.commit()
        logger.info(f"Seeded roles: {created} created, {skipped} skipped")

        return created, skipped

    @staticmethod
    def seed_all() -> dict:
        """
        Seed all RBAC data (permissions and roles).

        Returns:
            Dict with seeding results
        """
        perm_created, perm_skipped = RBACService.seed_permissions()
        role_created, role_skipped = RBACService.seed_roles()

        return {
            "permissions": {"created": perm_created, "skipped": perm_skipped},
            "roles": {"created": role_created, "skipped": role_skipped},
        }
