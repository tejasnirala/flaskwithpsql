"""
Tests for User Service.

These tests verify the UserService business logic including:
- User creation
- User authentication
- User retrieval and listing
- User updates and deletion
- Error handling
"""

import pytest

from app.schemas.user import UserCreateSchema, UserUpdateSchema
from app.services.user_service import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
)


class TestUserServiceCreate:
    """Tests for user creation service."""

    def test_create_user_success(self, db):
        """Test successful user creation."""
        data = UserCreateSchema(
            username="serviceuser",
            email="service@example.com",
            password="SecurePass123!",
            first_name="Service",
            last_name="User",
        )

        user = UserService.create_user(data)

        assert user.id is not None
        assert user.username == "serviceuser"
        assert user.email == "service@example.com"
        assert user.check_password("SecurePass123!")

    def test_create_user_duplicate_username(self, db, sample_user):
        """Test creating user with duplicate username raises error."""
        data = UserCreateSchema(
            username="testuser",  # Same as sample_user
            email="different@example.com",
            password="SecurePass123!",
            first_name="Test",
        )

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            UserService.create_user(data)

        assert exc_info.value.field == "username"

    def test_create_user_duplicate_email(self, db, sample_user):
        """Test creating user with duplicate email raises error."""
        data = UserCreateSchema(
            username="differentuser",
            email="test@example.com",  # Same as sample_user
            password="SecurePass123!",
            first_name="Test",
        )

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            UserService.create_user(data)

        assert exc_info.value.field == "email"


class TestUserServiceAuthentication:
    """Tests for user authentication service."""

    def test_authenticate_success(self, db, sample_user):
        """Test successful authentication."""
        user = UserService.authenticate("test@example.com", "TestPassword123!")

        assert user.id == sample_user.id

    def test_authenticate_wrong_password(self, db, sample_user):
        """Test authentication with wrong password."""
        with pytest.raises(InvalidCredentialsError):
            UserService.authenticate("test@example.com", "WrongPassword!")

    def test_authenticate_user_not_found(self, db):
        """Test authentication with non-existent user."""
        with pytest.raises(UserNotFoundError):
            UserService.authenticate("nobody@example.com", "AnyPassword123!")


class TestUserServiceRead:
    """Tests for user retrieval services."""

    def test_get_by_id(self, db, sample_user):
        """Test getting user by ID."""
        user = UserService.get_by_id(sample_user.id)

        assert user.id == sample_user.id
        assert user.username == "testuser"

    def test_get_by_id_not_found(self, db):
        """Test getting non-existent user returns None."""
        user = UserService.get_by_id(99999)

        assert user is None

    def test_get_by_id_or_404(self, db, sample_user):
        """Test get_by_id_or_404 returns user."""
        user = UserService.get_by_id_or_404(sample_user.id)

        assert user.id == sample_user.id

    def test_get_by_id_or_404_raises(self, db):
        """Test get_by_id_or_404 raises for non-existent user."""
        with pytest.raises(UserNotFoundError):
            UserService.get_by_id_or_404(99999)

    def test_get_by_email(self, db, sample_user):
        """Test getting user by email."""
        user = UserService.get_by_email("test@example.com")

        assert user.id == sample_user.id

    def test_get_all_with_pagination(self, db, sample_users):
        """Test getting all users with pagination."""
        users, total = UserService.get_all(page=1, per_page=2)

        assert len(users) == 2
        assert total == 5

    def test_get_all_excludes_deleted(self, db, sample_user):
        """Test that soft-deleted users are excluded by default."""
        sample_user.soft_delete()
        db.session.commit()

        users, total = UserService.get_all()

        assert total == 0

    def test_get_all_includes_deleted(self, db, sample_user):
        """Test including soft-deleted users."""
        sample_user.soft_delete()
        db.session.commit()

        users, total = UserService.get_all(include_deleted=True)

        assert total == 1


class TestUserServiceUpdate:
    """Tests for user update service."""

    def test_update_user_success(self, db, sample_user):
        """Test successful user update."""
        data = UserUpdateSchema(first_name="Updated", bio="New bio")

        user = UserService.update_user(sample_user.id, data)

        assert user.first_name == "Updated"
        assert user.bio == "New bio"

    def test_update_user_not_found(self, db):
        """Test updating non-existent user."""
        data = UserUpdateSchema(first_name="Test")

        with pytest.raises(UserNotFoundError):
            UserService.update_user(99999, data)


class TestUserServiceDelete:
    """Tests for user deletion service."""

    def test_soft_delete(self, db, sample_user):
        """Test soft delete."""
        user = UserService.soft_delete(sample_user.id)

        assert user.is_deleted is True

    def test_soft_delete_not_found(self, db):
        """Test soft deleting non-existent user."""
        with pytest.raises(UserNotFoundError):
            UserService.soft_delete(99999)

    def test_restore(self, db, sample_user):
        """Test restoring soft-deleted user."""
        sample_user.soft_delete()
        db.session.commit()

        user = UserService.restore(sample_user.id)

        assert user.is_deleted is False

    def test_hard_delete(self, db, sample_user):
        """Test hard delete."""
        user_id = sample_user.id
        result = UserService.hard_delete(user_id)

        assert result is True
        assert UserService.get_by_id(user_id, include_deleted=True) is None
