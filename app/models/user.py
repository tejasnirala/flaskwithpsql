"""
User Model
==========
User model representing the users table in PostgreSQL.
Inherits from BaseModel to get common fields (id, created_at, updated_at, is_deleted).

RBAC Integration:
-----------------
This model includes relationships for Role-Based Access Control:
- roles: Roles assigned to this user (provides permissions from roles)
- direct_permissions: Permissions granted directly to this user (extra/override)

Effective permissions = Role Permissions + Direct Permissions
"""

from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.orm import relationship

from app.models.associations import user_permissions, user_roles
from app.models.base import BaseModel


class User(BaseModel):
    """
    User model representing the users table in PostgreSQL.

    Inherits from BaseModel:
        - id (Integer, Primary Key)
        - created_at (DateTime)
        - updated_at (DateTime)
        - is_deleted (Boolean)

    This model adds user-specific fields on top of the base fields.

    RBAC Relationships:
        - roles: Many-to-many with Role (provides role-based permissions)
        - direct_permissions: Many-to-many with Permission (extra permissions)
    """

    __tablename__ = "users"
    __table_args__ = {"schema": "users"}

    # ========================================================================
    # USER INFORMATION (Unique identifiers)
    # ========================================================================
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)

    # ========================================================================
    # PROFILE INFORMATION
    # ========================================================================
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)

    # ========================================================================
    # STATUS FLAGS
    # ========================================================================
    # Note: is_deleted is inherited from BaseModel
    is_active = Column(Boolean, default=True)

    # ========================================================================
    # RBAC RELATIONSHIPS
    # ========================================================================
    # Many-to-many: User ←→ Role (via user_roles table)
    # A user can have multiple roles, and each role gives them permissions
    # Example: user.roles → [Role("moderator"), Role("support")]
    #
    # NOTE: We explicitly specify foreign_keys because user_roles has TWO
    # foreign keys to the users table (user_id and assigned_by).
    # We tell SQLAlchemy: "use user_id to link to User, use role_id to link to Role"
    # Without this, SQLAlchemy throws AmbiguousForeignKeysError.
    roles = relationship(
        "Role",
        secondary=user_roles,
        foreign_keys=[user_roles.c.user_id, user_roles.c.role_id],
        back_populates="users",
        lazy="selectin",  # Eager load for permission checks
    )

    # Many-to-many: User ←→ Permission (direct/extra permissions)
    # These are permissions granted DIRECTLY to the user (not through roles)
    # Use sparingly - most permissions should come from roles
    # Example: user.direct_permissions → [Permission("users:delete")]
    #
    # NOTE: Same issue - user_permissions has TWO FKs to users
    # (user_id and granted_by), so we specify foreign_keys explicitly.
    direct_permissions = relationship(
        "Permission",
        secondary=user_permissions,
        foreign_keys=[user_permissions.c.user_id, user_permissions.c.permission_id],
        lazy="selectin",  # Eager load for permission checks
    )

    # ========================================================================
    # METHODS
    # ========================================================================

    def __repr__(self):
        """String representation of the User."""
        return f"<User {self.username}>"

    def to_dict(self, include_roles: bool = False):
        """
        Convert user object to dictionary.

        Uses to_base_dict() from BaseModel for common fields,
        then adds user-specific fields.

        Args:
            include_roles: If True, include role names in the response

        Returns:
            dict: Dictionary representation of the user (excluding password)
        """
        # Start with base fields (id, created_at, updated_at, is_deleted)
        data = self.to_base_dict()

        # Add user-specific fields
        data.update(
            {
                "username": self.username,
                "email": self.email,
                "first_name": self.first_name,
                "middle_name": self.middle_name,
                "last_name": self.last_name,
                "bio": self.bio,
                "is_active": self.is_active,
            }
        )

        if include_roles:
            data["roles"] = [role.name for role in self.roles]

        return data

    # ========================================================================
    # RBAC HELPER METHODS
    # ========================================================================

    def get_all_permissions(self) -> set:
        """
        Get all effective permissions for this user.

        Combines:
        1. Permissions from assigned roles (including inherited)
        2. Direct permissions assigned to the user

        Returns:
            set: Set of permission name strings

        Example:
            user.roles = [moderator]  # has users:read, users:update
            user.direct_permissions = [users:delete]
            user.get_all_permissions() → {"users:read", "users:update", "users:delete"}
        """
        permissions = set()

        # Get permissions from all roles (including role inheritance)
        for role in self.roles:
            permissions.update(role.get_all_permissions())

        # Add direct permissions
        for perm in self.direct_permissions:
            permissions.add(perm.name)

        return permissions

    def has_permission(self, permission_name: str) -> bool:
        """
        Check if user has a specific permission.

        Checks both role-based and direct permissions.
        Also handles wildcard permissions (*:* and resource:*).

        Args:
            permission_name: Permission to check (e.g., "users:delete")

        Returns:
            bool: True if user has the permission

        Example:
            if user.has_permission("users:delete"):
                # User can delete users
                pass
        """
        all_perms = self.get_all_permissions()

        # Exact match
        if permission_name in all_perms:
            return True

        # Wildcard: super admin (*:*)
        if "*:*" in all_perms:
            return True

        # Wildcard: resource-level (e.g., users:*)
        if ":" in permission_name:
            resource, _ = permission_name.split(":", 1)
            if f"{resource}:*" in all_perms:
                return True

        return False

    def has_role(self, role_name: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            role_name: Role name to check (e.g., "admin")

        Returns:
            bool: True if user has the role
        """
        return any(role.name == role_name for role in self.roles)

    def has_any_role(self, *role_names: str) -> bool:
        """
        Check if user has ANY of the specified roles.

        Args:
            *role_names: Role names to check

        Returns:
            bool: True if user has at least one of the roles
        """
        user_role_names = {role.name for role in self.roles}
        return bool(user_role_names.intersection(role_names))

    def has_all_roles(self, *role_names: str) -> bool:
        """
        Check if user has ALL of the specified roles.

        Args:
            *role_names: Role names to check

        Returns:
            bool: True if user has all the roles
        """
        user_role_names = {role.name for role in self.roles}
        return all(role_name in user_role_names for role_name in role_names)

    # ========================================================================
    # PASSWORD METHODS
    # ========================================================================

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password for storing using secure werkzeug functions.

        Uses PBKDF2 with SHA-256 by default, which is:
        - Slow by design (resistant to brute-force)
        - Automatically salted (resistant to rainbow tables)
        - Industry standard for password hashing

        Args:
            password: The plain text password to hash

        Returns:
            str: The hashed password (includes algorithm, salt, and hash)

        Example:
            >>> User.hash_password("MySecurePass123")
            'pbkdf2:sha256:600000$...$...'
        """
        from werkzeug.security import generate_password_hash

        return generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Verify a password against the stored hash.

        Uses werkzeug's secure comparison which is:
        - Timing-attack safe
        - Handles the salt extraction automatically

        Args:
            password: The plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        from werkzeug.security import check_password_hash

        return check_password_hash(self.password_hash, password)

    def set_password(self, password: str) -> None:
        """
        Set a new password for the user.

        Convenience method that hashes and stores the password.

        Args:
            password: The plain text password to set
        """
        self.password_hash = self.hash_password(password)
