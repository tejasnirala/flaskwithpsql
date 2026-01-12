# Services Layer Architecture

## Overview

The services layer is a crucial part of clean architecture that **separates business logic from HTTP handling (routes)**. This document explains the implementation and benefits.

## Why Services?

### The Problem (Before)

```python
# BAD: Business logic mixed with route handling
@users_bp.post("/register")
def register_user(body: UserCreateSchema):
    # Validation logic here
    if User.query.filter_by(username=body.username).first():
        return error_response(...)

    # Database operations here
    user = User(...)
    db.session.add(user)
    db.session.commit()

    return success_response(...)
```

**Problems with this approach:**

1. **Untestable**: Can't test business logic without HTTP
2. **Not reusable**: Can't use same logic from CLI or background jobs
3. **Hard to maintain**: Route handlers become bloated
4. **Tight coupling**: HTTP layer knows about database details

### The Solution (Services Layer)

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Request                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Route Handler (Thin)                          │
│  - Parse request                                                 │
│  - Call service                                                  │
│  - Return response                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer                                 │
│  - Business logic                                                │
│  - Transaction management                                        │
│  - Validation rules                                              │
│  - Error handling                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Model Layer (ORM)                             │
│  - Data access                                                   │
│  - Relationships                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation

### Directory Structure

```
app/
└── services/
    ├── __init__.py          # Exports all services and exceptions
    └── user_service.py      # User business logic
```

### UserService Class

```python
# app/services/user_service.py

class UserService:
    """Service class for user-related business logic."""

    @staticmethod
    def create_user(data: UserCreateSchema) -> User:
        """Create a new user with validation."""
        # Check uniqueness
        if User.query.filter_by(username=data.username).first():
            raise UserAlreadyExistsError("username", data.username)

        # Create user
        user = User(...)
        user.set_password(data.password)

        # Transaction management
        try:
            db.session.add(user)
            db.session.commit()
            return user
        except Exception:
            db.session.rollback()
            raise
```

### Custom Exceptions

```python
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
```

### Using Services in Routes

```python
# app/routes/users.py

@users_bp.post("/register")
def register_user(body: UserCreateSchema):
    """Thin route handler - delegates to service."""
    try:
        user = UserService.create_user(body)
        return success_response(data=user.to_dict(), status_code=201)
    except UserAlreadyExistsError as e:
        return error_response(
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message=f"{e.field.title()} already exists",
            status_code=409,
        )
```

## Service Methods

### CRUD Operations

| Method                      | Description                                |
| --------------------------- | ------------------------------------------ |
| `create_user(data)`         | Create a new user                          |
| `get_by_id(id)`             | Get user by ID (returns None if not found) |
| `get_by_id_or_404(id)`      | Get user by ID (raises UserNotFoundError)  |
| `get_by_email(email)`       | Get user by email                          |
| `get_by_username(username)` | Get user by username                       |
| `get_all(page, per_page)`   | Get paginated list of users                |
| `update_user(id, data)`     | Update user profile                        |
| `soft_delete(id)`           | Soft delete user                           |
| `restore(id)`               | Restore soft-deleted user                  |
| `hard_delete(id)`           | Permanently delete user                    |

### Authentication

| Method                          | Description                        |
| ------------------------------- | ---------------------------------- |
| `authenticate(email, password)` | Verify credentials and return user |

## Benefits

### 1. Testability

```python
# Can test service directly without HTTP
def test_create_user(db):
    data = UserCreateSchema(...)
    user = UserService.create_user(data)
    assert user.id is not None
```

### 2. Reusability

```python
# Use from CLI
def cli_create_admin():
    data = UserCreateSchema(...)
    UserService.create_user(data)

# Use from background job
def job_send_welcome_email():
    user = UserService.get_by_id(user_id)
    send_email(user.email)
```

### 3. Transaction Safety

```python
# Service handles rollback on failure
try:
    db.session.add(user)
    db.session.commit()
except Exception:
    db.session.rollback()  # Always rollback on error
    raise
```

### 4. Soft Delete Support

```python
# Services enforce soft delete by default
users, total = UserService.get_all()  # Excludes deleted

# Explicitly include deleted
users, total = UserService.get_all(include_deleted=True)
```

## Best Practices

1. **Keep routes thin**: Only HTTP concerns (parsing, responding)
2. **Handle all business logic in services**: Validation, calculations, rules
3. **Use custom exceptions**: Clear error types for different failures
4. **Always manage transactions**: Commit on success, rollback on failure
5. **Log at appropriate levels**: INFO for success, WARNING for failures
6. **Keep services focused**: One service per domain entity

## Next Steps

Future enhancements could include:

- Caching layer (Redis)
- Event publishing (for microservices)
- Distributed transactions
- Rate limiting integration
