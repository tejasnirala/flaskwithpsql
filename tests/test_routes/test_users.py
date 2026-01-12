"""
Tests for User Routes.

These tests verify the user API endpoints including:
- User registration
- User login
- CRUD operations
- Error handling
"""

import json


class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_register_user_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "first_name": "New",
                "last_name": "User",
            },
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["username"] == "newuser"
        assert data["data"]["email"] == "newuser@example.com"
        # Password should never be returned
        assert "password" not in data["data"]
        assert "password_hash" not in data["data"]

    def test_register_user_duplicate_username(self, client, sample_user):
        """Test registration with duplicate username fails."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "testuser",  # Same as sample_user
                "email": "different@example.com",
                "password": "SecurePass123!",
                "first_name": "Test",
            },
            content_type="application/json",
        )

        assert response.status_code == 409
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_ALREADY_EXISTS"

    def test_register_user_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "differentuser",
                "email": "test@example.com",  # Same as sample_user
                "password": "SecurePass123!",
                "first_name": "Test",
            },
            content_type="application/json",
        )

        assert response.status_code == 409
        data = json.loads(response.data)
        assert data["success"] is False

    def test_register_user_validation_errors(self, client):
        """Test registration validation errors."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "ab",  # Too short (min 3)
                "email": "invalid-email",  # Invalid format
                "password": "weak",  # Too weak
                "first_name": "",  # Empty
            },
            content_type="application/json",
        )

        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"


class TestUserLogin:
    """Tests for user login endpoint."""

    def test_login_success(self, client, sample_user):
        """Test successful login."""
        response = client.post(
            "/api/users/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"

    def test_login_invalid_password(self, client, sample_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/users/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!",
            },
            content_type="application/json",
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    def test_login_user_not_found(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/api/users/login",
            json={
                "email": "nobody@example.com",
                "password": "SomePass123!",
            },
            content_type="application/json",
        )

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False


class TestGetUsers:
    """Tests for GET /api/users endpoints."""

    def test_get_all_users(self, client, sample_users):
        """Test getting all users."""
        response = client.get("/api/users/")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert len(data["data"]) == 5
        assert data["meta"]["total"] == 5

    def test_get_all_users_pagination(self, client, sample_users):
        """Test pagination."""
        response = client.get("/api/users/?page=1&per_page=2")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["data"]) == 2
        assert data["meta"]["total"] == 5
        assert data["meta"]["page"] == 1
        assert data["meta"]["per_page"] == 2
        assert data["meta"]["total_pages"] == 3

    def test_get_single_user(self, client, sample_user):
        """Test getting a single user by ID."""
        response = client.get(f"/api/users/{sample_user.id}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"

    def test_get_user_not_found(self, client):
        """Test getting non-existent user."""
        response = client.get("/api/users/99999")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["success"] is False


class TestUpdateUser:
    """Tests for PUT /api/users/<id> endpoint."""

    def test_update_user_success(self, client, sample_user):
        """Test successful user update."""
        response = client.put(
            f"/api/users/{sample_user.id}",
            json={
                "first_name": "Updated",
                "bio": "Updated bio",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["first_name"] == "Updated"
        assert data["data"]["bio"] == "Updated bio"

    def test_update_user_not_found(self, client):
        """Test updating non-existent user."""
        response = client.put(
            "/api/users/99999",
            json={"first_name": "Test"},
            content_type="application/json",
        )

        assert response.status_code == 404


class TestDeleteUser:
    """Tests for DELETE /api/users/<id> endpoint."""

    def test_soft_delete_user(self, client, sample_user, db):
        """Test soft deleting a user."""
        response = client.delete(f"/api/users/{sample_user.id}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

        # Verify user is soft-deleted
        db.session.refresh(sample_user)
        assert sample_user.is_deleted is True

    def test_delete_user_not_found(self, client):
        """Test deleting non-existent user."""
        response = client.delete("/api/users/99999")

        assert response.status_code == 404
