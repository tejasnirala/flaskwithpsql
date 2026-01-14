"""
Models Package
==============
Import all models here for easy access.

Usage:
    from app.models import BaseModel, User, Role, Permission

RBAC Models:
    - Permission: Individual permissions (e.g., "users:delete")
    - Role: Groups of permissions that can be assigned to users
    - Association tables: Junction tables for many-to-many relationships
"""

# IMPORTANT: Import associations BEFORE models that use them
# This ensures the junction tables are created before relationships are defined
from app.models.associations import role_permissions, user_permissions, user_roles
from app.models.base import BaseModel
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User

__all__ = [
    # Base
    "BaseModel",
    # User
    "User",
    # RBAC Models
    "Permission",
    "Role",
    # Association Tables
    "user_roles",
    "role_permissions",
    "user_permissions",
]
