# Pydantic Input Validation - Complete Guide

This document explains how Pydantic is set up and configured in this Flask application for input validation. It covers the conceptual understanding, implementation details, and usage patterns.

---

## Table of Contents

1. [What is Pydantic?](#what-is-pydantic)
2. [Why Pydantic for Flask?](#why-pydantic-for-flask)
3. [Pydantic vs Zod/Joi (Node.js Comparison)](#pydantic-vs-zodjoi-nodejs-comparison)
4. [Project Structure](#project-structure)
5. [Installation & Setup](#installation--setup)
6. [Core Concepts](#core-concepts)
7. [Schema Implementation](#schema-implementation)
8. [Flask Integration](#flask-integration)
9. [Usage Patterns](#usage-patterns)
10. [Request/Response Flow](#requestresponse-flow)
11. [Best Practices](#best-practices)

---

## What is Pydantic?

**Pydantic** is a Python library for data validation using Python type annotations. It leverages Python's type hints to:

- **Validate** incoming data against expected types and constraints
- **Parse/Coerce** data to the correct types
- **Serialize** Python objects to JSON-friendly formats
- **Document** your data structures (self-documenting code)

### Key Features

```
┌─────────────────────────────────────────────────────────────────┐
│                         PYDANTIC                                │
├─────────────────────────────────────────────────────────────────┤
│  ✓ Type Validation      - Ensures data matches expected types   │
│  ✓ Data Coercion        - "123" → 123 (string to int)          │
│  ✓ Custom Validators    - @field_validator, @model_validator   │
│  ✓ Error Messages       - Detailed, structured error info      │
│  ✓ JSON Schema          - Auto-generates OpenAPI schemas       │
│  ✓ Performance          - Pydantic v2 uses Rust (fast!)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Why Pydantic for Flask?

### The Problem Without Validation

```python
# ❌ Without Pydantic - Manual, error-prone validation
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()

    if not data:
        return {'error': 'No data'}, 400

    if 'email' not in data:
        return {'error': 'Email required'}, 400

    if not isinstance(data['email'], str):
        return {'error': 'Email must be string'}, 400

    if '@' not in data['email']:
        return {'error': 'Invalid email'}, 400

    # ... 50 more lines of validation
```

### The Solution With Pydantic

```python
# ✅ With Pydantic - Clean, declarative validation
from pydantic import EmailStr

class UserCreateSchema(BaseSchema):
    email: EmailStr  # Automatically validates email format!
    username: str = Field(min_length=3)

@app.route('/users', methods=['POST'])
@validate_with_schema(UserCreateSchema)
def create_user(validated_data):
    # validated_data is guaranteed to be valid!
    user = User(email=validated_data.email, ...)
```

---

## Pydantic vs Zod/Joi (Node.js Comparison)

Since you're coming from MERN/Next.js, here's how Pydantic compares:

### Conceptual Mapping

| Concept            | Node.js (Zod/Joi)                       | Python (Pydantic)                                 |
| ------------------ | --------------------------------------- | ------------------------------------------------- |
| Schema Definition   | `z.object({...})` / `Joi.object({...})` | `class MySchema(BaseModel)`                       |
| Required Field     | `z.string()`                            | `field: str`                                      |
| Optional Field     | `z.string().optional()`                 | `field: Optional[str] = None`                     |
| String Constraints | `z.string().min(3).max(50)`             | `field: str = Field(min_length=3, max_length=50)` |
| Email Validation   | `z.string().email()`                    | `field: EmailStr`                                 |
| Custom Transform   | `.transform(v => v.toLowerCase())`      | `@field_validator`                                |
| Parse & Validate   | `schema.parse(data)`                    | `Schema(**data)` or `Schema.model_validate(data)` |
| Safe Parse         | `schema.safeParse(data)`                | `try/except ValidationError`                      |

### Code Comparison

```javascript
// Zod (Node.js)
const UserSchema = z.object({
  username: z.string().min(3).max(80),
  email: z.string().email(),
  password: z.string().min(8),
  firstName: z.string().optional(),
});

const result = UserSchema.safeParse(req.body);
if (!result.success) {
  return res.status(400).json(result.error);
}
```

```python
# Pydantic (Python)
class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: Optional[str] = None

try:
    validated = UserSchema(**request.get_json())
except ValidationError as e:
    return jsonify(e.errors()), 400
```

---

## Project Structure

```
app/
├── __init__.py              # Flask app factory
├── models/                  # SQLAlchemy models (database)
│   ├── __init__.py
│   └── user.py             # User database model
├── routes/                  # API endpoints
│   ├── __init__.py
│   └── users.py            # User routes (uses schemas)
└── schemas/                 # Pydantic validation schemas
    ├── __init__.py         # Package exports
    ├── base.py             # Base schema configuration
    ├── user.py             # User validation schemas
    └── utils.py            # Validation utilities
```

### Why Separate `models/` and `schemas/`?

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEPARATION OF CONCERNS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   models/user.py (SQLAlchemy)      schemas/user.py (Pydantic)  │
│   ═══════════════════════════      ══════════════════════════  │
│                                                                  │
│   Represents DATABASE table         Validates API INPUT/OUTPUT  │
│   - Column definitions              - Field constraints         │
│   - Relationships                   - Custom validators         │
│   - Database queries                - Type coercion             │
│   - Persistence logic               - API documentation         │
│                                                                  │
│   Used for: STORING data            Used for: VALIDATING data  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**They serve different purposes:**

- **Models** define how data is stored in the database
- **Schemas** define how data is validated when entering/leaving the API

---

## Installation & Setup

### 1. Install Dependencies

```bash
# Via requirements.txt
pip install pydantic==2.5.3 email-validator==2.1.0

# Or directly
pip install pydantic email-validator
```

### 2. What Each Package Does

| Package           | Purpose                                             |
| ----------------- | --------------------------------------------------- |
| `pydantic`        | Core validation library                             |
| `email-validator` | Enables `EmailStr` type for proper email validation |

---

## Core Concepts

### 1. BaseModel

The foundation of Pydantic. All schemas inherit from `BaseModel`:

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# Creating an instance validates the data
user = User(name="John", age=30)  # ✅ Valid
user = User(name="John", age="thirty")  # ❌ ValidationError
```

### 2. Field()

Adds constraints and metadata to fields:

```python
from pydantic import Field

class User(BaseModel):
    username: str = Field(
        min_length=3,        # Minimum string length
        max_length=80,       # Maximum string length
        pattern=r'^[a-z]+$', # Regex pattern
        description="Username for login",
        examples=["john_doe"]
    )
```

### 3. Type Annotations

Pydantic uses Python's type hints:

```python
from typing import Optional
from pydantic import EmailStr

class User(BaseModel):
    # Required fields (no default value)
    email: EmailStr

    # Optional fields (default to None)
    bio: Optional[str] = None

    # With default value
    is_active: bool = True
```

### 4. Validators

Custom validation logic:

```python
from pydantic import field_validator, model_validator

class User(BaseModel):
    username: str
    password: str
    confirm_password: str

    # Validate single field
    @field_validator('username')
    @classmethod
    def username_lowercase(cls, v):
        return v.lower()

    # Validate multiple fields together
    @model_validator(mode='after')
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords must match')
        return self
```

---

## Schema Implementation

### Base Schema (`app/schemas/base.py`)

```python
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """Base schema with common configuration for all schemas."""

    model_config = ConfigDict(
        str_strip_whitespace=True,  # "  john  " → "john"
        extra='ignore',              # Ignore unknown fields
        from_attributes=True,        # Allow ORM → Schema conversion
    )
```

**Configuration Explained:**

| Option                 | What it Does                            | Why We Use It                       |
| ---------------------- | --------------------------------------- | ----------------------------------- |
| `str_strip_whitespace` | Removes leading/trailing whitespace     | Prevents " john " usernames         |
| `extra='ignore'`       | Ignores extra fields in input           | Lenient input, strict processing    |
| `from_attributes=True` | Allows `Schema.model_validate(orm_obj)` | Easy SQLAlchemy → Schema conversion |

### User Schemas (`app/schemas/user.py`)

We create **separate schemas for each operation**:

```
UserCreateSchema   → POST /users/register (create new user)
UserLoginSchema    → POST /users/login (authenticate)
UserUpdateSchema   → PUT /users/:id (update profile)
UserResponseSchema → All responses (control API output)
```

**Why separate schemas?**

```
┌─────────────────────────────────────────────────────────────┐
│                CREATE vs UPDATE vs RESPONSE                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CREATE (UserCreateSchema)                                   │
│  - username: required ✓                                     │
│  - password: required ✓                                     │
│  - email: required ✓                                        │
│                                                              │
│  UPDATE (UserUpdateSchema)                                   │
│  - username: cannot change ✗                                │
│  - password: not in this endpoint ✗                         │
│  - bio: optional ✓                                          │
│                                                              │
│  RESPONSE (UserResponseSchema)                               │
│  - password: NEVER exposed ✗                                │
│  - created_at: included ✓                                   │
│  - id: included ✓                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Flask Integration

### The Integration Challenge

Pydantic doesn't know about Flask's `request` object. We need to:

1. Get JSON from Flask's request
2. Pass it to Pydantic for validation
3. Handle validation errors → return proper HTTP responses
4. On success → pass validated data to route handler

### Our Solution: `utils.py`

We provide two approaches:

#### Approach 1: Manual Validation

```python
from app.schemas import validate_request, UserCreateSchema

@app.route('/users', methods=['POST'])
def create_user():
    result = validate_request(UserCreateSchema)

    if isinstance(result, tuple):
        # Validation failed, result is (response, status_code)
        return result

    # Validation passed, result is the schema instance
    validated_data = result
    # Use validated_data.username, validated_data.email, etc.
```

#### Approach 2: Decorator (Recommended)

```python
from app.schemas import validate_with_schema, UserCreateSchema

@app.route('/users', methods=['POST'])
@validate_with_schema(UserCreateSchema)
def create_user(validated_data: UserCreateSchema):
    # validated_data is guaranteed to be valid!
    # Validation errors are automatically handled
    user = User(username=validated_data.username, ...)
```

### How the Decorator Works

```
Request Flow with @validate_with_schema
═══════════════════════════════════════

┌──────────────┐
│ HTTP Request │
│ POST /users  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ @validate_with_schema(UserCreateSchema)               │
│                                                       │
│  1. Get JSON from request.get_json()                 │
│  2. Try to create UserCreateSchema(**json_data)      │
│  3. If ValidationError:                               │
│     └── Return 422 error with formatted errors       │
│  4. If success:                                       │
│     └── Call create_user(validated_schema_instance)  │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│ def create_user(validated_data):                      │
│     # validated_data is a UserCreateSchema instance  │
│     # All fields are validated and transformed!      │
│     user = User(username=validated_data.username)    │
└──────────────────────────────────────────────────────┘
```

---

## Usage Patterns

### Pattern 1: Validating Input

```python
from app.schemas import UserCreateSchema, validate_with_schema

@users_bp.route('/register', methods=['POST'])
@validate_with_schema(UserCreateSchema)
def register_user(validated_data: UserCreateSchema):
    """
    After decorator runs, validated_data contains:
    - username: cleaned lowercase string
    - email: valid email format
    - password: meets strength requirements
    - first_name: title-cased
    - etc.
    """
    user = User(
        username=validated_data.username,
        email=validated_data.email,
        # ...
    )
```

### Pattern 2: Formatting Output

```python
from app.schemas import UserResponseSchema

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id: int):
    user = User.query.get_or_404(user_id)

    # Convert SQLAlchemy model to response schema
    response_data = UserResponseSchema.model_validate(user)

    return jsonify({
        'success': True,
        'data': response_data.to_dict()
    })
```

### Pattern 3: Partial Updates

```python
from app.schemas import UserUpdateSchema

@users_bp.route('/<int:user_id>', methods=['PUT'])
@validate_with_schema(UserUpdateSchema)
def update_user(validated_data: UserUpdateSchema, user_id: int):
    user = User.query.get_or_404(user_id)

    # Only get fields that were explicitly provided
    update_data = validated_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.session.commit()
```

---

## Request/Response Flow

### Complete Request Lifecycle

```
                           REQUEST LIFECYCLE
═══════════════════════════════════════════════════════════════════

       ┌─────────────────────────────────────────────────────────┐
       │                                                          │
       │   1. CLIENT SENDS REQUEST                                │
       │      POST /api/users/register                            │
       │      Body: {"username": "  JOHN_DOE  ", "email": "..."}  │
       │                                                          │
       └──────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
       ┌─────────────────────────────────────────────────────────┐
       │                                                          │
       │   2. FLASK RECEIVES REQUEST                              │
       │      Routes to register_user()                           │
       │      Decorator intercepts first                          │
       │                                                          │
       └──────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
       ┌─────────────────────────────────────────────────────────┐
       │                                                          │
       │   3. PYDANTIC VALIDATION                                 │
       │      @validate_with_schema(UserCreateSchema)             │
       │                                                          │
       │      a. Parse JSON from request                          │
       │      b. Create UserCreateSchema instance                 │
       │      c. Run field validators:                            │
       │         - Strip whitespace: "  JOHN_DOE  " → "JOHN_DOE" │
       │         - Lowercase: "JOHN_DOE" → "john_doe"            │
       │         - Validate email format                          │
       │         - Check password strength                        │
       │      d. If any fail → Return 422 with error details     │
       │      e. If all pass → Continue with validated data      │
       │                                                          │
       └──────────────────────────┬───────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              VALIDATION OK              VALIDATION FAILED
                    │                           │
                    ▼                           ▼
       ┌───────────────────────┐    ┌─────────────────────────────┐
       │                       │    │                              │
       │  4a. ROUTE HANDLER    │    │  4b. ERROR RESPONSE          │
       │  register_user()      │    │  HTTP 422                    │
       │                       │    │  {                           │
       │  - Check uniqueness   │    │    "success": false,         │
       │  - Create User        │    │    "error": "Validation...", │
       │  - Save to DB         │    │    "details": [              │
       │  - Return 201         │    │      {"field": "email"...}   │
       │                       │    │    ]                         │
       │                       │    │  }                           │
       └───────────────────────┘    └─────────────────────────────┘
```

### Validation Error Response Example

```json
{
  "success": false,
  "error": "Validation failed",
  "message": "One or more fields failed validation",
  "details": [
    {
      "field": "username",
      "message": "String should have at least 3 characters",
      "type": "string_too_short"
    },
    {
      "field": "email",
      "message": "value is not a valid email address",
      "type": "value_error"
    },
    {
      "field": "password",
      "message": "Password must contain at least one uppercase letter",
      "type": "value_error"
    }
  ]
}
```

---

## Best Practices

### 1. One Schema Per Operation

```python
# ✅ Good - Clear intent, specific validation
class UserCreateSchema(BaseSchema): ...
class UserUpdateSchema(BaseSchema): ...
class UserLoginSchema(BaseSchema): ...

# ❌ Bad - Confusing, complex conditional logic
class UserSchema(BaseSchema):
    # Is this for create? update? login?
```

### 2. Never Expose Passwords

```python
# ✅ Good - Response schema excludes password
class UserResponseSchema(BaseSchema):
    id: int
    username: str
    email: EmailStr
    # NO password_hash here!

# ❌ Bad - Directly returning model
return jsonify(user.to_dict())  # Might include password!
```

### 3. Use Descriptive Field Names and Descriptions

```python
username: str = Field(
    ...,
    min_length=3,
    max_length=80,
    description="Unique username for login (3-80 characters)",
    examples=["john_doe", "user123"]
)
```

### 4. Validate Business Logic in Routes, Not Schemas

```python
# Schema validates DATA FORMAT
class UserCreateSchema(BaseSchema):
    email: EmailStr  # Validates it's a valid email format

# Route validates BUSINESS RULES
@validate_with_schema(UserCreateSchema)
def create_user(validated_data):
    # Check if email already exists in database
    if User.query.filter_by(email=validated_data.email).first():
        return jsonify({'error': 'Email already exists'}), 409
```

### 5. Reuse Common Validators

```python
# Define once in base.py or a validators.py
def normalize_name(v: str) -> str:
    if v is None:
        return v
    return v.strip().title()

# Use in multiple schemas
class UserCreateSchema(BaseSchema):
    @field_validator('first_name', 'last_name')
    @classmethod
    def name_validator(cls, v):
        return normalize_name(v)
```

---

## Quick Reference

### Common Field Types

| Type            | Description     | Example               |
| --------------- | --------------- | --------------------- |
| `str`           | String          | `"hello"`             |
| `int`           | Integer         | `42`                  |
| `float`         | Float           | `3.14`                |
| `bool`          | Boolean         | `True`                |
| `EmailStr`      | Valid email     | `"user@example.com"`  |
| `Optional[str]` | String or None  | `"hello"` or `None`   |
| `list[str]`     | List of strings | `["a", "b"]`          |
| `datetime`      | DateTime object | `2024-01-01T00:00:00` |

### Common Field Constraints

| Constraint   | For Type  | Description               |
| ------------ | --------- | ------------------------- |
| `min_length` | str       | Minimum string length     |
| `max_length` | str       | Maximum string length     |
| `pattern`    | str       | Regex pattern             |
| `ge`         | int/float | Greater than or equal (≥) |
| `le`         | int/float | Less than or equal (≤)    |
| `gt`         | int/float | Greater than (>)          |
| `lt`         | int/float | Less than (<)             |

### Validator Modes

| Mode            | When It Runs         | Use Case                     |
| --------------- | -------------------- | ---------------------------- |
| `mode='before'` | Before type coercion | Pre-processing raw input     |
| `mode='after'`  | After type coercion  | Post-processing typed values |
| `mode='wrap'`   | Wraps both           | Custom parsing logic         |

---

## Next Steps

1. **Add more schemas** as you add new models (e.g., `ProductSchema`, `OrderSchema`)
2. **Explore nested schemas** for complex data structures
3. **Look into OpenAPI integration** for automatic API documentation
4. **Consider `pydantic-settings`** for environment variable validation

---

_Last Updated: 2026-01-11_
