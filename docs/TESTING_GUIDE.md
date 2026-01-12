# Testing Guide

## Overview

This guide explains the testing setup for the Flask application, including:

- Test structure and organization
- Pytest fixtures
- Running tests
- Writing new tests

## Test Structure

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Shared fixtures
├── test_models/
│   ├── __init__.py
│   └── test_user.py         # User model tests
├── test_routes/
│   ├── __init__.py
│   ├── test_main.py         # Health check tests
│   └── test_users.py        # User API tests
└── test_services/
    ├── __init__.py
    └── test_user_service.py # UserService tests
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_routes/test_users.py

# Run specific test class
pytest tests/test_routes/test_users.py::TestUserRegistration

# Run specific test
pytest tests/test_routes/test_users.py::TestUserRegistration::test_register_user_success

# Run with coverage report
pytest --cov=app --cov-report=html

# Run and show print statements
pytest -s

# Run failed tests only (after first run)
pytest --lf
```

## Fixtures

Fixtures are defined in `conftest.py` and automatically available in all tests.

### Available Fixtures

| Fixture        | Scope    | Description                              |
| -------------- | -------- | ---------------------------------------- |
| `app`          | session  | Flask application configured for testing |
| `db`           | function | Clean database for each test             |
| `client`       | function | Flask test client                        |
| `sample_user`  | function | A pre-created user                       |
| `sample_users` | function | List of 5 pre-created users              |

### Using Fixtures

```python
def test_something(client, sample_user):
    """Fixtures are passed as function parameters."""
    response = client.get(f'/api/users/{sample_user.id}')
    assert response.status_code == 200
```

### Fixture Details

#### `app` Fixture

```python
@pytest.fixture(scope="session")
def app():
    """Create Flask app configured for testing."""
    app = create_app("testing")
    with app.app_context():
        yield app
```

- Uses `TestingConfig` from `config.py`
- Created once per test session (fast)
- Uses separate test database

#### `db` Fixture

```python
@pytest.fixture(scope="function")
def db(app):
    """Create fresh database tables for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()
```

- Creates tables before each test
- Drops tables after each test
- Ensures test isolation

#### `client` Fixture

```python
@pytest.fixture(scope="function")
def client(app, db):
    """Flask test client for HTTP requests."""
    with app.test_client() as client:
        with app.app_context():
            yield client
```

- Makes HTTP requests to the app
- Returns response objects

#### `sample_user` Fixture

```python
@pytest.fixture(scope="function")
def sample_user(db) -> User:
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )
    user.set_password("TestPassword123!")
    db.session.add(user)
    db.session.commit()
    return user
```

## Writing Tests

### Model Tests

Test the ORM models directly:

```python
class TestUserModel:
    def test_create_user(self, db):
        """Test creating a user."""
        user = User(
            username="newuser",
            email="new@example.com",
            first_name="New",
        )
        user.set_password("SecurePass123!")

        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == "newuser"

    def test_password_hashing(self, db):
        """Test password is hashed."""
        user = User(username="test", email="t@t.com", first_name="T")
        user.set_password("MyPassword123!")

        assert user.password_hash != "MyPassword123!"
        assert user.password_hash.startswith("pbkdf2:")
```

### Service Tests

Test business logic without HTTP:

```python
class TestUserServiceCreate:
    def test_create_user_success(self, db):
        """Test successful user creation."""
        data = UserCreateSchema(
            username="serviceuser",
            email="service@example.com",
            password="SecurePass123!",
            first_name="Service",
        )

        user = UserService.create_user(data)

        assert user.id is not None
        assert user.username == "serviceuser"

    def test_create_user_duplicate_username(self, db, sample_user):
        """Test duplicate username raises error."""
        data = UserCreateSchema(
            username="testuser",  # Same as sample_user
            email="different@example.com",
            password="SecurePass123!",
            first_name="Test",
        )

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            UserService.create_user(data)

        assert exc_info.value.field == "username"
```

### Route Tests

Test HTTP endpoints:

```python
class TestUserRegistration:
    def test_register_user_success(self, client):
        """Test successful registration."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "SecurePass123!",
                "first_name": "New",
            },
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["username"] == "newuser"

    def test_register_user_validation_error(self, client):
        """Test validation errors return 422."""
        response = client.post(
            "/api/users/register",
            json={
                "username": "ab",  # Too short
                "email": "invalid",  # Invalid email
                "password": "weak",  # Too weak
                "first_name": "",  # Empty
            },
            content_type="application/json",
        )

        assert response.status_code == 422
        data = json.loads(response.data)
        assert data["error"]["code"] == "VALIDATION_ERROR"
```

## Test Patterns

### Testing Errors

```python
def test_user_not_found(self, client):
    """Test 404 for non-existent user."""
    response = client.get("/api/users/99999")

    assert response.status_code == 404
    data = json.loads(response.data)
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
```

### Testing with Exceptions

```python
def test_authenticate_wrong_password(self, db, sample_user):
    """Test authentication fails with wrong password."""
    with pytest.raises(InvalidCredentialsError):
        UserService.authenticate("test@example.com", "WrongPassword!")
```

### Testing Pagination

```python
def test_pagination(self, client, sample_users):
    """Test pagination works correctly."""
    response = client.get("/api/users/?page=1&per_page=2")

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data["data"]) == 2
    assert data["meta"]["total"] == 5
    assert data["meta"]["page"] == 1
    assert data["meta"]["total_pages"] == 3
```

## Configuration

### pytest.ini / pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = ["-v", "--tb=short"]
```

### Coverage Configuration

```toml
[tool.coverage.run]
source = ["app"]
branch = true
omit = ["app/__init__.py", "*/tests/*"]

[tool.coverage.report]
show_missing = true
```

## Best Practices

1. **One assertion per test** (when practical)
2. **Descriptive test names**: `test_register_user_with_duplicate_email_returns_409`
3. **Use fixtures** for common setup
4. **Test edge cases**: Empty input, max length, special characters
5. **Test error paths**: Not just happy paths
6. **Keep tests fast**: Avoid unnecessary database operations
7. **Independent tests**: Each test should work in isolation

## Debugging Tests

```bash
# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Enter debugger on failure
pytest --pdb

# Run with verbose output
pytest -vv
```
