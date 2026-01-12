"""
Tests for User Model.

These tests verify the User model's functionality including:
- Password hashing and verification
- Soft delete functionality
- Serialization methods
"""

from app.models.user import User


class TestUserModel:
    """Test suite for User model."""

    def test_create_user(self, db):
        """Test creating a new user."""
        user = User(
            username="newuser",
            email="new@example.com",
            first_name="New",
            last_name="User",
        )
        user.set_password("SecurePass123!")

        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.is_deleted is False
        assert user.is_active is True

    def test_password_hashing(self, db):
        """Test that passwords are properly hashed."""
        user = User(
            username="passtest",
            email="pass@example.com",
            first_name="Pass",
        )
        password = "SecurePass123!"
        user.set_password(password)

        # Password should be hashed, not stored in plain text
        assert user.password_hash != password
        assert user.password_hash.startswith("pbkdf2:sha256:")

    def test_password_verification(self, sample_user):
        """Test password verification works correctly."""
        # Correct password should verify
        assert sample_user.check_password("TestPassword123!") is True

        # Wrong password should fail
        assert sample_user.check_password("WrongPassword123!") is False

    def test_soft_delete(self, sample_user, db):
        """Test soft delete functionality."""
        assert sample_user.is_deleted is False

        sample_user.soft_delete()
        db.session.commit()

        assert sample_user.is_deleted is True

    def test_restore(self, sample_user, db):
        """Test restore after soft delete."""
        sample_user.soft_delete()
        db.session.commit()
        assert sample_user.is_deleted is True

        sample_user.restore()
        db.session.commit()
        assert sample_user.is_deleted is False

    def test_to_dict(self, sample_user):
        """Test to_dict serialization."""
        user_dict = sample_user.to_dict()

        assert "id" in user_dict
        assert user_dict["username"] == "testuser"
        assert user_dict["email"] == "test@example.com"
        assert user_dict["first_name"] == "Test"
        # Password should NOT be in the dict
        assert "password_hash" not in user_dict
        assert "password" not in user_dict

    def test_timestamps(self, sample_user):
        """Test that timestamps are set."""
        assert sample_user.created_at is not None
        assert sample_user.updated_at is not None

    def test_repr(self, sample_user):
        """Test string representation."""
        assert repr(sample_user) == "<User testuser>"
