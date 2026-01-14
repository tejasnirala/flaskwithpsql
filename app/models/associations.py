"""
RBAC Association Tables (Junction Tables)
==========================================
Many-to-many relationship tables for the RBAC system.

These tables connect:
1. user_roles: Users ←→ Roles
2. role_permissions: Roles ←→ Permissions
3. user_permissions: Users ←→ Permissions (direct/extra permissions)

Why Separate Tables?
--------------------
In relational databases, many-to-many relationships require a "junction table"
(also called "bridge table" or "association table") to connect two entities.

Example: One user can have many roles, and one role can belong to many users.
         This is a many-to-many relationship.

   users                user_roles               roles
   ┌────┐              ┌───────────┐            ┌────┐
   │ id │──────────────│ user_id   │────────────│ id │
   │    │              │ role_id   │            │    │
   └────┘              │ metadata  │            └────┘
                       └───────────┘

Design Decisions:
-----------------
1. Using SQLAlchemy Table() instead of Model class
   - Junction tables typically don't need ORM features
   - Simpler and more lightweight
   - SQLAlchemy handles the relationship automatically

2. Including metadata columns (assigned_at, assigned_by)
   - Audit trail: who assigned what and when
   - Useful for compliance and debugging
   - Best practice in production systems

3. Stored in 'rbac' schema
   - Keeps all RBAC tables together
   - Clean separation from application data
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, Text

from app import db

# =============================================================================
# USER ←→ ROLES (Many-to-Many)
# =============================================================================
# Links users to their assigned roles
# One user can have multiple roles (e.g., both "moderator" and "support")
# One role can be assigned to multiple users

user_roles = Table(
    "user_roles",
    db.Model.metadata,
    # Composite primary key: (user_id, role_id)
    Column(
        "user_id",
        Integer,
        ForeignKey("users.users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="User who has this role",
    ),
    Column(
        "role_id",
        Integer,
        ForeignKey("rbac.roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Role assigned to the user",
    ),
    # Audit columns
    Column(
        "assigned_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When this role was assigned",
    ),
    Column(
        "assigned_by",
        Integer,
        ForeignKey("users.users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User ID of admin who assigned this role",
    ),
    # Schema placement
    schema="rbac",
)


# =============================================================================
# ROLE ←→ PERMISSIONS (Many-to-Many)
# =============================================================================
# Links roles to their permissions
# One role can have multiple permissions (e.g., admin has many permissions)
# One permission can belong to multiple roles (e.g., "users:read" on both admin and moderator)

role_permissions = Table(
    "role_permissions",
    db.Model.metadata,
    # Composite primary key: (role_id, permission_id)
    Column(
        "role_id",
        Integer,
        ForeignKey("rbac.roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Role that has this permission",
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("rbac.permissions.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Permission granted to the role",
    ),
    # Audit columns
    Column(
        "granted_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When this permission was granted to the role",
    ),
    # Schema placement
    schema="rbac",
)


# =============================================================================
# USER ←→ PERMISSIONS (Direct/Extra Permissions)
# =============================================================================
# Links users DIRECTLY to permissions (bypassing roles)
# Used for:
#   - Temporary extra permissions for specific users
#   - Exceptions that don't fit into role structure
#   - Testing features with specific users
#
# BEST PRACTICE: Use sparingly! Most permissions should come from roles.
# If many users need the same direct permission, create a new role instead.

user_permissions = Table(
    "user_permissions",
    db.Model.metadata,
    # Composite primary key: (user_id, permission_id)
    Column(
        "user_id",
        Integer,
        ForeignKey("users.users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="User who has this direct permission",
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("rbac.permissions.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Permission granted directly to the user",
    ),
    # Audit columns
    Column(
        "granted_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="When this permission was granted",
    ),
    Column(
        "granted_by",
        Integer,
        ForeignKey("users.users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User ID of admin who granted this permission",
    ),
    # Reason for granting (audit trail)
    Column(
        "reason",
        Text,
        nullable=True,
        comment="Reason for granting this direct permission (audit trail)",
    ),
    # Schema placement
    schema="rbac",
)
