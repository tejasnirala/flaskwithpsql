"""
Base Model Module
=================
This module provides a base model class that contains common fields
shared across all database models in the application.

All models should inherit from BaseModel to ensure consistency
and avoid code duplication.

Common Fields:
- id: Primary key (auto-increment integer)
- created_at: Timestamp when record was created
- updated_at: Timestamp when record was last updated
- is_deleted: Soft delete flag (boolean)
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer

from app import db


class BaseModel(db.Model):
    """
    Abstract base model class that provides common fields for all models.

    This class is marked as abstract, meaning SQLAlchemy will NOT create
    a separate table for it. It only serves as a parent class for other models.

    Attributes:
        id (int): Primary key, auto-incrementing integer
        created_at (datetime): UTC timestamp of when the record was created
        updated_at (datetime): UTC timestamp of when the record was last modified
        is_deleted (bool): Soft delete flag. True = record is "deleted" but still in DB

    Usage:
        class User(BaseModel):
            __tablename__ = 'users'
            username = db.Column(db.String(80), unique=True, nullable=False)
            # ... other fields
            # id, created_at, updated_at, is_deleted are automatically inherited

    Note:
        - This class uses `__abstract__ = True` to prevent table creation
        - All timestamps are stored in UTC for consistency
        - The `is_deleted` field enables soft deletes (data is never truly deleted)
    """

    # ========================================================================
    # ABSTRACT FLAG
    # ========================================================================
    # This tells SQLAlchemy: "Don't create a table for this class"
    # Only child classes that inherit from this will have tables created
    __abstract__ = True

    # ========================================================================
    # PRIMARY KEY
    # ========================================================================
    # Auto-incrementing integer primary key
    # PostgreSQL will use SERIAL type for this
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Unique identifier for the record",
    )

    # ========================================================================
    # TIMESTAMP FIELDS
    # ========================================================================
    # created_at: Set automatically when a new record is inserted
    # We use timezone.utc to ensure all timestamps are in UTC
    # This avoids timezone confusion when your app runs in different regions
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="UTC timestamp when this record was created",
    )

    # updated_at: Set automatically when record is inserted AND updated
    # - `default`: Sets the value when the record is first created
    # - `onupdate`: Automatically updates the value when the record is modified
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="UTC timestamp when this record was last updated",
    )

    # ========================================================================
    # SOFT DELETE FLAG
    # ========================================================================
    # Instead of actually deleting records (which loses data forever),
    # we set is_deleted=True. This is called "soft delete".
    #
    # Benefits of soft delete:
    # 1. Data recovery: Can "undelete" records if needed
    # 2. Audit trail: Keep history of all records
    # 3. Foreign key safety: No orphaned references
    # 4. Analytics: Can analyze even "deleted" data
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,  # Index for faster queries with WHERE is_deleted = False
        comment="Soft delete flag. True means record is logically deleted",
    )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def soft_delete(self):
        """
        Mark this record as deleted (soft delete).

        Instead of removing the record from the database, this sets
        is_deleted=True. The record remains in the database but is
        treated as "deleted" by the application.

        Usage:
            user = User.query.get(1)
            user.soft_delete()
            db.session.commit()
        """
        self.is_deleted = True

    def restore(self):
        """
        Restore a soft-deleted record.

        Sets is_deleted=False, making the record "active" again.

        Usage:
            user = User.query.get(1)
            user.restore()
            db.session.commit()
        """
        self.is_deleted = False

    def to_base_dict(self):
        """
        Convert base fields to a dictionary.

        This provides the common fields that all models share.
        Child models can call this and extend with their own fields.

        Returns:
            dict: Dictionary containing id, created_at, updated_at, is_deleted

        Usage in child class:
            def to_dict(self):
                data = self.to_base_dict()
                data.update({
                    'username': self.username,
                    'email': self.email
                })
                return data
        """
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.is_deleted,
        }

    def __repr__(self):
        """
        Default string representation.

        Child classes should override this for more meaningful output.
        """
        return f"<{self.__class__.__name__} id={self.id}>"
