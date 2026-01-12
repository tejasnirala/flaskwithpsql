# Flask-OpenAPI3 Integration Guide

This document explains how `flask-openapi3` has been integrated into our Flask application to automatically generate OpenAPI specifications and provide interactive API documentation.

## Table of Contents

1. [What is flask-openapi3?](#what-is-flask-openapi3)
2. [Why flask-openapi3?](#why-flask-openapi3)
3. [How It Works](#how-it-works)
4. [Changes Made to Our Application](#changes-made-to-our-application)
5. [Automatic OpenAPI Specification Generation](#automatic-openapi-specification-generation)
6. [Available Documentation UIs](#available-documentation-uis)
7. [Custom Documentation URLs](#custom-documentation-urls)
8. [Editing the OpenAPI Specification](#editing-the-openapi-specification)
9. [Request Validation Flow](#request-validation-flow)
10. [Quick Reference](#quick-reference)

---

## What is flask-openapi3?

`flask-openapi3` is a Flask extension that:

1. **Replaces** the standard Flask class with an `OpenAPI` class
2. **Automatically generates** OpenAPI 3.x specifications from your code
3. **Provides built-in** Swagger UI, ReDoc, and RapiDoc documentation interfaces
4. **Uses Pydantic** for request/response validation (which we already use!)

### Key Insight

```
Regular Flask:
    Flask + Pydantic → Validation works, but NO auto documentation

flask-openapi3:
    OpenAPI class + Pydantic → Validation works AND auto documentation!
```

---

## Why flask-openapi3?

| Feature                        | Regular Flask + Pydantic    | flask-openapi3     |
| ------------------------------ | --------------------------- | ------------------ |
| Request validation             | ✅ Manual integration       | ✅ Built-in        |
| Response validation            | ❌ Manual                   | ✅ Built-in        |
| OpenAPI spec generation        | ❌ Manual (write YAML/JSON) | ✅ Automatic       |
| Swagger UI                     | ❌ Manual setup             | ✅ Built-in        |
| ReDoc UI                       | ❌ Manual setup             | ✅ Built-in        |
| Keep existing Pydantic schemas | N/A                         | ✅ 100% compatible |

### The Problem It Solves

Previously, we had this disconnect:

```
┌─────────────────────────────────────────────────────────────┐
│ Pydantic Schema                                             │
│   class UserCreateSchema(BaseModel):                        │
│       username: str = Field(min_length=3, max_length=80)    │
│       email: EmailStr                                       │
│       ...                                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Schema knows:                                               │
│   - username must be 3-80 chars                             │
│   - email must be valid format                              │
│   - Which fields are required vs optional                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ╳ THIS KNOWLEDGE WAS LOST!
                            │ Flask didn't expose it to docs
                            │
┌─────────────────────────────────────────────────────────────┐
│ API Documentation: "What fields does /register need?"        │
│ Answer: ¯\_(ツ)_/¯ You'd have to read the code              │
└─────────────────────────────────────────────────────────────┘
```

**flask-openapi3 bridges this gap** - it extracts schema information and exposes it via OpenAPI.

---

## How It Works

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YOUR CODE                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Pydantic Schemas (unchanged)                                        │
│     class UserCreateSchema(BaseModel):                                  │
│         username: str = Field(min_length=3)                             │
│         email: EmailStr                                                 │
│                                                                         │
│  2. Route Definition (new syntax)                                        │
│     @users_bp.post("/register")                                         │
│     def register_user(body: UserCreateSchema):  # ← Type hint magic     │
│         ...                                                             │
│                                                                         │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                    flask-openapi3   │   Introspects your code
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    GENERATED OPENAPI SPEC                               │
├─────────────────────────────────────────────────────────────────────────┤
│  {                                                                      │
│    "paths": {                                                           │
│      "/api/users/register": {                                           │
│        "post": {                                                        │
│          "requestBody": {                                               │
│            "content": {                                                 │
│              "application/json": {                                      │
│                "schema": { "$ref": "#/components/schemas/UserCreate" }  │
│              }                                                          │
│            }                                                            │
│          }                                                              │
│        }                                                                │
│      }                                                                  │
│    },                                                                   │
│    "components": {                                                      │
│      "schemas": {                                                       │
│        "UserCreateSchema": {                                            │
│          "type": "object",                                              │
│          "required": ["username", "email", "password", "first_name"],    │
│          "properties": {                                                │
│            "username": { "type": "string", "minLength": 3 }             │
│          }                                                              │
│        }                                                                │
│      }                                                                  │
│    }                                                                    │
│  }                                                                      │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                         Served at  │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Documentation UIs                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  /openapi/swagger       →  Swagger UI (interactive testing)             │
│  /openapi/redoc         →  ReDoc (clean documentation)                  │
│  /openapi/rapidoc       →  RapiDoc (alternative UI)                     │
│  /openapi/openapi.json  →  Raw JSON specification                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Changes Made to Our Application

### 1. App Factory (`app/__init__.py`)

**Before:**

```python
from flask import Flask

app = Flask(__name__)
app.register_blueprint(users_bp, url_prefix="/api/users")
```

**After:**

```python
from flask_openapi3 import OpenAPI, Info

# API metadata for documentation
info = Info(
    title="Flask PostgreSQL Learning API",
    version="1.0.0",
    description="API description in Markdown..."
)

app = OpenAPI(__name__, info=info)
app.register_api(users_bp)  # Note: register_api, not register_blueprint
```

**Key Changes:**

- `Flask` → `OpenAPI`
- `register_blueprint()` → `register_api()`
- Added `Info` object with API metadata

### 2. Blueprints → APIBlueprints

**Before:**

```python
from flask import Blueprint

users_bp = Blueprint("users", __name__)

@users_bp.route("/register", methods=["POST"])
@validate_with_schema(UserCreateSchema)  # Our custom decorator
def register_user(validated_data: UserCreateSchema):
    ...
```

**After:**

```python
from flask_openapi3 import APIBlueprint, Tag

tag = Tag(name="Users", description="User management")

users_bp = APIBlueprint(
    "users",
    __name__,
    url_prefix="/api/users",  # URL prefix set here
    abp_tags=[tag],           # Tag for grouping in docs
)

@users_bp.post("/register")  # HTTP method as decorator name
def register_user(body: UserCreateSchema):  # 'body' is auto-validated
    ...
```

**Key Changes:**

- `Blueprint` → `APIBlueprint`
- `@bp.route(..., methods=["POST"])` → `@bp.post(...)`
- `@validate_with_schema(Schema)` → `def func(body: Schema):`
- `url_prefix` moved to `APIBlueprint` constructor

### 3. Route Parameters

**Path Parameters:**

```python
# Define a Pydantic model for path parameters
class UserPath(BaseModel):
    user_id: int = Field(..., ge=1, description="User ID")

# Use it in the route
@users_bp.get("/<int:user_id>")
def get_user(path: UserPath):  # 'path' is auto-validated
    user = User.query.get_or_404(path.user_id)
    ...
```

**Query Parameters:**

```python
class UserQuery(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

@users_bp.get("/")
def get_users(query: UserQuery):
    users = User.query.limit(query.limit).offset(query.offset).all()
    ...
```

### 4. Response Schemas

```python
@users_bp.post(
    "/register",
    summary="Register New User",
    description="Creates a new user account.",
    responses={
        201: UserDataResponse,      # Success response schema
        409: ErrorResponse,         # Conflict error schema
        422: ValidationErrorResponse,  # Validation error schema
    },
)
def register_user(body: UserCreateSchema):
    ...
```

---

## Automatic OpenAPI Specification Generation

### What Gets Auto-Generated?

| Source                                 | What's Generated                          |
| -------------------------------------- | ----------------------------------------- |
| `Info(title=..., version=...)`         | API title, version, description           |
| `Tag(name=..., description=...)`       | Endpoint groupings                        |
| `@bp.post("/path", summary=...)`       | Endpoint path, method, summary            |
| Method signature `(body: Schema)`      | Request body schema                       |
| Method signature `(path: PathModel)`   | Path parameter schemas                    |
| Method signature `(query: QueryModel)` | Query parameter schemas                   |
| `responses={200: ResponseModel}`       | Response schemas                          |
| Pydantic `Field(...)`                  | Field constraints, descriptions, examples |

### How Pydantic Fields Map to OpenAPI

```python
# Pydantic Field Definition
username: str = Field(
    ...,                              # required (no default)
    min_length=3,                     # minimum string length
    max_length=80,                    # maximum string length
    pattern=r"^[a-zA-Z0-9_]+$",       # regex pattern
    description="Unique username",    # field description
    examples=["john_doe"],            # example values
)
```

Becomes this OpenAPI schema:

```json
{
  "username": {
    "type": "string",
    "minLength": 3,
    "maxLength": 80,
    "pattern": "^[a-zA-Z0-9_]+$",
    "description": "Unique username",
    "examples": ["john_doe"]
  }
}
```

---

## Available Documentation UIs

After starting your Flask app, these URLs are available:

### Default flask-openapi3 URLs

| URL                                          | Description                                |
| -------------------------------------------- | ------------------------------------------ |
| `http://localhost:5500/openapi/swagger`      | **Swagger UI** - Interactive API testing   |
| `http://localhost:5500/openapi/redoc`        | **ReDoc** - Clean, readable documentation  |
| `http://localhost:5500/openapi/rapidoc`      | **RapiDoc** - Alternative documentation UI |
| `http://localhost:5500/openapi/openapi.json` | **Raw JSON** - OpenAPI specification file    |

### Swagger UI Features

1. **Try It Out** - Execute API calls directly from the browser
2. **Request Builder** - Auto-generated forms based on schemas
3. **Response Viewer** - See actual API responses
4. **Schema Browser** - Explore all data models
5. **Authentication** - Test with auth headers (when implemented)

---

## Custom Documentation URLs

We've added cleaner, shorter URLs that redirect to the default documentation:

| Custom URL                           | Redirects To            | Description  |
| ------------------------------------ | ----------------------- | ------------ |
| `http://localhost:5500/docs`         | `/openapi/swagger`      | Swagger UI   |
| `http://localhost:5500/redoc`        | `/openapi/redoc`        | ReDoc        |
| `http://localhost:5500/rapidoc`      | `/openapi/rapidoc`      | RapiDoc      |
| `http://localhost:5500/openapi.json` | `/openapi/openapi.json` | OpenAPI JSON |

### How Custom URLs Work

The custom URLs are implemented as redirect routes in `app/__init__.py`:

```python
from flask import redirect

@app.route("/docs")
def docs_redirect():
    """Redirect /docs to Swagger UI."""
    return redirect("/openapi/swagger")

@app.route("/redoc")
def redoc_redirect():
    """Redirect /redoc to ReDoc."""
    return redirect("/openapi/redoc")

@app.route("/rapidoc")
def rapidoc_redirect():
    """Redirect /rapidoc to RapiDoc."""
    return redirect("/openapi/rapidoc")

@app.route("/openapi.json")
def openapi_json_redirect():
    """Redirect /openapi.json to the OpenAPI specification."""
    return redirect("/openapi/openapi.json")
```

### Why Use Redirects Instead of Direct Custom Paths?

flask-openapi3's static assets (CSS, JavaScript for Swagger UI, ReDoc, etc.) are
served from paths relative to `doc_prefix`. When we tried setting `doc_prefix=""`
with custom URLs, the static assets couldn't be found.

The redirect approach:

1. ✅ Keeps static asset serving working correctly
2. ✅ Provides clean, memorable URLs (`/docs` instead of `/openapi/swagger`)
3. ✅ No impact on performance (browser follows redirect instantly)
4. ✅ Both URL styles work simultaneously

---

## Editing the OpenAPI Specification

### Method 1: Edit Through Code (Recommended)

The best way to customize the spec is through your code:

**API-Level Customization:**

```python
info = Info(
    title="My API",
    version="1.0.0",
    description="Markdown **description** here",
    terms_of_service="https://example.com/terms",
    contact={"name": "Support", "email": "support@example.com"},
    license={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)
```

**Endpoint-Level Customization:**

```python
@users_bp.post(
    "/register",
    summary="Register New User",              # Short summary
    description="Long description here...",   # Detailed description
    operation_id="createUser",                # Unique operation ID
    deprecated=False,                         # Mark as deprecated
    responses={...},                          # Response schemas
)
```

**Schema-Level Customization:**

```python
class UserCreateSchema(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "first_name": "John"
            }
        }
    )
```

### Method 2: Export, Edit, and Serve Custom Spec

If you need to manually edit the JSON:

1. **Export the spec:**

   ```bash
   curl http://localhost:5500/openapi/openapi.json > custom_openapi.json
   ```

2. **Edit `custom_openapi.json`** with any changes you need

3. **Serve the custom spec** (advanced - requires custom route):
   ```python
   @app.get("/custom-docs")
   def custom_docs():
       with open("custom_openapi.json") as f:
           return json.load(f)
   ```

### Method 3: Add Extra Schema Properties

For fields that Pydantic doesn't directly support:

```python
username: str = Field(
    ...,
    json_schema_extra={
        "x-custom-property": "custom value",
        "externalDocs": {
            "description": "Learn more",
            "url": "https://example.com/docs"
        }
    }
)
```

---

## Request Validation Flow

### How flask-openapi3 Handles Requests

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. INCOMING REQUEST                                                     │
│    POST /api/users/register                                             │
│    Body: {"username": "ab", "email": "invalid", ...}                    │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. FLASK-OPENAPI3 INTERCEPTS                                            │
│    Sees: def register_user(body: UserCreateSchema)                      │
│    Action: Parses JSON and validates against UserCreateSchema           │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌────────────────────────────┐      ┌────────────────────────────────────┐
│ 3a. VALIDATION FAILS       │      │ 3b. VALIDATION SUCCEEDS            │
│                            │      │                                    │
│ Returns 422 response:      │      │ Calls your function with           │
│ {                          │      │ validated schema instance:         │
│   "detail": [              │      │                                    │
│     {                      │      │ def register_user(body):           │
│       "loc": ["username"], │      │     # body.username is validated   │
│       "msg": "too short",  │      │     # body.email is valid EmailStr │
│       "type": "string..."  │      │     # All transformations applied  │
│     }                      │      │     ...                            │
│   ]                        │      │                                    │
│ }                          │      │                                    │
└────────────────────────────┘      └────────────────────────────────────┘
```

### Comparison: Before and After

**Before (Custom Decorator):**

```python
@users_bp.route("/register", methods=["POST"])
@validate_with_schema(UserCreateSchema)
def register_user(validated_data: UserCreateSchema):
    # validated_data injected by our decorator
    ...
```

**After (flask-openapi3):**

```python
@users_bp.post("/register")
def register_user(body: UserCreateSchema):
    # body automatically validated by flask-openapi3
    ...
```

The key difference:

- **Before:** We wrote custom `validate_with_schema` decorator
- **After:** flask-openapi3 handles this automatically based on type hints

---

## Quick Reference

### Import Changes

```python
# Before
from flask import Flask, Blueprint

# After
from flask_openapi3 import OpenAPI, APIBlueprint, Info, Tag
```

### Route Decorator Mapping

| Before                                   | After                 |
| ---------------------------------------- | --------------------- |
| `@bp.route("/path", methods=["GET"])`    | `@bp.get("/path")`    |
| `@bp.route("/path", methods=["POST"])`   | `@bp.post("/path")`   |
| `@bp.route("/path", methods=["PUT"])`    | `@bp.put("/path")`    |
| `@bp.route("/path", methods=["DELETE"])` | `@bp.delete("/path")` |
| `@bp.route("/path", methods=["PATCH"])`  | `@bp.patch("/path")`  |

### Parameter Types

| Parameter Type   | In Route Signature     |
| ---------------- | ---------------------- |
| Request Body     | `body: BodySchema`     |
| Path Parameters  | `path: PathSchema`     |
| Query Parameters | `query: QuerySchema`   |
| Headers          | `header: HeaderSchema` |
| Cookies          | `cookie: CookieSchema` |

### Documentation URLs

| Custom URL      | Default URL             | Purpose               |
| --------------- | ----------------------- | --------------------- |
| `/docs`         | `/openapi/swagger`      | Swagger UI            |
| `/redoc`        | `/openapi/redoc`        | ReDoc documentation   |
| `/rapidoc`      | `/openapi/rapidoc`      | RapiDoc documentation |
| `/openapi.json` | `/openapi/openapi.json` | Raw OpenAPI JSON      |

---

## Summary

### What We Achieved

1. ✅ **Automatic OpenAPI spec generation** from existing Pydantic schemas
2. ✅ **Built-in Swagger UI** for interactive API testing
3. ✅ **No manual YAML/JSON writing** - specs derived from code
4. ✅ **Pydantic schemas unchanged** - only route syntax updated
5. ✅ **All existing validation** still works

### Key Takeaways

1. **flask-openapi3 is a drop-in enhancement**, not a replacement
2. **Your Pydantic schemas are the single source of truth** for both validation AND documentation
3. **Type hints drive everything** - `body: Schema` tells flask-openapi3 what to do
4. **Documentation stays in sync** with code automatically

---

## Next Steps

1. **Add Authentication** - Configure security schemes in OpenAPI
2. **Add Response Examples** - Make Swagger UI show example responses
3. **Customize Swagger UI** - Brand with custom CSS
4. **Add Request/Response Logging** - For debugging

For more information, see:

- [flask-openapi3 Documentation](https://luolingchun.github.io/flask-openapi3/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
