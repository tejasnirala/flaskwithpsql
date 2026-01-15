# Known Issues and Future Improvements

> **Production-Readiness TODO List**

This document tracks known issues and areas for improvement identified during code review. These items should be addressed before deploying to production.

---

## Table of Contents

1. [Critical Issues](#critical-issues)
2. [Security Issues](#security-issues)
3. [Testing Issues](#testing-issues)
4. [Code Quality](#code-quality)
5. [Minor Improvements](#minor-improvements)
6. [Fixed Issues](#fixed-issues)

---

## Critical Issues

### 1. In-Memory Token Blacklist is NOT Production-Ready

**File:** `app/auth/__init__.py` (lines 57-59)

**Status:** ⚠️ Open

**Problem:**

```python
# Current implementation
_token_blacklist = set()  # In-memory - lost on restart!
```

-   Blacklist is lost on server restart
-   Doesn't work with multiple workers/instances (Gunicorn uses 4 workers)
-   A logged-out token will still work on other workers

**Required Fix:** Implement Redis-based blacklist for production:

```python
# Example with Redis
import redis
_redis = redis.Redis(host='localhost', port=6379, db=0)

def revoke_token(jti: str, expires_in: int = 86400) -> None:
    _redis.setex(f"blacklist:{jti}", expires_in, "1")

def is_token_revoked(jti: str) -> bool:
    return _redis.get(f"blacklist:{jti}") is not None
```

**Priority:** 🔴 Critical (Must fix before production)

---

### 2. Testing Configuration Uses PostgreSQL

**File:** `config.py` (lines 287-290)

**Status:** ⚠️ Open

**Problem:**

```python
SQLALCHEMY_DATABASE_URI: str = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/flaskwithpsql_test",
)
```

-   Requires a running PostgreSQL server for tests
-   Tests are slower and less portable
-   Documentation mentions using SQLite for tests, but config uses PostgreSQL

**Suggested Fix:** Use in-memory SQLite for faster, isolated tests:

```python
SQLALCHEMY_DATABASE_URI: str = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:",
)
```

**Note:** Some PostgreSQL-specific features (schemas, JSONB) won't work with SQLite.

**Priority:** 🟠 Significant

---

### 3. Auth Headers Test Fixture is Placeholder

**File:** `tests/conftest.py` (lines 119-127)

**Status:** ⚠️ Open

**Problem:**

```python
@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}  # Fake token!
```

-   `"Bearer test-token"` is not a valid JWT
-   Protected route tests will fail with 401

**Required Fix:**

```python
@pytest.fixture
def auth_headers(client, sample_user):
    """Get real authentication headers."""
    response = client.post("/api/v1/auth/login", json={
        "email": sample_user.email,
        "password": "TestPassword123!"
    })
    token = response.json["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

**Priority:** 🔴 Critical (Tests won't work properly)

---

## Security Issues

### 4. No Password Change Endpoint

**Status:** ⚠️ Open

Users can register and login, but there's no endpoint to:

-   Change password
-   Reset password (forgot password flow)
-   Email verification

**Priority:** 🟠 Significant (Required for production)

---

### 5. Logging Sensitive Information

**File:** `app/services/user_service.py`

**Status:** ⚠️ Open

**Problem:**

```python
logger.warning(f"Email already exists: {data.email}")  # Email in logs!
```

Email addresses are PII and shouldn't be logged directly.

**Fix:** Mask or hash the email:

```python
logger.warning(f"Email already exists: {data.email[:3]}***@***")
```

**Priority:** 🟠 Significant

---

## Testing Issues

### 6. Health Check Doesn't Verify Dependencies

**Status:** ⚠️ Open

The `/health` endpoint just returns `200 OK` without checking:

-   Database connectivity
-   Redis connectivity (when added)

**Suggested Fix:**

```python
@app.route("/health")
def health():
    checks = {
        "database": check_database(),
        "redis": check_redis(),
    }
    healthy = all(checks.values())
    return jsonify({"healthy": healthy, "checks": checks}), 200 if healthy else 503
```

**Priority:** 🟢 Medium

---

## Code Quality

### 7. Port Mismatch in Documentation

**Status:** ⚠️ Open

Inconsistent port defaults across files:

-   `.env.example`: `FLASK_PORT=5000`
-   `run.py`: Default port `5500`
-   `Dockerfile`: Exposes port `5500`

**Fix:** Standardize to one port (5500) and update `.env.example`

**Priority:** 🔵 Low

---

### 8. No Index on `is_deleted` Column

**File:** `app/models/base.py`

**Status:** ⚠️ Open

You frequently filter by `is_deleted=False`, but this column has no index.

**Fix:**

```python
# In BaseModel
is_deleted = Column(Boolean, default=False, index=True)
```

**Priority:** 🔵 Low (Performance optimization)

---

### 9. No Request ID for Tracing

**Status:** ⚠️ Open

The `MetaInfo` schema has `request_id` field, but it's never populated.

**Fix:** Add request ID generation:

```python
@app.before_request
def add_request_id():
    g.request_id = str(uuid.uuid4())
```

**Priority:** 🔵 Low (Helpful for debugging)

---

## Minor Improvements

### 10. Missing Custom Validation Messages

**File:** `app/schemas/user.py`

Some fields could have more user-friendly error messages.

**Priority:** 🔵 Low

---

### 11. Makefile help Target

Add a comprehensive `help` target that lists all available commands with descriptions.

**Priority:** 🔵 Low

---

## Fixed Issues ✅

These issues have been addressed:

| Issue                            | Description                                                              | Fix Date   |
| -------------------------------- | ------------------------------------------------------------------------ | ---------- |
| Hardcoded `debug=True` in run.py | Debug mode was always enabled                                            | 2026-01-15 |
| Email enumeration vulnerability  | Auth returned different errors for "user not found" vs "wrong password"  | 2026-01-15 |
| No rate limiting on login        | Login endpoint had no brute-force protection                             | 2026-01-15 |
| Duplicate RBAC decorator code    | JWT verification was duplicated in permission_required and role_required | 2026-01-15 |
| Inconsistent type annotations    | Used lowercase `tuple` instead of `Tuple` from typing                    | 2026-01-15 |

---

## Priority Legend

| Symbol | Priority    | Action                     |
| ------ | ----------- | -------------------------- |
| 🔴     | Critical    | Must fix before production |
| 🟠     | Significant | Should fix soon            |
| 🟢     | Medium      | Nice to have               |
| 🔵     | Low         | When time permits          |

---

> **Next Steps:**
>
> 1. Fix critical issues before any production deployment
> 2. Add proper test coverage with working auth fixtures
> 3. Implement Redis-based token blacklist
> 4. Add password reset functionality
