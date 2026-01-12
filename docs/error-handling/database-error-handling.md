# Database Error Handling in Flask

## Overview

This document explains how database errors are handled in the Flask application to ensure:

1. **User-Friendly Messages**: Users get helpful, actionable messages
2. **Security**: Internal database details are never exposed to clients
3. **Debugging**: Full technical details are logged server-side
4. **Consistency**: All errors follow the standard response envelope format

---

## The Problem: Raw Database Errors

Without proper handling, database errors expose sensitive information:

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "ProgrammingError: (psycopg2.errors.UndefinedTable) relation \"users.users\" does not exist\nLINE 2: FROM users.users..."
  }
}
```

### Why This Is Bad:

1. **Security Risk**: Attackers learn your table names, schema structure, and ORM being used
2. **Poor UX**: Users don't understand SQL errors
3. **Unprofessional**: Exposes internal implementation details

---

## The Solution: Layered Database Error Handlers

We register specific handlers for different SQLAlchemy exception types:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Database Error Handling Flow                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Exception Raised in Route Handler                                          │
│            │                                                                 │
│            ▼                                                                 │
│   ┌────────────────────────────────────────────────────────────────────────┐ │
│   │                    Flask Error Handler Chain                            │ │
│   │                                                                         │ │
│   │  ┌─────────────────────┐   Order matters! More specific handlers       │ │
│   │  │  IntegrityError     │   are checked first.                          │ │
│   │  │  (unique, FK, etc.) │                                               │ │
│   │  └──────────┬──────────┘                                               │ │
│   │             │ No match?                                                │ │
│   │             ▼                                                          │ │
│   │  ┌─────────────────────┐                                               │ │
│   │  │  OperationalError   │                                               │ │
│   │  │  (connection, auth) │                                               │ │
│   │  └──────────┬──────────┘                                               │ │
│   │             │ No match?                                                │ │
│   │             ▼                                                          │ │
│   │  ┌─────────────────────┐                                               │ │
│   │  │  ProgrammingError   │   ← Missing table, bad SQL                   │ │
│   │  │  (schema mismatch)  │                                               │ │
│   │  └──────────┬──────────┘                                               │ │
│   │             │ No match?                                                │ │
│   │             ▼                                                          │ │
│   │  ┌─────────────────────┐                                               │ │
│   │  │  DataError          │                                               │ │
│   │  │  (type mismatch)    │                                               │ │
│   │  └──────────┬──────────┘                                               │ │
│   │             │ No match?                                                │ │
│   │             ▼                                                          │ │
│   │  ┌─────────────────────┐                                               │ │
│   │  │  SQLAlchemyError    │   ← Catch-all for any other DB errors        │ │
│   │  │  (base class)       │                                               │ │
│   │  └──────────┬──────────┘                                               │ │
│   │             │ No match?                                                │ │
│   │             ▼                                                          │ │
│   │  ┌─────────────────────┐                                               │ │
│   │  │  Exception          │   ← Last resort catch-all                    │ │
│   │  │  (any exception)    │                                               │ │
│   │  └─────────────────────┘                                               │ │
│   │                                                                         │ │
│   └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│   Result:                                                                    │
│   ┌─────────────────────────────────────────────────────────────────────────┐│
│   │  SERVER-SIDE (Logs)       │  CLIENT-SIDE (Response)                     ││
│   │  ─────────────────────────│──────────────────────────────────           ││
│   │  Full traceback           │  User-friendly message                      ││
│   │  SQL statement            │  Generic error code                         ││
│   │  Table names              │  Appropriate HTTP status                    ││
│   │  Parameters               │  NO internal details                        ││
│   └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Exception Types and Their Meanings

### 1. IntegrityError (HTTP 409 Conflict)

**When it occurs:**

- Unique constraint violation (duplicate username, email)
- Foreign key constraint violation
- NOT NULL constraint violation
- Check constraint violation

**Example trigger:**

```python
# User tries to register with existing email
user = User(email="existing@example.com")
db.session.add(user)
db.session.commit()  # → IntegrityError
```

**Client receives:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "CONFLICT",
    "message": "A record with this information already exists"
  },
  "meta": null
}
```

---

### 2. OperationalError (HTTP 503 Service Unavailable)

**When it occurs:**

- Database server is down
- Connection timeout
- Connection pool exhausted
- Authentication failure

**Example trigger:**

```python
# Database server is unreachable
db.session.query(User).all()  # → OperationalError
```

