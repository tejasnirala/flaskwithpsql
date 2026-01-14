"""
Permission Model
================
Represents a single permission in the RBAC system.

Permissions follow the format: {resource}:{action}
Examples:
    - users:read      → Can read user data
    - users:create    → Can create new users
    - users:delete    → Can delete users
    - roles:assign    → Can assign roles to users
    - *:*             → Super admin (all permissions)

Design Decisions:
-----------------
1. Permissions are stored in the database (not hardcoded constants)
   - Allows dynamic permission management
   - Can add/remove permissions without code changes
   - Easier to audit

2. Split into resource + action columns
   - Enables querying by resource ("all user permissions")
   - Enables querying by action ("all delete permissions")
   - Still stored as combined 'name' for easy checking

3. Stored in 'rbac' schema
   - Logical separation from user data
   - Clear ownership of RBAC tables
"""

from sqlalchemy import Column, Index, String, Text

from app.models.base import BaseModel


class Permission(BaseModel):
    """
    Permission model representing a single permission in the RBAC system.

    Inherits from BaseModel:
        - id (Integer, Primary Key)
        - created_at (DateTime)
        - updated_at (DateTime)
        - is_deleted (Boolean)

    Attributes:
        name: Full permission string (e.g., "users:delete")
        resource: Resource part (e.g., "users")
        action: Action part (e.g., "delete")
        description: Human-readable description of what this permission allows

    Example:
        permission = Permission(
            name="users:delete",
            resource="users",
            action="delete",
            description="Allows deleting user accounts (soft delete)"
        )
    """

    __tablename__ = "permissions"
    __table_args__ = (
        # Composite index for resource+action queries
        Index("ix_permissions_resource_action", "resource", "action"),
        {"schema": "rbac"},
    )

    # ========================================================================
    # PERMISSION IDENTIFICATION
    # ========================================================================
    # The full permission string in format "resource:action"
    # This is what gets checked in the code: @permission_required("users:delete")
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Full permission string (e.g., 'users:delete')",
    )

    # Split parts for easier querying
    # "users:delete" → resource="users", action="delete"
    resource = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Resource this permission applies to (e.g., 'users')",
    )

    action = Column(
        String(50),
        nullable=False,
        comment="Action allowed on the resource (e.g., 'delete')",
    )

    # ========================================================================
    # DESCRIPTION
    # ========================================================================
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of this permission",
    )

    # ========================================================================
    # METHODS
    # ========================================================================

    def __repr__(self) -> str:
        """String representation of the Permission."""
        return f"<Permission {self.name}>"

    def to_dict(self) -> dict:
        """
        Convert permission to dictionary.

        Returns:
            dict: Dictionary representation of the permission
        """
        data = self.to_base_dict()
        data.update(
            {
                "name": self.name,
                "resource": self.resource,
                "action": self.action,
                "description": self.description,
            }
        )
        return data

    @classmethod
    def create_permission(cls, resource: str, action: str, description: str = None):
        """
        Factory method to create a permission with proper name format.

        Args:
            resource: The resource (e.g., "users")
            action: The action (e.g., "delete")
            description: Optional description

        Returns:
            Permission: New permission instance

        Example:
            perm = Permission.create_permission("users", "delete", "Can delete users")
            # Creates: Permission(name="users:delete", resource="users", action="delete")
        """
        name = f"{resource}:{action}"
        return cls(
            name=name,
            resource=resource,
            action=action,
            description=description,
        )
