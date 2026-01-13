"""
User Model
==========
User model representing the users table in PostgreSQL.
Inherits from BaseModel to get common fields (id, created_at, updated_at, is_deleted).
"""

from sqlalchemy import Boolean, Column, String, Text

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
    # METHODS
    # ========================================================================

    def __repr__(self):
        """String representation of the User."""
        return f"<User {self.username}>"

    def to_dict(self):
        """
        Convert user object to dictionary.

        Uses to_base_dict() from BaseModel for common fields,
        then adds user-specific fields.

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

        return data

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
