"""
Pytest Configuration and Fixtures.

This file is automatically loaded by pytest and provides fixtures
that can be used across all test files.

Fixtures Provided:
-----------------
- app: Flask application configured for testing
- client: Flask test client for making HTTP requests
- db: Database session for direct database access
- sample_user: A pre-created user for testing

Usage:
    def test_something(client, sample_user):
        response = client.get(f'/api/users/{sample_user.id}')
        assert response.status_code == 200
"""

from typing import Generator

import pytest

from app import create_app
from app import db as _db
from app.models.user import User


@pytest.fixture(scope="session")
def app():
    """
    Create and configure a Flask application for testing.

    Scope is 'session' so the app is created once per test session.
    """
    app = create_app("testing")

    # Establish application context
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def db(app) -> Generator:
    """
    Create database tables for each test function.

    This ensures each test starts with a clean database.
    Tables are created before the test and dropped after.
    """
    with app.app_context():
        # Create all tables
        _db.create_all()

        yield _db

        # Cleanup: remove session and drop all tables
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    """
    Flask test client for making HTTP requests.

    Each test gets a fresh client with a clean database.
    """
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope="function")
def sample_user(db) -> User:
    """
    Create a sample user for testing.

    Returns a User object that has been committed to the database.
    """
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        bio="A test user for testing purposes",
    )
    user.set_password("TestPassword123!")

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture(scope="function")
def sample_users(db) -> list:
    """
    Create multiple sample users for testing list operations.

    Returns a list of User objects.
    """
    users = []
    for i in range(5):
        user = User(
            username=f"testuser{i}",
            email=f"test{i}@example.com",
            first_name=f"Test{i}",
            last_name="User",
        )
        user.set_password("TestPassword123!")
        db.session.add(user)
        users.append(user)

    db.session.commit()
    return users


@pytest.fixture
def auth_headers():
    """
    Return authorization headers for authenticated requests.

    Note: Implement actual token generation when authentication is added.
    """
    return {"Authorization": "Bearer test-token"}
