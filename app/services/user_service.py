"""
User Service - Business logic for user operations.

This service layer separates business logic from route handlers, making
the code more testable, maintainable, and reusable.

Why Use a Service Layer?
------------------------
1. **Separation of Concerns**: Routes handle HTTP, services handle business logic
2. **Testability**: Services can be unit tested without HTTP overhead
3. **Reusability**: Same logic can be used from CLI scripts, background jobs, etc.
4. **Single Responsibility**: Each layer has one job to do well

Usage:
    from app.services.user_service import UserService

    # In a route
    user = UserService.create_user(data)

    # In a CLI script
    user = UserService.get_by_email("test@example.com")
"""

import logging
from typing import List, Optional, Tuple

from app import db
from app.models.user import User
from app.schemas.user import UserCreateSchema, UserUpdateSchema

logger = logging.getLogger(__name__)


class UserServiceError(Exception):
    """Base exception for user service errors."""

    pass


class UserNotFoundError(UserServiceError):
    """Raised when a user is not found."""

    pass


class UserAlreadyExistsError(UserServiceError):
    """Raised when trying to create a user that already exists."""

    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"User with {field}='{value}' already exists")


class InvalidCredentialsError(UserServiceError):
    """Raised when login credentials are invalid."""

    pass


class UserService:
    """
    Service class for user-related business logic.

    All methods are static for simplicity. In a larger application,
    you might use dependency injection with instance methods.

    Transaction Management:
    ----------------------
    Methods that modify data commit their own transactions.
    If you need multiple operations in one transaction, use
    the lower-level methods with manual transaction control.
    """

    # =========================================================================
    # CREATE Operations
    # =========================================================================

    @staticmethod
    def create_user(data: UserCreateSchema) -> User:
        """
        Create a new user.

        Args:
            data: Validated user creation data

        Returns:
            The newly created User object

        Raises:
            UserAlreadyExistsError: If username or email already exists
        """
        logger.info(f"Creating user: {data.username}")

        # Check for existing username
        if User.query.filter_by(username=data.username, is_deleted=False).first():
            logger.warning(f"Username already exists: {data.username}")
            raise UserAlreadyExistsError("username", data.username)

        # Check for existing email
        if User.query.filter_by(email=data.email, is_deleted=False).first():
            logger.warning(f"Email already exists: {data.email}")
            raise UserAlreadyExistsError("email", data.email)

        # Create user
        user = User(
            username=data.username,
            email=data.email,
            first_name=data.first_name,
            middle_name=data.middle_name,
            last_name=data.last_name,
            bio=data.bio,
        )
        user.set_password(data.password)

        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f"User created successfully: id={user.id}")
            return user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create user: {e}")
            raise

    # =========================================================================
    # READ Operations
    # =========================================================================

    @staticmethod
    def get_by_id(user_id: int, include_deleted: bool = False) -> Optional[User]:
        """
        Get a user by ID.

        Args:
            user_id: The user's ID
            include_deleted: If True, include soft-deleted users

        Returns:
            User object or None if not found
        """
        query = User.query.filter_by(id=user_id)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.first()

    @staticmethod
    def get_by_id_or_404(user_id: int, include_deleted: bool = False) -> User:
        """
        Get a user by ID or raise 404.

        Args:
            user_id: The user's ID
            include_deleted: If True, include soft-deleted users

        Returns:
            User object

        Raises:
            UserNotFoundError: If user not found
        """
        user = UserService.get_by_id(user_id, include_deleted)
        if not user:
            raise UserNotFoundError(f"User with id={user_id} not found")
        return user

    @staticmethod
    def get_by_email(email: str, include_deleted: bool = False) -> Optional[User]:
        """
        Get a user by email.

        Args:
            email: The user's email address
            include_deleted: If True, include soft-deleted users

        Returns:
            User object or None if not found
        """
        query = User.query.filter_by(email=email)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.first()

    @staticmethod
    def get_by_username(username: str, include_deleted: bool = False) -> Optional[User]:
        """
        Get a user by username.

        Args:
            username: The user's username
            include_deleted: If True, include soft-deleted users

        Returns:
            User object or None if not found
        """
        query = User.query.filter_by(username=username)
        if not include_deleted:
            query = query.filter_by(is_deleted=False)
        return query.first()

    @staticmethod
    def get_all(
        include_deleted: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[User], int]:
        """
        Get all users with pagination.

        Args:
            include_deleted: If True, include soft-deleted users
            page: Page number (1-indexed)
            per_page: Number of users per page

        Returns:
            Tuple of (list of users, total count)
        """
        query = User.query
        if not include_deleted:
            query = query.filter_by(is_deleted=False)

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        users = query.order_by(User.id).offset((page - 1) * per_page).limit(per_page).all()

        return users, total

    # =========================================================================
    # AUTHENTICATION Operations
    # =========================================================================

    @staticmethod
    def authenticate(email: str, password: str) -> User:
        """
        Authenticate a user with email and password.

        Args:
            email: The user's email address
            password: The plain text password

        Returns:
            The authenticated User object

        Raises:
            UserNotFoundError: If user with email not found
            InvalidCredentialsError: If password is incorrect
        """
        logger.info("Authentication attempt")

        user = UserService.get_by_email(email)
        if not user:
            logger.warning("Authentication failed: user not found")
            raise UserNotFoundError("User not found")

        if not user.check_password(password):
            logger.warning(f"Authentication failed: invalid password for user_id={user.id}")
            raise InvalidCredentialsError("Invalid password")

        logger.info(f"User authenticated successfully: user_id={user.id}")
        return user

    # =========================================================================
    # UPDATE Operations
    # =========================================================================

    @staticmethod
    def update_user(user_id: int, data: UserUpdateSchema) -> User:
        """
        Update a user's profile.

        Args:
            user_id: The user's ID
            data: Validated update data

        Returns:
            The updated User object

        Raises:
            UserNotFoundError: If user not found
        """
        user = UserService.get_by_id_or_404(user_id)

        logger.info(f"Updating user: user_id={user_id}")

        # Get only fields that were set
        update_data = data.model_dump(exclude_unset=True)
        logger.debug(f"Fields being updated: {list(update_data.keys())}")

        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            db.session.commit()
            logger.info(f"User updated successfully: user_id={user_id}")
            return user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update user: {e}")
            raise

    # =========================================================================
    # DELETE Operations
    # =========================================================================

    @staticmethod
    def soft_delete(user_id: int) -> User:
        """
        Soft delete a user.

        Args:
            user_id: The user's ID

        Returns:
            The soft-deleted User object

        Raises:
            UserNotFoundError: If user not found
        """
        user = UserService.get_by_id_or_404(user_id)

        logger.info(f"Soft-deleting user: user_id={user_id}")

        user.soft_delete()

        try:
            db.session.commit()
            logger.info(f"User soft-deleted successfully: user_id={user_id}")
            return user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to soft-delete user: {e}")
            raise

    @staticmethod
    def restore(user_id: int) -> User:
        """
        Restore a soft-deleted user.

        Args:
            user_id: The user's ID

        Returns:
            The restored User object

        Raises:
            UserNotFoundError: If user not found
        """
        user = UserService.get_by_id(user_id, include_deleted=True)
        if not user:
            raise UserNotFoundError(f"User with id={user_id} not found")

        logger.info(f"Restoring user: user_id={user_id}")

        user.restore()

        try:
            db.session.commit()
            logger.info(f"User restored successfully: user_id={user_id}")
            return user
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to restore user: {e}")
            raise

    @staticmethod
    def hard_delete(user_id: int) -> bool:
        """
        Permanently delete a user (use with caution!).

        Args:
            user_id: The user's ID

        Returns:
            True if deleted successfully

        Raises:
            UserNotFoundError: If user not found
        """
        user = UserService.get_by_id(user_id, include_deleted=True)
        if not user:
            raise UserNotFoundError(f"User with id={user_id} not found")

        logger.warning(f"HARD DELETING user: user_id={user_id}")

        try:
            db.session.delete(user)
            db.session.commit()
            logger.info(f"User hard-deleted successfully: user_id={user_id}")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to hard-delete user: {e}")
            raise
