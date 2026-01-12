# Standardized API Responses Guide

## Overview

This document explains the standardized API response system implemented in the Flask application. **Every API endpoint now returns responses following a consistent envelope format**, making the API predictable and frontend-friendly.

---

## Table of Contents

1. [What Changed?](#what-changed)
2. [Standard Response Envelope](#standard-response-envelope)
3. [Response Utilities](#response-utilities)
4. [Error Codes](#error-codes)
5. [Global Error Handlers](#global-error-handlers)
6. [Usage Examples](#usage-examples)
7. [Flow Diagrams](#flow-diagrams)
8. [OpenAPI Integration](#openapi-integration)
9. [Best Practices](#best-practices)

---

## What Changed?

### Before (Inconsistent Responses)

```python
# Different routes returned different formats
return jsonify({"success": True, "data": user}), 200
return jsonify({"error": "Not found"}), 404
return jsonify({"success": False, "error": "Invalid"}), 400
```

### After (Standardized Responses)

```python
# All routes now use centralized utilities
return success_response(data=user)
return error_response(code=ErrorCode.NOT_FOUND, message="User not found", status_code=404)
```

### Key Benefits

| Aspect             | Before          | After                  |
| ------------------ | --------------- | ---------------------- |
| Response Format    | Inconsistent    | Standardized envelope  |
| Error Structure    | Mixed formats   | Unified error object   |
| Metadata           | Ad-hoc          | Dedicated `meta` field |
| Error Codes        | String messages | Enum-based codes       |
| Exception Handling | Default Flask   | Custom global handlers |

---

## Standard Response Envelope

Every API response follows this structure:

```json
{
    "success": boolean,
    "data": object | array | null,
    "error": {
        "code": string,
        "message": string,
        "details"?: object
    } | null,
    "meta"?: object | null
}
```

### Field Descriptions

| Field           | Type                      | Description                            |
| --------------- | ------------------------- | -------------------------------------- |
| `success`       | `boolean`                 | `true` for success, `false` for errors |
| `data`          | `object \| array \| null` | Response payload (null on error)       |
| `error`         | `object \| null`          | Error details (null on success)        |
| `error.code`    | `string`                  | Machine-readable error code            |
| `error.message` | `string`                  | Human-readable error message           |
| `error.details` | `object` (optional)       | Field-level errors or additional info  |
| `meta`          | `object` (optional)       | Metadata like pagination, request_id   |

### Success Response Example

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  },
  "error": null,
  "meta": null
}
```

### Error Response Example

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "email": "Invalid email format",
      "password": "Must be at least 8 characters"
    }
  },
  "meta": null
}
```

### List Response with Metadata

```json
{
  "success": true,
  "data": [
    { "id": 1, "username": "user1" },
    { "id": 2, "username": "user2" }
  ],
  "error": null,
  "meta": {
    "count": 2,
    "page": 1,
    "per_page": 10,
    "total": 50
  }
}
```

---

## Response Utilities

### File Location

```
app/
├── utils/
│   ├── __init__.py          # Exports all utilities
│   ├── responses.py         # Response helper functions
│   └── error_handlers.py    # Global error handlers
```

### Importing Utilities

```python
from app.utils.responses import (
    success_response,
    error_response,
    ErrorCode,
    StandardSuccessResponse,
    StandardErrorResponse,
)
```

### `success_response()` Function

Creates a standardized success response.

```python
def success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = 200
) -> tuple[Response, int]:
```

#### Parameters

| Parameter     | Type   | Default | Description                     |
| ------------- | ------ | ------- | ------------------------------- |
| `data`        | `Any`  | `None`  | Response payload                |
| `message`     | `str`  | `None`  | Success message (added to data) |
| `meta`        | `dict` | `None`  | Metadata (pagination, etc.)     |
| `status_code` | `int`  | `200`   | HTTP status code                |

#### Examples

```python
# Simple success
return success_response(data={"id": 1, "name": "John"})

# With message (for creation)
return success_response(
    data=user.to_dict(),
    message="User created successfully",
    status_code=201
)

# List with pagination metadata
return success_response(
    data=users_list,
    meta={"page": 1, "per_page": 10, "total": 100}
)

# No data (just a message)
return success_response(message="User deleted successfully")
```

### `error_response()` Function

Creates a standardized error response.

```python
def error_response(
    code: Union[ErrorCode, str],
    message: str,
    details: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = 400
) -> tuple[Response, int]:
```

#### Parameters

| Parameter     | Type               | Default  | Description                 |
| ------------- | ------------------ | -------- | --------------------------- |
| `code`        | `ErrorCode \| str` | Required | Machine-readable error code |
| `message`     | `str`              | Required | Human-readable message      |
| `details`     | `dict`             | `None`   | Additional error details    |
| `meta`        | `dict`             | `None`   | Optional metadata           |
| `status_code` | `int`              | `400`    | HTTP status code            |

#### Examples

```python
# Simple error
return error_response(
    code=ErrorCode.NOT_FOUND,
    message="User not found",
    status_code=404
)

# Validation error with field details
return error_response(
    code=ErrorCode.VALIDATION_ERROR,
    message="Validation failed",
    details={
        "email": "Invalid email format",
        "password": "Must be at least 8 characters"
    },
    status_code=422
)

# Conflict error
return error_response(
    code=ErrorCode.RESOURCE_ALREADY_EXISTS,
    message="Username already exists",
    status_code=409
)
```

---

## Error Codes

The `ErrorCode` enum provides machine-readable error codes:

```python
from app.utils.responses import ErrorCode
```

### Available Codes

| Code                      | Description               | Typical HTTP Status |
| ------------------------- | ------------------------- | ------------------- |
| `INTERNAL_ERROR`          | Unhandled server error    | 500                 |
| `BAD_REQUEST`             | Malformed request         | 400                 |
| `NOT_FOUND`               | Resource not found        | 404                 |
| `METHOD_NOT_ALLOWED`      | Wrong HTTP method         | 405                 |
| `CONFLICT`                | Resource conflict          | 409                 |
| `VALIDATION_ERROR`        | Input validation failed   | 422                 |
| `INVALID_INPUT`           | Invalid input data        | 400                 |
| `MISSING_FIELD`           | Required field missing     | 400                 |
| `UNAUTHORIZED`            | Not authenticated         | 401                 |
| `FORBIDDEN`               | No permission             | 403                 |
| `INVALID_CREDENTIALS`     | Wrong username/password   | 401                 |
| `TOKEN_EXPIRED`           | Auth token expired        | 401                 |
| `TOKEN_INVALID`           | Auth token invalid        | 401                 |
| `RESOURCE_NOT_FOUND`      | Specific resource missing  | 404                 |
| `RESOURCE_ALREADY_EXISTS` | Duplicate resource        | 409                 |
| `DATABASE_ERROR`          | Database operation failed | 500                 |
| `RATE_LIMIT_EXCEEDED`     | Too many requests         | 429                 |

### Usage

```python
from app.utils.responses import ErrorCode, error_response

# Use enum values
return error_response(
    code=ErrorCode.RESOURCE_ALREADY_EXISTS,
    message="Email already registered",
    status_code=409
)
```

---

## Global Error Handlers

Global error handlers ensure that **all exceptions** return standardized responses, including:

- HTTP exceptions (404, 405, 500, etc.)
- Pydantic validation errors
- Unhandled exceptions

### Registered Handlers

| Error Type        | Handler                            | Description             |
| ----------------- | ---------------------------------- | ----------------------- |
| 400               | `handle_bad_request`               | Malformed requests      |
| 401               | `handle_unauthorized`              | Missing auth            |
| 403               | `handle_forbidden`                 | No permission           |
| 404               | `handle_not_found`                 | Resource not found      |
| 405               | `handle_method_not_allowed`        | Wrong HTTP method       |
| 409               | `handle_conflict`                   | Resource conflict        |
| 422               | `handle_unprocessable_entity`      | Validation error        |
| 429               | `handle_rate_limit`                | Rate limit exceeded     |
| 500               | `handle_internal_error`            | Server error            |
| `HTTPException`   | `handle_http_exception`            | All werkzeug exceptions |
| `ValidationError` | `handle_pydantic_validation_error` | Pydantic errors         |
| `Exception`       | `handle_generic_exception`         | Catch-all handler       |

### flask-openapi3 Validation Errors

flask-openapi3 has its own built-in Pydantic validation that runs before our route handlers are called. To make these validation errors conform to our standard format, we configure a custom `validation_error_callback` in the application factory:

```python
# In app/__init__.py

def validation_error_callback(error: ValidationError):
    """
    Custom callback for flask-openapi3 Pydantic validation errors.
    Returns a Response object with our standard error format.
    """
    # Transform Pydantic errors to our format
    details = {}
    for err in error.errors():
        loc = err.get("loc", ())
        field = ".".join(str(l) for l in loc if l != "body") or "unknown"
        message = err.get("msg", "Validation failed")
        details[field] = message

    response_body = {
        "success": False,
        "data": None,
        "error": {
            "code": ErrorCode.VALIDATION_ERROR.value,
            "message": "Validation failed",
            "details": details,
        },
        "meta": None,
    }

    return make_response(jsonify(response_body), 422)

# Pass to OpenAPI constructor
app = OpenAPI(
    __name__,
    info=info,
    validation_error_callback=validation_error_callback,
)
```

This ensures that when Pydantic validation fails (e.g., missing required field), the response looks like:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "password": "Field required",
      "email": "value is not a valid email address"
    }
  },
  "meta": null
}
```

### How Handlers Are Registered

In `app/__init__.py`:

```python
def create_app(config_name="default"):
    # ... other initialization ...

    # Register global error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)

    return app
```

### Example: 404 Handler

When a `get_or_404()` fails:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "The requested resource was not found"
  },
  "meta": null
}
```

### Example: Validation Error

When Pydantic validation fails:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "email": "String should have at least 5 characters",
      "password": "Field required"
    }
  },
  "meta": null
}
```

---

## Usage Examples

### Complete Route Example

```python
from flask_openapi3 import APIBlueprint
from pydantic import BaseModel, Field

from app import db
from app.models.user import User
from app.schemas import UserCreateSchema, UserResponseSchema
from app.utils.responses import (
    success_response,
    error_response,
    ErrorCode,
    StandardSuccessResponse,
    StandardErrorResponse,
)


users_bp = APIBlueprint("users", __name__, url_prefix="/api/users")


@users_bp.post(
    "/register",
    summary="Register New User",
    responses={
        201: StandardSuccessResponse,
        409: StandardErrorResponse,
        422: StandardErrorResponse,
    },
)
def register_user(body: UserCreateSchema):
    # Check for existing user
    if User.query.filter_by(username=body.username).first():
        return error_response(
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message="Username already exists",
            status_code=409
        )

    # Create user
    user = User(
        username=body.username,
        email=body.email,
        # ... other fields
    )
    db.session.add(user)
    db.session.commit()

    # Return success
    response_data = UserResponseSchema.model_validate(user)
    return success_response(
        data=response_data.to_dict(),
        message="User created successfully",
        status_code=201
    )
```

### Handling Different Scenarios

```python
@users_bp.get("/{user_id}")
def get_user(path: UserPath):
    # get_or_404 will trigger global 404 handler automatically
    user = User.query.get_or_404(path.user_id)

    return success_response(data=UserResponseSchema.model_validate(user).to_dict())


@users_bp.post("/login")
def login(body: LoginSchema):
    user = User.query.filter_by(email=body.email).first()

    if not user:
        return error_response(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="User not found",
            status_code=404
        )

    if not user.check_password(body.password):
        return error_response(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="Invalid password",
            status_code=401
        )

    return success_response(
        data={"user": user.to_dict(), "token": generate_token(user)},
        message="Login successful"
    )
```

---

## Flow Diagrams

### Success Response Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         HTTP Request                            │
│                    POST /api/users/register                     │
│                    {"username": "john", ...}                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    flask-openapi3 Validation                     │
│                  (Validates against Pydantic schema)            │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
            Valid ✓ │               Invalid ✗
                    │                       │
                    ▼                       ▼
    ┌───────────────────────┐  ┌───────────────────────────────┐
    │    Route Handler      │  │    Global Error Handler       │
    │                       │  │    (Pydantic Validation)      │
    │  1. Business logic    │  │                               │
    │  2. DB operations     │  │    Returns 422 with           │
    │  3. success_response()│  │    standardized error         │
    └───────────┬───────────┘  └───────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    success_response()                           │
│                                                                 │
│    1. Convert Pydantic model to dict (if needed)                │
│    2. Build envelope: {success, data, error, meta}              │
│    3. Return jsonify() with status code                         │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HTTP Response                              │
│                     201 Created                                 │
│    {                                                            │
│        "success": true,                                         │
│        "data": {"id": 1, "username": "john", ...},              │
│        "error": null,                                           │
│        "meta": null                                             │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         HTTP Request                            │
│                      GET /api/users/999                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Route Handler                             │
│                                                                 │
│    user = User.query.get_or_404(999)                            │
│    # User not found → raises 404 NotFound exception             │
└─────────────────────────────────────────────────────────────────┘
                                │
                    Exception raised!
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Global Error Handler                         │
│                    @app.errorhandler(404)                       │
│                                                                 │
│    def handle_not_found(error):                                 │
│        return error_response(                                   │
│            code=ErrorCode.NOT_FOUND,                            │
│            message="The requested resource was not found",      │
│            status_code=404                                      │
│        )                                                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      HTTP Response                              │
│                      404 Not Found                              │
│    {                                                            │
│        "success": false,                                        │
│        "data": null,                                            │
│        "error": {                                               │
│            "code": "NOT_FOUND",                                 │
│            "message": "The requested resource was not found"    │
│        },                                                       │
│        "meta": null                                             │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## OpenAPI Integration

### Response Schemas

The response schemas extend `StandardSuccessResponse` and `StandardErrorResponse` for proper OpenAPI documentation:

```python
from app.utils.responses import StandardSuccessResponse, StandardErrorResponse

class UserDataResponse(StandardSuccessResponse):
    """Success response containing user data."""
    data: Optional[Dict[str, Any]] = Field(
        ...,
        description="User data object"
    )

class UsersListResponse(StandardSuccessResponse):
    """Success response containing list of users."""
    data: Optional[List[Dict[str, Any]]] = Field(
        ...,
        description="List of user objects"
    )
```

### Route Definition

```python
@users_bp.get(
    "/<int:user_id>",
    summary="Get User by ID",
    description="Retrieves a specific user by their ID.",
    responses={
        200: UserDataResponse,
        404: StandardErrorResponse,
    },
)
def get_user(path: UserPath):
    user = User.query.get_or_404(path.user_id)
    return success_response(data=UserResponseSchema.model_validate(user).to_dict())
```

### Generated OpenAPI Spec

The above generates this in the OpenAPI spec:

```yaml
paths:
  /api/users/{user_id}:
    get:
      summary: Get User by ID
      responses:
        "200":
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/UserDataResponse"
        "404":
          description: Error Response
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/StandardErrorResponse"
```

---

## Best Practices

### DO ✓

1. **Always use `success_response()` and `error_response()`**

   ```python
   # ✓ Good
   return success_response(data=user.to_dict())

   # ✗ Bad
   return jsonify({"success": True, "data": user.to_dict()})
   ```

2. **Use `ErrorCode` enum for error codes**

   ```python
   # ✓ Good
   return error_response(code=ErrorCode.NOT_FOUND, message="User not found", status_code=404)

   # ✗ Bad
   return error_response(code="not_found", message="User not found", status_code=404)
   ```

3. **Include meaningful messages**

   ```python
   # ✓ Good
   return error_response(
       code=ErrorCode.VALIDATION_ERROR,
       message="Email already registered. Please use a different email.",
       status_code=409
   )

   # ✗ Bad
   return error_response(code=ErrorCode.VALIDATION_ERROR, message="Error", status_code=409)
   ```

4. **Use `meta` for pagination and metadata**

   ```python
   # ✓ Good
   return success_response(
       data=users,
       meta={"page": 1, "per_page": 10, "total": 100}
   )
   ```

5. **Use `get_or_404()` for resource lookup**
   ```python
   # ✓ Good - triggers global 404 handler
   user = User.query.get_or_404(user_id)
   ```

### DON'T ✗

1. **Don't return raw dictionaries**

   ```python
   # ✗ Bad
   return {"status": "ok"}
   ```

2. **Don't mix response formats**

   ```python
   # ✗ Bad
   if success:
       return jsonify(user.to_dict())
   else:
       return {"error": "Failed"}, 400
   ```

3. **Don't expose internal errors in production**

   ```python
   # ✗ Bad (in production)
   return error_response(
       code=ErrorCode.DATABASE_ERROR,
       message=str(database_exception),  # Exposes internal details!
       status_code=500
   )
   ```

4. **Don't forget the status code**

   ```python
   # ✗ Bad - defaults to 400 when you need 404
   return error_response(code=ErrorCode.NOT_FOUND, message="Not found")

   # ✓ Good
   return error_response(code=ErrorCode.NOT_FOUND, message="Not found", status_code=404)
   ```

---

## Directory Structure

After implementing standardized responses:

```
app/
├── __init__.py           # Application factory (registers error handlers)
├── utils/
│   ├── __init__.py       # Exports all utilities
│   ├── responses.py      # success_response(), error_response(), ErrorCode
│   └── error_handlers.py # Global error handlers
├── routes/
│   ├── main.py           # Uses success_response()
│   └── users.py          # Uses success_response(), error_response()
└── ...
```

---

## Summary

The standardized API response system provides:

1. **Consistency** - All endpoints return the same envelope format
2. **Predictability** - Frontend knows exactly what to expect
3. **Error Handling** - Unified error structure with machine-readable codes
4. **Documentation** - OpenAPI schemas match actual responses
5. **Maintainability** - Single point of change for response format
6. **Security** - Global handlers prevent leaking internal errors

This makes the API much more professional and easier to consume by frontend applications.
