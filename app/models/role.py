"""
Role Model
==========
Represents a role in the RBAC system.

Roles group permissions together and can be assigned to users.
A user with a role inherits ALL permissions assigned to that role.

Design Decisions:
-----------------
1. Role Hierarchy (parent_role_id)
   - Roles can inherit from a parent role
   - Child role gets all parent's permissions PLUS its own
   - Example: "admin" inherits from "moderator" inherits from "user"

2. System Roles (is_system_role)
   - Cannot be deleted via API
   - Protects critical roles like "super_admin"
   - Prevents accidental lockout

3. Stored in 'rbac' schema
   - Logical separation from user data
   - Clear ownership of RBAC tables

Role Inheritance Example:
-------------------------
    user (base role)
      ↓ inherits
    moderator (can read + update users)
      ↓ inherits
    admin (can create + delete users)
      ↓ inherits
    super_admin (full access)
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.associations import role_permissions, user_roles
from app.models.base import BaseModel


class Role(BaseModel):
    """
    Role model representing a role in the RBAC system.

    Inherits from BaseModel:
        - id (Integer, Primary Key)
        - created_at (DateTime)
        - updated_at (DateTime)
        - is_deleted (Boolean)

    Attributes:
        name: Unique role identifier (lowercase, e.g., "admin")
        display_name: Human-friendly name (e.g., "Administrator")
        description: Description of the role
        is_system_role: If True, cannot be deleted
        parent_role_id: ID of parent role for inheritance

    Relationships:
        permissions: Many-to-many with Permission (via role_permissions)
        users: Many-to-many with User (via user_roles)
        parent_role: Self-referential for role hierarchy
        child_roles: Roles that inherit from this role

    Example:
        admin_role = Role(
            name="admin",
            display_name="Administrator",
            description="Full administrative access",
            is_system_role=True
        )
    """

    __tablename__ = "roles"
    __table_args__ = {"schema": "rbac"}

    # ========================================================================
    # ROLE IDENTIFICATION
    # ========================================================================
    # Unique identifier used in code: @role_required("admin")
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique role identifier (lowercase, e.g., 'admin')",
    )

    # Human-friendly name for display in UI
    display_name = Column(
        String(100),
        nullable=False,
        comment="Human-friendly display name (e.g., 'Administrator')",
    )

    # ========================================================================
    # DESCRIPTION
    # ========================================================================
    description = Column(
        Text,
        nullable=True,
        comment="Description of this role and its purpose",
    )

    # ========================================================================
    # SYSTEM PROTECTION
    # ========================================================================
    # System roles cannot be deleted via API
    # Protects critical roles like "super_admin"
    is_system_role = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="If True, this role cannot be deleted (protected)",
    )

    # ========================================================================
    # ROLE HIERARCHY (Inheritance)
    # ========================================================================
    # A role can inherit permissions from a parent role
    # This enables role hierarchies like: user → moderator → admin
    parent_role_id = Column(
        Integer,
        ForeignKey("rbac.roles.id"),
        nullable=True,
        comment="Parent role ID for permission inheritance",
    )

    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    # Many-to-many: Role ←→ Permission (via role_permissions table)
    # Lazy loading for performance (loads only when accessed)
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        lazy="selectin",  # Eager load when role is queried
        backref="roles",
    )

    # Many-to-many: Role ←→ User (via user_roles table)
    # backref creates User.roles automatically
    #
    # NOTE: We explicitly specify foreign_keys because user_roles has TWO
    # foreign keys to users table (user_id and assigned_by).
    # We tell SQLAlchemy: "use role_id to link to Role, use user_id to link to User"
    # Without this, SQLAlchemy throws AmbiguousForeignKeysError.
    users = relationship(
        "User",
        secondary=user_roles,
        foreign_keys=[user_roles.c.role_id, user_roles.c.user_id],
        back_populates="roles",
        lazy="dynamic",  # Returns query for large user sets
    )

    # Self-referential: Role hierarchy
    # parent_role: The role this role inherits from
    parent_role = relationship(
        "Role",
        remote_side="Role.id",
        backref="child_roles",
        foreign_keys=[parent_role_id],
    )

    # ========================================================================
    # METHODS
    # ========================================================================

    def __repr__(self) -> str:
        """String representation of the Role."""
        return f"<Role {self.name}>"

    def to_dict(self, include_permissions: bool = False) -> dict:
        """
        Convert role to dictionary.

        Args:
            include_permissions: If True, include list of permission names

        Returns:
            dict: Dictionary representation of the role
        """
        data = self.to_base_dict()
        data.update(
            {
                "name": self.name,
                "display_name": self.display_name,
                "description": self.description,
                "is_system_role": self.is_system_role,
                "parent_role_id": self.parent_role_id,
                "parent_role_name": self.parent_role.name if self.parent_role else None,
            }
        )

        if include_permissions:
            data["permissions"] = [perm.name for perm in self.permissions]

        return data

    def get_all_permissions(self) -> set:
        """
        Get all permissions for this role, including inherited ones.

        Walks up the parent role chain and collects all permissions.

        Returns:
            set: Set of permission name strings

        Example:
            # If admin inherits from moderator:
            # moderator has: ["users:read", "users:update"]
            # admin has: ["users:create", "users:delete"]
            # admin.get_all_permissions() → {
            #     "users:read", "users:update",  # inherited
            #     "users:create", "users:delete"  # own
            # }
        """
        permissions = set()

        # Add this role's direct permissions
        for perm in self.permissions:
            permissions.add(perm.name)

        # Add inherited permissions from parent roles
        parent = self.parent_role
        while parent:
            for perm in parent.permissions:
                permissions.add(perm.name)
            parent = parent.parent_role

        return permissions

    def has_permission(self, permission_name: str) -> bool:
        """
        Check if this role has a specific permission (including inherited).

        Args:
            permission_name: Permission to check (e.g., "users:delete")

        Returns:
            bool: True if role has the permission
        """
        return permission_name in self.get_all_permissions()
