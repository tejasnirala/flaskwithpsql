# Centralized Logging System

This document explains the centralized logging system implemented in the Flask application. The system provides structured logging with request correlation, sensitive data protection, and production-ready observability.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Log Levels Guide](#log-levels-guide)
5. [Request Correlation](#request-correlation)
6. [Log Formats](#log-formats)
7. [Security & Privacy](#security--privacy)
8. [Usage Guide](#usage-guide)
9. [Flow Diagrams](#flow-diagrams)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Centralized Logging?

Centralized logging means having a single, consistent logging configuration that is used across the entire application. Instead of each module configuring its own logging, all modules use the same logger setup, ensuring:

- **Consistent format** - All logs look the same
- **Centralized configuration** - One place to change log settings
- **Request correlation** - Ability to trace all logs from a single request
- **Security** - Automatic masking of sensitive data

### Key Features

| Feature                     | Description                                                                    |
| --------------------------- | ------------------------------------------------------------------------------ |
| **Structured JSON Logging** | Logs are output as JSON for easy parsing by log aggregation tools              |
| **Request ID Correlation**  | Every request gets a unique ID that appears in all related logs                |
| **Sensitive Data Masking**  | Passwords, tokens, and secrets are automatically redacted                      |
| **Dual Output**             | Console (human-readable in dev) + File (JSON for production)                   |
| **Daily Log Rotation**      | New log file each day (e.g., `app.log.2026-01-11`) with configurable retention |

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Logging System                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────────────┐    ┌──────────────────────┐              │
│   │   logging_config.py   │    │   Request Middleware │              │
│   │                      │    │                      │              │
│   │  • setup_logging()   │◄───│  • before_request    │              │
│   │  • JSONFormatter     │    │  • after_request     │              │
│   │  • ConsoleFormatter  │    │  • teardown_request  │              │
│   │  • mask_sensitive()  │    │  • request_id gen    │              │
│   └──────────────────────┘    └──────────────────────┘              │
│              │                           │                          │
│              ▼                           ▼                          │
│   ┌──────────────────────────────────────────────────────┐          │
│   │                   Python Logging                     │          │
│   │                                                      │          │
│   │  ┌─────────────────┐    ┌─────────────────┐          │          │
│   │  │ Console Handler │    │  File Handler   │          │          │
│   │  │ (stdout)        │    │ (logs/app.log)  │          │          │
│   │  └─────────────────┘    └─────────────────┘          │          │
│   └──────────────────────────────────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### File Structure

```
app/
├── utils/
│   ├── __init__.py          # Exports logging utilities
│   └── logging_config.py    # Main logging configuration
│
logs/
├── app.log                  # Current day's logs (JSON format)
├── app.log.2026-01-10       # Yesterday's logs
├── app.log.2026-01-09       # Two days ago
└── ...                      # Up to LOG_RETENTION_DAYS (default: 30)
```

---

## Configuration

### Environment Variables

| Variable             | Default                       | Description                          |
| -------------------- | ----------------------------- | ------------------------------------ |
| `LOG_LEVEL`          | `DEBUG` (dev) / `INFO` (prod) | Minimum log level to output          |
| `LOG_RETENTION_DAYS` | `30`                          | Number of days to keep old log files |

### Initialization

The logging system is initialized in the application factory (`app/__init__.py`):

```python
from app.utils.logging_config import setup_logging

def create_app(config_name="default"):
    app = OpenAPI(__name__, info=info)
    app.config.from_object(config_class)

    # Initialize logging early
    setup_logging(app)

    # ... rest of initialization
```

### What `setup_logging()` Does

1. **Determines environment** - Checks `app.debug` to decide formatting style
2. **Creates console handler** - Human-readable in dev, JSON in production
3. **Creates file handler** - Daily rotating files with JSON format
4. **Suppresses noisy loggers** - Reduces noise from werkzeug, urllib3, etc.
5. **Registers request middleware** - Adds request lifecycle logging

---

## Log Levels Guide

Python's logging module provides 5 standard log levels. Here's how we use each:

### Level Hierarchy

```
CRITICAL (50) ─── Application-level failure
    │
ERROR (40) ────── Request failed but app continues
    │
WARNING (30) ──── Recoverable issues
    │
INFO (20) ─────── Normal application flow
    │
DEBUG (10) ────── Internal development details
```

### When to Use Each Level

#### DEBUG

Use for internal development details that help trace code execution.

```python
logger.debug(f"Retrieved {len(users)} users from database")
logger.debug(f"Fields being updated: {list(update_data.keys())}")
```

**Examples:**

- Variable values during debugging
- Function entry/exit traces
- Query results counts
- Cache hits/misses

#### INFO

Use for normal application flow events that are useful in production.

```python
logger.info(f"User registered successfully: id={user.id}")
logger.info("Request started")
logger.info("Request completed")
```

**Examples:**

- Request lifecycle (start/end)
- User actions (login, register, update)
- Business events (order placed, payment processed)
- System startup/shutdown

#### WARNING

Use for potentially problematic situations that don't prevent operation.

```python
logger.warning(f"Login failed: invalid password for user_id={user.id}")
logger.warning("Rate limit approaching threshold")
```

**Examples:**

- Authentication failures
- Validation warnings
- Deprecated feature usage
- Resource usage approaching limits

#### ERROR

Use when a request fails but the application continues.

```python
logger.error(f"Database connection failed: {error}", exc_info=True)
logger.error("External API call failed")
```

**Examples:**

- Caught exceptions that prevent completing a request
- Failed API calls
- Database errors
- File system errors

#### CRITICAL

Use for application-level failures that may require immediate attention.

```python
logger.critical("Database connection pool exhausted")
logger.critical("Required service unavailable")
```

**Examples:**

- Database pool exhausted
- Required external service down
- Configuration errors preventing startup
- Security breaches detected

---

## Request Correlation

### How It Works

Every incoming request receives a unique `request_id`:

```
Request arrives
       │
       ▼
  ┌────────────────────────────────┐
  │        before_request          │
  │                                │
  │  1. Check for X-Request-ID     │
  │     header (distributed trace) │
  │  2. Generate UUID if none      │
  │  3. Store in Flask's g object  │
  │  4. Log "Request started"      │
  └────────────────────────────────┘
       │
       ▼
    Route Handler
       │
       ▼
  ┌────────────────────────────────┐
  │        after_request           │
  │                                │
  │  1. Calculate duration         │
  │  2. Log "Request completed"    │
  │  3. Add X-Request-ID header    │
  └────────────────────────────────┘
```

### Using Request ID

The `request_id` is automatically included in all logs within a request context:

```
2026-01-11 20:20:06 | INFO | app.request | [4eb32ecd] GET /health | Request started
2026-01-11 20:20:06 | INFO | app.request | [4eb32ecd] GET /health | Request completed
```

### Client-Side Correlation

The `X-Request-ID` is returned in response headers:

```bash
curl -i http://localhost:5500/health
# Response headers include:
# X-Request-ID: 4eb32ecd
```

This allows clients to include the request ID in bug reports for easier debugging.

### Distributed Tracing

For microservices, clients can send an `X-Request-ID` header, which will be used instead of generating a new one:

```bash
curl -H "X-Request-ID: my-trace-123" http://localhost:5500/health
```

---

## Log Formats

### Console Format (Development)

Human-readable format for development:

```
2026-01-11 20:20:06 | INFO     | app.routes.users | [4eb32ecd] POST /api/users/register | User registered successfully
```

Format breakdown:

- `2026-01-11 20:20:06` - Timestamp
- `INFO` - Log level (padded to 8 chars)
- `app.routes.users` - Logger name (module path)
- `[4eb32ecd]` - Request ID
- `POST /api/users/register` - HTTP method and path
- `User registered successfully` - Log message

### JSON Format (File & Production Console)

Structured JSON for log aggregation:

```json
{
  "timestamp": "2026-01-11T14:50:06.123456+00:00",
  "level": "INFO",
  "logger": "app.routes.users",
  "request_id": "4eb32ecd",
  "method": "POST",
  "path": "/api/users/register",
  "message": "User registered successfully",
  "extra": {
    "user_id": 42,
    "username": "johndoe"
  }
}
```

### Why JSON for Files?

1. **Parseable** - Log aggregation tools (ELK, Splunk, CloudWatch) can parse JSON
2. **Queryable** - Filter logs by any field
3. **Structured** - Consistent field names across all logs
4. **Extensible** - Easy to add new fields without breaking parsing

---

## Security & Privacy

### Automatic Masking

The logging system automatically masks sensitive fields:

```python
# These fields are NEVER logged with actual values:
SENSITIVE_FIELDS = frozenset([
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "secret",
    "secret_key",
    "authorization",
    "credential",
    "private_key",
    "credit_card",
    "cvv",
    "ssn",
])
```

### How Masking Works

```python
# Before masking
{"username": "john", "password": "secret123"}

# After masking
{"username": "john", "password": "***REDACTED***"}
```

### What We DON'T Log

| Data Type                          | Reason                       |
| ---------------------------------- | ---------------------------- |
| Passwords                          | Security                     |
| Auth tokens                        | Security                     |
| Full request bodies                | May contain sensitive data   |
| Email addresses (in auth failures) | Prevents enumeration attacks |
| Credit card numbers                | PCI compliance               |
| Social security numbers            | Privacy laws                 |

### Safe Logging Practices

```python
# ✅ GOOD - Log only non-sensitive identifiers
logger.info(f"User registered: user_id={user.id}")
logger.warning(f"Login failed for user_id={user.id}")

# ❌ BAD - Never log sensitive data
logger.info(f"User registered: password={user.password}")  # NEVER DO THIS
logger.warning(f"Login failed for email={email}")  # Could enable enumeration
```

---

## Usage Guide

### Basic Usage in Any Module

```python
import logging

# Create a logger for this module
logger = logging.getLogger(__name__)

def some_function():
    logger.info("Operation started")
    try:
        # ... do something ...
        logger.info("Operation completed successfully")
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        raise
```

### Using the `@log_function_call` Decorator

For debugging service functions:

```python
from app.utils.logging_config import log_function_call

@log_function_call()
def process_payment(order_id, amount, card_token):
    # Automatically logs:
    # - Entering process_payment
    # - Exiting process_payment successfully (or exception details)
    ...
```

### Getting the Current Request ID

```python
from app.utils.logging_config import get_request_id

def some_function():
    request_id = get_request_id()
    # Use request_id for external API calls, database queries, etc.
    external_api.call(trace_id=request_id)
```

### Adding Extra Context to Logs

```python
logger.info(
    "User action completed",
    extra={
        "user_id": user.id,
        "action": "purchase",
        "item_count": 3
    }
)
```

This produces:

```json
{
  "timestamp": "...",
  "level": "INFO",
  "message": "User action completed",
  "extra": {
    "user_id": 42,
    "action": "purchase",
    "item_count": 3
  }
}
```

---

## Flow Diagrams

### Application Startup Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    Application Startup                       │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. create_app() called                                       │
│    - Load configuration                                       │
│    - Validate config                                          │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. setup_logging(app) called                                 │
│    - Determine environment (debug/production)                │
│    - Create log directory if needed                          │
│    - Configure root logger                                    │
│    - Add console handler                                     │
│    - Add file handler (rotating)                              │
│    - Suppress noisy third-party loggers                      │
│    - Register request middleware                             │
│    - Log "Logging initialized"                               │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Rest of app initialization                                │
│    - Initialize database                                     │
│    - Register blueprints                                     │
│    - Register error handlers                                 │
│    - All now use configured logging                           │
└──────────────────────────────────────────────────────────────┘
```

### Request Lifecycle Logging

```
┌──────────────────────────────────────────────────────────────┐
│                    HTTP Request Arrives                      │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ before_request middleware                                    │
│                                                              │
│ 1. Generate request_id (or use X-Request-ID header)          │
│ 2. Store in Flask's g.request_id                             │
│ 3. Store start time in g.request_start_time                  │
│ 4. Log: "Request started"                                    │
│    - Includes: remote_addr, user_agent, content_length       │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Route Handler Execution                                      │
│                                                              │
│ - All logger.* calls include request context automatically   │
│ - [request_id] METHOD PATH | message                         │
│                                                              │
│ Example logs:                                                │
│   [abc123] POST /api/users/register | Registration attempt   │
│   [abc123] POST /api/users/register | User registered        │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ after_request middleware                                     │
│                                                              │
│ 1. Calculate request duration                                │
│ 2. Determine log level based on status code:                 │
│    - 2xx/3xx → INFO                                          │
│    - 4xx → WARNING                                           │
│    - 5xx → ERROR                                             │
│ 3. Log: "Request completed"                                  │
│    - Includes: status_code, duration_ms, content_length      │
│ 4. Add X-Request-ID to response headers                      │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ If exception occurred: teardown_request                      │
│                                                              │
│ - Log ERROR with exception details                           │
│ - Include stack trace using exc_info=True                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### DO ✅

1. **Use module-level loggers**

   ```python
   logger = logging.getLogger(__name__)
   ```

2. **Use appropriate log levels**

   - DEBUG for development details
   - INFO for business events
   - WARNING for recoverable issues
   - ERROR for failures

3. **Include identifying information**

   ```python
   logger.info(f"User updated: user_id={user.id}")
   ```

4. **Use `exc_info=True` for exceptions**

   ```python
   logger.error(f"Operation failed", exc_info=True)
   ```

5. **Log at function boundaries**
   ```python
   logger.debug("Processing started")
   # ... work ...
   logger.debug("Processing completed")
   ```

### DON'T ❌

1. **Never log sensitive data**

   ```python
   # BAD
   logger.info(f"Login: email={email}, password={password}")
   ```

2. **Don't use print statements**

   ```python
   # BAD - use logger.info() instead
   print("User created")
   ```

3. **Don't log too much at INFO level**

   ```python
   # BAD - this should be DEBUG
   logger.info(f"Checking condition: {some_variable}")
   ```

4. **Don't suppress exceptions silently**
   ```python
   # BAD
   except Exception:
       pass  # At least log the error!
   ```

---

## Troubleshooting

### Logs Not Appearing

1. **Check log level** - Set `LOG_LEVEL=DEBUG` environment variable
2. **Check console output** - Development logs go to stdout
3. **Check file** - Look in `logs/app.log`

### Log File Not Created

1. **Check permissions** - Ensure the app can write to `logs/` directory
2. **Check path** - The log directory is created relative to `app/`

### Request ID Not Showing

1. **Outside request context** - Shows as `no-request` when not in a Flask request
2. **Check middleware** - Ensure `register_request_logging(app)` was called

### JSON Parsing Issues

1. **Check file format** - Each line should be valid JSON
2. **Check encoding** - File uses UTF-8 encoding

---

## Appendix: Log File Rotation

The logging system uses `TimedRotatingFileHandler` for **daily log rotation**:

### How It Works

| Setting       | Value      | Description                                     |
| ------------- | ---------- | ----------------------------------------------- |
| `when`        | `midnight` | Rotate at midnight (UTC)                        |
| `interval`    | `1`        | Every 1 day                                     |
| `backupCount` | `30`       | Keep 30 days of logs (configurable via env var) |
| `utc`         | `True`     | Use UTC time for consistent rotation            |
| `suffix`      | `%Y-%m-%d` | Date format for rotated files                   |

### File Naming Convention

```
logs/
├── app.log              # Current day's logs (always this name)
├── app.log.2026-01-10   # Yesterday's logs
├── app.log.2026-01-09   # Two days ago
├── app.log.2026-01-08   # Three days ago
└── ...                  # Up to 30 days (or LOG_RETENTION_DAYS)
```

### Benefits of Daily Rotation

1. **Easy to find historical logs** - Just look for the date file
2. **Simple archiving** - Move old files to cold storage by date
3. **Automatic cleanup** - Files older than retention period are deleted
4. **Compliance friendly** - Easy to prove log retention for audits
5. **Debugging** - Quickly narrow down issues to specific days

### Finding Logs for a Specific Date

```bash
# View logs from January 10, 2026
cat logs/app.log.2026-01-10

# Search for errors on a specific day
grep '"level": "ERROR"' logs/app.log.2026-01-10

# Search for a specific request ID across all logs
grep 'abc12345' logs/app.log*
```

### Configuring Retention Period

Set the `LOG_RETENTION_DAYS` environment variable:

```bash
# Keep logs for 7 days (development)
export LOG_RETENTION_DAYS=7

# Keep logs for 90 days (production/compliance)
export LOG_RETENTION_DAYS=90
```

### Disk Space Estimation

| Daily Log Size | Retention | Total Space |
| -------------- | --------- | ----------- |
| 10 MB          | 30 days   | ~300 MB     |
| 50 MB          | 30 days   | ~1.5 GB     |
| 100 MB         | 30 days   | ~3 GB       |
| 10 MB          | 90 days   | ~900 MB     |

> **Tip**: Monitor your log directory size and adjust retention based on your deployment environment.
