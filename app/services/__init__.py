"""
Services Package - Business logic layer.

This package contains service classes that encapsulate business logic,
separating it from the route handlers (controllers) and models (data layer).

Why Services?
-------------
1. Routes become thin - only handle HTTP concerns
2. Business logic becomes testable without HTTP
3. Logic can be reused across routes, CLI, background jobs
4. Easier to understand and maintain

Usage:
    from app.services import UserService

    # Create a user
    user = UserService.create_user(data)

    # Authenticate
    user = UserService.authenticate(email, password)
"""

from app.services.user_service import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserService,
    UserServiceError,
)

__all__ = [
    "UserService",
    "UserServiceError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "InvalidCredentialsError",
]
