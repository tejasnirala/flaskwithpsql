"""
Models Package
==============
Import all models here for easy access.

Usage:
    from app.models import BaseModel, User
"""

from app.models.base import BaseModel
from app.models.user import User

__all__ = ["BaseModel", "User"]