**Client receives:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "DATABASE_ERROR",
    "message": "The service is temporarily unavailable. Please try again later."
  },
  "meta": null
}
```

**Server logs (CRITICAL level):**

```
Database OperationalError - Database may be unavailable
Traceback: psycopg2.OperationalError: could not connect to server...
```

---

### 3. ProgrammingError (HTTP 500 Internal Server Error)

**When it occurs:**

- Table doesn't exist (missing migrations)
- Column doesn't exist
- Invalid SQL syntax
- Schema mismatch between code and database

**Example trigger:**

```python
# Table hasn't been created yet
User.query.filter_by(username="test").first()  # → ProgrammingError
```

**This is what you encountered!** The `users.users` table didn't exist.

**Client receives:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "DATABASE_ERROR",
    "message": "The service encountered a configuration error. Please try again later."
  },
  "meta": null
}
```

**Server logs (ERROR level):**

```
Database ProgrammingError - Possible schema mismatch or missing migrations
Extra: {
  "error_type": "ProgrammingError",
  "original_error": "relation \"users.users\" does not exist",
  "hint": "Run 'flask db upgrade' to apply pending migrations"
}
```

---

### 4. DataError (HTTP 400 Bad Request)

**When it occurs:**

- Value too long for column
- Invalid data type conversion
- Numeric overflow

**Example trigger:**

```python
# Username column is VARCHAR(50), but input is 1000 characters
user = User(username="a" * 1000)
db.session.commit()  # → DataError
```

**Client receives:**

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "The provided data could not be processed. Please check your input."
  },
  "meta": null
}
```

---

### 5. SQLAlchemyError (Catch-All for DB Errors)

**When it occurs:**

- Any other SQLAlchemy error not caught by specific handlers

This ensures NO database error ever exposes raw SQL to clients.

---

## How Flask Error Handler Order Works

Flask checks handlers in this order:

```python
# 1. Most specific first
@app.errorhandler(IntegrityError)     # Checks this first
@app.errorhandler(OperationalError)   # Then this
@app.errorhandler(ProgrammingError)   # Then this
@app.errorhandler(DataError)          # Then this
@app.errorhandler(SQLAlchemyError)    # Then this (base class - catches remaining DB errors)
@app.errorhandler(Exception)          # Finally, catch-all for any other exception
```

**Key insight:** SQLAlchemy exceptions inherit from `SQLAlchemyError`, which inherits from `Exception`:

```
Exception
  └── SQLAlchemyError (base for all SQLAlchemy errors)
        ├── IntegrityError
        ├── OperationalError
        ├── ProgrammingError
        ├── DataError
        └── (many others...)
```

---

## Security Best Practices Implemented

### 1. Never Expose SQL or Table Names

```python
# ❌ BAD - Exposes table name
message = str(error)  # "relation 'users.users' does not exist"

# ✅ GOOD - Generic message
message = "The service encountered a configuration error."
```

### 2. Log Full Details Server-Side Only

```python
logger.error(
    "Database ProgrammingError - Possible schema mismatch",
    exc_info=True,  # Full traceback in logs
    extra={
        "original_error": str(error.orig),  # Full SQL error - ONLY in logs
        "hint": "Run 'flask db upgrade'"
    }
)
```

### 3. Even in Debug Mode, Don't Expose Details to Clients

```python
# In debug mode, we show the exception TYPE but not the MESSAGE
if app.debug:
    message = f"An unexpected error occurred ({type(error).__name__}). Check server logs."
else:
    message = "An unexpected error occurred."
```

The exception type (e.g., `ProgrammingError`) helps developers identify the issue class while the actual error details remain in server logs.

---

## Fixing Your Current Issue

The error you're seeing (`relation "users.users" does not exist`) indicates:

1. **The `users` schema and/or `users` table doesn't exist in the database**
2. **You need to run database migrations**

### Solution:

```bash
# 1. Create migrations if not already done
flask db init       # Only once, if migrations folder doesn't exist
flask db migrate -m "Create users table"

# 2. Apply migrations to database
flask db upgrade
```

### Or, if you want to quickly create tables for development:

```bash
# In Flask shell
flask shell
>>> from app import db
>>> db.create_all()
```

---

## Error Code Reference

| Exception Type   | HTTP Status | Error Code     | When It Happens               |
| ---------------- | ----------- | -------------- | ----------------------------- |
| IntegrityError   | 409         | CONFLICT       | Duplicate, FK violation, etc. |
| OperationalError | 503         | DATABASE_ERROR | DB connection issues          |
| ProgrammingError | 500         | DATABASE_ERROR | Missing table, bad SQL        |
| DataError        | 400         | BAD_REQUEST    | Data type mismatch            |
| SQLAlchemyError  | 500         | DATABASE_ERROR | Any other DB error            |

---

## Related Documentation

- [Standardized API Responses](../api/standardized-responses.md)
- [Logging Configuration](../logging/logging-setup.md)
- [Database Migrations](../database/migrations-guide.md)
