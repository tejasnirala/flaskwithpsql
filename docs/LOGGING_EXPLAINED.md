# Python Logging - Complete Guide

This document explains Python's logging system from the ground up, then walks through our complete implementation in `logging_config.py`. Since this is your first time working with logging, we'll start with the basics and build up to the advanced concepts.

## Table of Contents

1. [What is Logging?](#1-what-is-logging)
2. [Python's Built-in Logging Module](#2-pythons-built-in-logging-module)
3. [Core Concepts](#3-core-concepts)
4. [Log Levels Explained](#4-log-levels-explained)
5. [The Logging Flow](#5-the-logging-flow)
6. [Our Implementation Explained](#6-our-implementation-explained)
7. [Code Walkthrough](#7-code-walkthrough)
8. [Quick Reference](#8-quick-reference)

---

## 1. What is Logging?

### 1.1 Definition

**Logging** is the practice of recording events that happen during program execution. Think of it as a diary that your application writes automatically.

### 1.2 Why Not Just Use `print()`?

You might wonder: "Why not just use `print()` to see what's happening?"

| Feature            | `print()`                 | `logging`                                |
| ------------------ | ------------------------- | ---------------------------------------- |
| Goes to            | Only stdout (console)     | Console, files, network, email, etc.     |
| Severity levels    | ❌ No                     | ✅ DEBUG, INFO, WARNING, ERROR, CRITICAL |
| Timestamps         | ❌ Manual                 | ✅ Automatic                             |
| Turn on/off easily | ❌ Comment out all prints | ✅ Change log level                      |
| Production use     | ❌ Not suitable           | ✅ Designed for it                       |
| Performance        | Slow (always executes)    | Fast (can skip low-priority logs)        |
| Filtering          | ❌ No                     | ✅ By level, module, message             |

### 1.3 Real-World Example

**With print():**

```python
def login(username, password):
    print("Login attempt")  # Where did this come from? When?
    user = find_user(username)
    if not user:
        print("User not found")  # Is this an error? Warning?
    ...
```

**With logging:**

```python
import logging
logger = logging.getLogger(__name__)

def login(username, password):
    logger.info(f"Login attempt for user: {username}")
    # Output: 2026-01-11 10:30:45 | INFO | app.auth | Login attempt for user: john

    user = find_user(username)
    if not user:
        logger.warning(f"Login failed: user not found")
        # Output: 2026-01-11 10:30:45 | WARNING | app.auth | Login failed: user not found
```

---

## 2. Python's Built-in Logging Module

### 2.1 Is Logging Built-in?

**Yes!** Python's `logging` module is part of Python's **standard library**. This means:

- ✅ No `pip install` needed
- ✅ Available in every Python installation
- ✅ Stable and well-tested
- ✅ Used by thousands of production systems

### 2.2 Basic Import

```python
import logging
```

That's it! No external dependencies.

### 2.3 The Simplest Logging Example

```python
import logging

# Configure basic logging (quick & dirty way)
logging.basicConfig(level=logging.INFO)

# Create a logger
logger = logging.getLogger(__name__)

# Use it
logger.info("Hello, logging!")
logger.warning("This is a warning")
logger.error("Something went wrong")
```

Output:

```
INFO:__main__:Hello, logging!
WARNING:__main__:This is a warning
ERROR:__main__:Something went wrong
```

---

## 3. Core Concepts

Python's logging system has **four main components**. Understanding these is crucial:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Python Logging Architecture                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│    Your Code                                                        │
│        │                                                            │
│        ▼                                                            │
│    ┌─────────┐                                                      │
│    │ LOGGER  │  "The entry point - you call logger.info(), etc."   │
│    └────┬────┘                                                      │
│         │                                                           │
│         ▼                                                           │
│    ┌──────────┐                                                     │
│    │ HANDLER  │  "Where should logs go? Console? File? Both?"      │
│    └────┬─────┘                                                     │
│         │                                                           │
│         ▼                                                           │
│    ┌───────────┐                                                    │
│    │ FORMATTER │  "How should log messages look?"                  │
│    └───────────┘                                                    │
│         │                                                           │
│         ▼                                                           │
│    ┌────────────┐                                                   │
│    │ DESTINATION│  Console, File, Network, Email, etc.             │
│    └────────────┘                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.1 Logger

**What:** The object you interact with in your code.  
**Purpose:** Entry point for logging. You create one per module.

```python
import logging

# Create a logger for this module
logger = logging.getLogger(__name__)

# __name__ is a Python special variable that equals the module's full path
# Example: In app/routes/users.py, __name__ = "app.routes.users"

# Use the logger
logger.info("This is an info message")
logger.error("This is an error message")
```

**Key Points:**

- `logging.getLogger(name)` - Gets or creates a logger with that name
- `__name__` - Use this as the name (becomes module path)
- Loggers form a hierarchy based on dots (e.g., `app` → `app.routes` → `app.routes.users`)

### 3.2 Handler

**What:** Determines WHERE log messages go.  
**Purpose:** Send logs to different destinations.

```python
import logging
import sys

logger = logging.getLogger(__name__)

# Handler 1: Send to console (stdout)
console_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(console_handler)

# Handler 2: Send to file
file_handler = logging.FileHandler("app.log")
logger.addHandler(file_handler)

# Now logs go to BOTH console and file!
logger.info("This appears in console AND file")
```

**Common Handler Types:**

| Handler                    | Where Logs Go           | Use Case             |
| -------------------------- | ----------------------- | -------------------- |
| `StreamHandler`            | Console (stdout/stderr) | Development          |
| `FileHandler`              | Fixed file              | Simple file logging  |
| `RotatingFileHandler`      | File with size rotation | Prevent huge files   |
| `TimedRotatingFileHandler` | File with time rotation | Daily log files      |
| `SMTPHandler`              | Email                   | Send errors to admin |
| `HTTPHandler`              | HTTP endpoint           | Send to log server   |

### 3.3 Formatter

**What:** Determines HOW log messages look.  
**Purpose:** Format the log output.

```python
import logging

# Create a formatter
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Attach formatter to handler
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Attach handler to logger
logger = logging.getLogger(__name__)
logger.addHandler(handler)

logger.info("User logged in")
# Output: 2026-01-11 10:30:45 | INFO | __main__ | User logged in
```

**Common Format Variables:**

| Variable        | Meaning                  | Example                    |
| --------------- | ------------------------ | -------------------------- |
| `%(asctime)s`   | Human-readable timestamp | `2026-01-11 10:30:45`      |
| `%(levelname)s` | Log level name           | `INFO`, `WARNING`, `ERROR` |
| `%(name)s`      | Logger name              | `app.routes.users`         |
| `%(message)s`   | Your actual message      | `User logged in`           |
| `%(filename)s`  | Python filename          | `users.py`                 |
| `%(lineno)d`    | Line number              | `42`                       |
| `%(funcName)s`  | Function name            | `login_user`               |
| `%(module)s`    | Module name              | `users`                    |

### 3.4 Filter (Optional)

**What:** Additional filtering beyond log levels.  
**Purpose:** Fine-grained control over which logs pass through.

```python
# Only allow logs from specific modules
class ModuleFilter(logging.Filter):
    def filter(self, record):
        # Only allow logs from "app.routes" modules
        return record.name.startswith("app.routes")
```

---

## 4. Log Levels Explained

### 4.1 The Five Built-in Levels

Python provides 5 log levels, each with a numeric value:

```
                          SEVERITY
                              ▲
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
    │  CRITICAL (50) ─────────┼──── Application dying   │
    │       │                 │                         │
    │  ERROR (40) ────────────┼──── Request failed      │
    │       │                 │                         │
    │  WARNING (30) ──────────┼──── Something fishy     │
    │       │                 │                         │
    │  INFO (20) ─────────────┼──── Normal events       │
    │       │                 │                         │
    │  DEBUG (10) ────────────┼──── Developer details   │
    │       │                 │                         │
    │  NOTSET (0) ────────────┼──── Log everything      │
    │                         │                         │
    └─────────────────────────┼─────────────────────────┘
                              ▼
                         Less Important
```

### 4.2 How Log Level Filtering Works

When you set a log level, only messages at that level **or higher** are output:

```python
logger.setLevel(logging.WARNING)  # Set level to WARNING (30)

logger.debug("Debug message")     # 10 < 30 → IGNORED
logger.info("Info message")       # 20 < 30 → IGNORED
logger.warning("Warning message") # 30 >= 30 → OUTPUT ✅
logger.error("Error message")     # 40 >= 30 → OUTPUT ✅
logger.critical("Critical!")      # 50 >= 30 → OUTPUT ✅
```

### 4.3 When to Use Each Level

#### DEBUG (10)

**Purpose:** Internal information for developers only.

```python
logger.debug(f"Processing user_id={user_id}")
logger.debug(f"Query returned {len(rows)} rows")
logger.debug(f"Cache hit for key: {cache_key}")
```

**Never use in production** (too much output).

#### INFO (20)

**Purpose:** Normal application flow - things that should happen.

```python
logger.info(f"User logged in: user_id={user.id}")
logger.info("Server started on port 5500")
logger.info("Database connection established")
```

**Use for:** Startup, user actions, business events.

#### WARNING (30)

**Purpose:** Something unexpected but recoverable.

```python
logger.warning("Rate limit approaching: 90% used")
logger.warning(f"Login failed for user_id={user.id}")
logger.warning("Cache miss, falling back to database")
```

**Use for:** Auth failures, deprecation warnings, unusual situations.

#### ERROR (40)

**Purpose:** Request failed, but application continues.

```python
logger.error(f"Database query failed: {error}", exc_info=True)
logger.error("External API timeout")
logger.error("File not found: config.yaml")
```

**Use for:** Caught exceptions, failed operations.

#### CRITICAL (50)

**Purpose:** Application is broken or about to crash.

```python
logger.critical("Database connection pool exhausted!")
logger.critical("Out of memory!")
logger.critical("Required service unavailable, shutting down")
```

**Use for:** Fatal errors, system-level failures.

---

## 5. The Logging Flow

### 5.1 What Happens When You Call `logger.info()`?

```
                    logger.info("User logged in")
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 1: Level Check                                                   │
│                                                                       │
│ Is INFO (20) >= logger's level?                                       │
│   - If NO  → Stop here, message ignored                              │
│   - If YES → Continue to Step 2                                       │
└───────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: Create LogRecord                                              │
│                                                                       │
│ Python creates a LogRecord object containing:                         │
│   - message: "User logged in"                                         │
│   - level: INFO                                                       │
│   - logger name: "app.routes.users"                                   │
│   - timestamp: 2026-01-11 10:30:45.123                               │
│   - filename, lineno, funcName, etc.                                  │
└───────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 3: Pass to Handlers                                              │
│                                                                       │
│ For each handler attached to the logger:                              │
│   - Handler checks its own level filter                               │
│   - Handler passes LogRecord to its Formatter                         │
│   - Formatter converts LogRecord to string                            │
│   - Handler outputs the string to its destination                     │
└───────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 4: Output                                                        │
│                                                                       │
│ Console: 2026-01-11 10:30:45 | INFO | app.routes.users | User logged │
│ File: {"timestamp":"...","level":"INFO","message":"User logged in"}   │
└───────────────────────────────────────────────────────────────────────┘
```

### 5.2 Logger Hierarchy

Loggers form a tree based on their names (separated by dots):

```
                      Root Logger ("")
                           │
             ┌─────────────┼─────────────┐
             │             │             │
         "app"        "werkzeug"    "sqlalchemy"
             │
    ┌────────┴────────┐
    │                 │
"app.routes"     "app.utils"
    │                 │
    ├── "app.routes.users"    "app.utils.logging_config"
    └── "app.routes.main"
```

**Key Behavior:**

- If `app.routes.users` has no handlers, it passes logs UP to its parent (`app.routes`, then `app`, then root)
- You typically configure handlers on the **root logger** only
- Child loggers inherit parent's handlers

---

## 6. Our Implementation Explained

Now let's understand our `logging_config.py` implementation.

### 6.1 File Structure Overview

```python
# logging_config.py structure:

# 1. IMPORTS
import logging
import logging.handlers  # For RotatingFileHandler, etc.
# ...

# 2. CONSTANTS
SENSITIVE_FIELDS = [...]     # Fields to mask
LEVEL_COLORS = {...}         # Colors for each level
CONSOLE_FORMAT = "..."       # Format string

# 3. HELPER FUNCTIONS
def get_request_id():        # Get current request ID
def mask_sensitive_data():   # Hide passwords, tokens, etc.

# 4. CUSTOM FORMATTERS (Classes)
class JSONFormatter:         # Format logs as JSON
class RequestContextFormatter:  # Add request info to logs
class ColoredRequestContextFormatter:  # Add colors

# 5. MIDDLEWARE
def register_request_logging():  # Flask before/after request hooks

# 6. MAIN SETUP
def setup_logging():         # Configure everything

# 7. UTILITIES
def get_logger():            # Convenience function
```

### 6.2 Why Custom Formatters?

Python's built-in `Formatter` is limited:

- Can't add request ID (doesn't know about Flask)
- Can't output JSON
- Can't colorize output
- Can't mask sensitive data

So we create **custom formatter classes** that extend the built-in one.

---

## 7. Code Walkthrough

Let's go through each part of `logging_config.py`:

### 7.1 Imports

```python
import logging                  # Python's built-in logging module
import logging.handlers         # Extra handlers (RotatingFileHandler, etc.)
import json                     # For JSON formatting
import os                       # For environment variables & paths
import sys                      # For sys.stdout (console output)
from datetime import datetime, timezone  # For timestamps
from typing import Any, Dict, Optional   # Type hints
from functools import wraps     # For decorator
from flask import Flask, g, request, has_request_context  # Flask request info
import uuid                     # For generating unique request IDs
```

**Why `logging.handlers`?**
The main `logging` module includes basic handlers, but advanced handlers like `RotatingFileHandler` and `TimedRotatingFileHandler` are in `logging.handlers`.

### 7.2 Constants - Sensitive Fields

```python
SENSITIVE_FIELDS = frozenset([
    "password",
    "password_hash",
    "token",
    "access_token",
    # ... more sensitive field names
])
```

**What:** A set of field names that should NEVER appear in logs.

**Why `frozenset`?**

- `frozenset` is immutable (can't be changed accidentally)
- Lookups are O(1) - very fast for checking "is this field sensitive?"

**How It's Used:**
When logging extra data, we check each field name against this set and replace sensitive values with `***REDACTED***`.

### 7.3 Constants - ANSI Color Codes

```python
class LogColors:
    """ANSI escape codes for colorizing terminal output."""
    RESET = "\033[0m"       # Reset to default
    RED = "\033[31m"        # Red text
    GREEN = "\033[32m"      # Green text
    YELLOW = "\033[33m"     # Yellow text
    CYAN = "\033[36m"       # Cyan text
    BOLD = "\033[1m"        # Bold text
    # ...
```

**What:** ANSI escape codes that terminals understand.

**How It Works:**
When you print `\033[32mHello\033[0m`, the terminal:

1. Sees `\033[32m` → "Switch to green"
2. Prints "Hello" in green
3. Sees `\033[0m` → "Reset to default color"

**The Format:**

- `\033[` - Escape sequence start (tells terminal: "command coming")
- `32` - The color/style code
- `m` - End of escape sequence

### 7.4 Constants - Format Strings

```python
CONSOLE_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "[%(request_id)s] %(method)s %(path)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
```

**What:** Template strings that define log output format.

**The `%()s` Syntax:**
This is Python's old-style string formatting. The logging module uses this syntax:

- `%(asctime)s` → Insert the `asctime` attribute as a string
- `%(levelname)s` → Insert the `levelname` attribute as a string
- `%(name)s` → Insert the `name` attribute as a string

**Custom Attributes:**
Notice `%(request_id)s`, `%(method)s`, `%(path)s` - these aren't built-in! We add them in our custom formatter.

### 7.5 Helper Function - get_request_id()

```python
def get_request_id() -> str:
    """Get the current request ID from Flask's g object."""
    if has_request_context():           # Are we inside a Flask request?
        return getattr(g, "request_id", "unknown")  # Get g.request_id
    return "no-request"                 # Outside request context
```

**What:** Returns the current request's unique ID.

**Flask's `g` Object:**

- `g` is Flask's "request globals" - data that lives for one request
- `g.request_id` - We store the request ID here (see middleware)
- `has_request_context()` - Returns True if we're inside a request

**Why Check `has_request_context()`?**
Because code can run OUTSIDE of a request (startup, background jobs, CLI commands). In those cases, there's no `g` object, so we return `"no-request"`.

### 7.6 Helper Function - mask_sensitive_data()

```python
def mask_sensitive_data(data: Any, depth: int = 0, max_depth: int = 10) -> Any:
    """Recursively mask sensitive fields in data structures."""

    # Prevent stack overflow with deeply nested data
    if depth > max_depth:
        return "[MAX_DEPTH_EXCEEDED]"

    # Handle dictionaries
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if key_lower in SENSITIVE_FIELDS:
                masked[key] = "***REDACTED***"  # Mask the value
            else:
                masked[key] = mask_sensitive_data(value, depth + 1)  # Recurse
        return masked

    # Handle lists
    elif isinstance(data, (list, tuple)):
        return [mask_sensitive_data(item, depth + 1) for item in data]

    # Handle strings that look like tokens
    elif isinstance(data, str):
        if data.startswith(("Bearer ", "Token ")):
            return "***REDACTED***"
        return data

    # Return primitives as-is
    return data
```

**What:** Takes any data structure and replaces sensitive values with `***REDACTED***`.

**How It Works:**

1. If it's a dict → Check each key, mask if sensitive, recurse into values
2. If it's a list → Recurse into each item
3. If it's a string → Check if it looks like a token
4. Otherwise → Return as-is

**Example:**

```python
data = {
    "username": "john",
    "password": "secret123",
    "profile": {
        "api_key": "abc123"
    }
}

masked = mask_sensitive_data(data)
# Result:
# {
#     "username": "john",
#     "password": "***REDACTED***",
#     "profile": {
#         "api_key": "***REDACTED***"
#     }
# }
```

### 7.7 Custom Formatter - JSONFormatter

```python
class JSONFormatter(logging.Formatter):
    """Output logs as JSON for production/file logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a LogRecord to JSON string."""

        # Build the JSON structure
        log_dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": get_request_id(),
            "method": get_request_method(),
            "path": get_request_path(),
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_dict["exception"] = self.formatException(record.exc_info)

        # Add extra fields (and mask sensitive ones)
        # ... (see full code)

        return json.dumps(log_dict, default=str)
```

**What:** A custom formatter that outputs JSON instead of plain text.

**Key Concepts:**

1. **Inheritance:**

   ```python
   class JSONFormatter(logging.Formatter):
   ```

   We extend Python's built-in `Formatter` class.

2. **The `format()` Method:**
   This is the method Python calls to convert a `LogRecord` to a string. We override it to return JSON.

3. **`logging.LogRecord`:**
   This is a Python object containing everything about a log event:

   - `record.levelname` → "INFO", "WARNING", etc.
   - `record.name` → Logger name (e.g., "app.routes.users")
   - `record.getMessage()` → The formatted message
   - `record.exc_info` → Exception info (if `exc_info=True`)
   - `record.filename`, `record.lineno`, etc.

4. **`json.dumps()`:**
   Converts Python dict to JSON string.

### 7.8 Custom Formatter - RequestContextFormatter

```python
class RequestContextFormatter(logging.Formatter):
    """Add Flask request context to log messages."""

    def format(self, record: logging.LogRecord) -> str:
        # Add our custom attributes to the record
        record.request_id = get_request_id()
        record.method = get_request_method()
        record.path = get_request_path()

        # Call parent's format method
        return super().format(record)
```

**What:** Injects request info (request_id, method, path) into the log record.

**How It Works:**

1. When `format()` is called, we add custom attributes to the `record` object
2. These attributes can now be used in the format string: `%(request_id)s`
3. We call `super().format(record)` to do the actual formatting

**Why Add Attributes to `record`?**
The format string `%(request_id)s` looks for a `request_id` attribute on the record. By default, records don't have this - so we add it.

### 7.9 Custom Formatter - ColoredRequestContextFormatter

```python
class ColoredRequestContextFormatter(RequestContextFormatter):
    """Add colors to console output based on log level."""

    def format(self, record: logging.LogRecord) -> str:
        color = LEVEL_COLORS.get(record.levelname, "")

        if color:
            # Save original levelname
            original = record.levelname

            # Wrap levelname with color codes
            record.levelname = f"{color}{record.levelname:<8}{LogColors.RESET}"

            # Format with colored levelname
            formatted = super().format(record)

            # Restore original (in case record is reused)
            record.levelname = original

            return formatted

        return super().format(record)
```

**What:** Adds ANSI color codes to the log level in terminal output.

**Key Concepts:**

1. **Inheritance Chain:**

   ```
   ColoredRequestContextFormatter
       → extends RequestContextFormatter
           → extends logging.Formatter
   ```

2. **The `{record.levelname:<8}` Syntax:**

   - `<8` = Left-align, pad to 8 characters
   - This ensures alignment: `INFO    `, `WARNING `, `ERROR   `

3. **Why Save and Restore?**
   LogRecords might be reused. If we don't restore the original levelname, subsequent handlers might get the color-coded version (which would look wrong in files).

### 7.10 Middleware - register_request_logging()

```python
def register_request_logging(app: Flask) -> None:
    """Register Flask middleware for request logging."""

    logger = logging.getLogger("app.request")

    @app.before_request
    def log_request_start():
        """Called BEFORE each request is handled."""
        # Generate unique request ID
        g.request_id = request.headers.get(
            "X-Request-ID",
            str(uuid.uuid4())[:8]
        )

        # Store start time for duration calculation
        g.request_start_time = datetime.now(timezone.utc)

        # Log request start
        logger.info("Request started", extra={
            "remote_addr": request.remote_addr,
            "user_agent": request.user_agent.string,
            "content_length": request.content_length,
        })

    @app.after_request
    def log_request_end(response):
        """Called AFTER each request is handled."""
        # Calculate duration
        duration = datetime.now(timezone.utc) - g.request_start_time
        duration_ms = round(duration.total_seconds() * 1000, 2)

        # Choose log level based on status code
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        # Log request completion
        logger.log(log_level, "Request completed", extra={
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        })

        # Add request ID to response headers
        response.headers["X-Request-ID"] = g.request_id

        return response  # MUST return response!
```

**What:** Automatically logs every HTTP request start and end.

**Flask Request Lifecycle:**

```
Request arrives
      │
      ▼
@app.before_request  ← log_request_start() runs here
      │
      ▼
Route handler (your code)
      │
      ▼
@app.after_request   ← log_request_end() runs here
      │
      ▼
Response sent
```

**Key Concepts:**

1. **`@app.before_request`:**
   Flask decorator that registers a function to run before EVERY request.

2. **`@app.after_request`:**
   Flask decorator that runs after every request. MUST return the response.

3. **`uuid.uuid4()`:**
   Generates a random UUID like: `550e8400-e29b-41d4-a716-446655440000`
   We use `[:8]` to get just the first 8 characters: `550e8400`

4. **`extra={...}`:**
   Pass additional data to the log message. This appears in the "extra" field in JSON logs.

### 7.11 Main Setup - setup_logging()

```python
def setup_logging(app: Flask) -> None:
    """Configure the entire logging system."""

    # Determine environment & settings
    is_debug = app.debug
    log_level_str = os.environ.get("LOG_LEVEL", "DEBUG" if is_debug else "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Create logs directory
    log_dir = os.path.join(app.root_path, "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    # Get root logger (parent of all loggers)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers (prevent duplicates)
    root_logger.handlers.clear()

    # === CONSOLE HANDLER ===
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if is_debug:
        # Development: Colored human-readable
        console_formatter = ColoredRequestContextFormatter(
            fmt=CONSOLE_FORMAT, datefmt=DATE_FORMAT
        )
    else:
        # Production: JSON
        console_formatter = JSONFormatter()

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # === FILE HANDLER ===
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
        utc=True,
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Register request middleware
    register_request_logging(app)

    # Log that we're ready
    logging.getLogger("app").info("Logging initialized")
```

**Key Concepts:**

1. **Root Logger:**

   ```python
   root_logger = logging.getLogger()  # No name = root logger
   ```

   The root logger is the parent of ALL loggers. Handlers attached here receive logs from everywhere.

2. **`getattr(logging, log_level_str.upper())`:**
   This converts a string like "INFO" to the constant `logging.INFO` (which equals 20).

3. **`handlers.clear()`:**
   In Flask debug mode, the app is loaded twice. Without this, we'd get duplicate handlers and duplicate log output.

4. **`StreamHandler(sys.stdout)`:**
   Creates a handler that writes to the console (stdout).

5. **`TimedRotatingFileHandler`:**
   Creates a handler that:

   - Writes to a file
   - Rotates at midnight UTC
   - Keeps 30 days of logs
   - Names old files like `app.log.2026-01-11`

6. **Suppressing Noisy Loggers:**
   ```python
   logging.getLogger("werkzeug").setLevel(logging.WARNING)
   ```
   Flask's web server (werkzeug) logs every request at INFO level. We set it to WARNING to reduce noise.

---

## 8. Quick Reference

### 8.1 Common Logging Methods

```python
import logging
logger = logging.getLogger(__name__)

# Basic logging at different levels
logger.debug("For developers only")
logger.info("Normal operation")
logger.warning("Something might be wrong")
logger.error("Something failed")
logger.critical("Application is broken")

# Log with exception traceback
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True)
    # exc_info=True adds the full stack trace

# Log with extra data
logger.info("User action", extra={
    "user_id": 42,
    "action": "login"
})

# Log at a specific level (dynamic)
level = logging.WARNING
logger.log(level, "Dynamic level logging")
```

### 8.2 Common Handler Types

```python
import logging
import logging.handlers

# Console (stdout)
handler1 = logging.StreamHandler(sys.stdout)

# Fixed file
handler2 = logging.FileHandler("app.log")

# File with size rotation (max 10MB, keep 5 backups)
handler3 = logging.handlers.RotatingFileHandler(
    "app.log", maxBytes=10*1024*1024, backupCount=5
)

# File with daily rotation
handler4 = logging.handlers.TimedRotatingFileHandler(
    "app.log", when="midnight", backupCount=30
)
```

### 8.3 Flow Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                         THE COMPLETE FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. App starts → setup_logging() called                             │
│     └── Creates handlers, formatters, registers middleware         │
│                                                                     │
│  2. Request arrives                                                 │
│     └── @before_request: Generate request_id, log "Request started"│
│                                                                     │
│  3. Your code runs                                                  │
│     └── logger.info("Something")                                    │
│         └── Check level → Create LogRecord → Pass to handlers       │
│             └── Console handler: Format with colors → Print        │
│             └── File handler: Format as JSON → Write to file       │
│                                                                     │
│  4. Response ready                                                  │
│     └── @after_request: Log "Request completed" with duration      │
│                                                                     │
│  5. At midnight UTC                                                 │
│     └── File handler rotates: app.log → app.log.2026-01-11         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

You now understand:

- ✅ What logging is and why it's better than print()
- ✅ Python's built-in logging module
- ✅ The four components: Logger, Handler, Formatter, Filter
- ✅ The five log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ How our custom formatters work
- ✅ How request middleware provides correlation
- ✅ How everything connects together

The logging system is now production-ready with:

- Colorized console output in development
- JSON file logging with daily rotation
- Request ID correlation
- Sensitive data masking
- Proper log levels throughout

Happy logging! 🚀
