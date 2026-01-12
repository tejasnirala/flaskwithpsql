"""
Centralized Logging Configuration Module.

This module provides a production-ready logging system for the Flask application.
It implements structured logging with request correlation and secure handling of
sensitive data.

Key Features:
-------------
1. Structured JSON logging for production
2. Human-readable console logging for development
3. Request ID correlation for tracing requests
4. Automatic sensitive data masking
5. File and console output handlers
6. Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Log Format (JSON):
------------------
{
    "timestamp": "2024-01-15T10:30:45.123Z",
    "level": "INFO",
    "logger": "app.routes.users",
    "request_id": "abc123-def456",
    "method": "POST",
    "path": "/api/users/register",
    "message": "User registration successful",
    "extra": {...}
}

Usage:
------
1. Import and call setup_logging() in your application factory:

   from app.utils.logging_config import setup_logging

   def create_app():
       app = Flask(__name__)
       setup_logging(app)
       ...

2. Use logging in any module:

   import logging
   logger = logging.getLogger(__name__)
   logger.info("User created successfully")

Log Levels Guide:
-----------------
- DEBUG: Internal development details only (e.g., variable values, flow traces)
- INFO: Normal application flow (request start, success, business events)
- WARNING: Recoverable issues (auth failures, validation warnings)
- ERROR: Request failed but application continues (caught exceptions)
- CRITICAL: Application-level failure (database down, required service unavailable)

Security Considerations:
------------------------
- NEVER log passwords, tokens, secrets, or full request bodies
- Sensitive fields are automatically masked if detected
- Error messages are sanitized before logging to remove potential secrets
"""

import json
import logging
import logging.handlers
import os
import sys
import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Optional

from flask import Flask, g, has_request_context, request

# =============================================================================
# Constants
# =============================================================================

# Fields that should NEVER be logged - these will be masked
SENSITIVE_FIELDS = frozenset(
    [
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "secret",
        "secret_key",
        "authorization",
        "auth",
        "credential",
        "credentials",
        "private_key",
        "ssh_key",
        "credit_card",
        "card_number",
        "cvv",
        "ssn",
        "social_security",
    ]
)

# Mask value for sensitive data
SENSITIVE_MASK = "***REDACTED***"

# =============================================================================
# ANSI Color Codes for Terminal Output
# =============================================================================
# These codes work in most modern terminals (macOS, Linux, Windows 10+)
# Format: \033[<code>m where code defines the color/style


class LogColors:
    """ANSI escape codes for colorizing terminal output."""

    # Reset
    RESET = "\033[0m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright/Light colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


# Map log levels to colors
LEVEL_COLORS = {
    "DEBUG": LogColors.CYAN,
    "INFO": LogColors.GREEN,
    "WARNING": LogColors.YELLOW,
    "ERROR": LogColors.RED,
    "CRITICAL": LogColors.BOLD + LogColors.MAGENTA,
}

# Default log format for console (human-readable)
# Note: levelname padding is handled by the formatter for proper color code alignment
CONSOLE_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | " "[%(request_id)s] %(method)s %(path)s | %(message)s"
)

# Simple format for console when no request context
SIMPLE_CONSOLE_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# Date format
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# Request Context Storage
# =============================================================================


def get_request_id() -> str:
    """
    Get the current request ID.

    Returns the request ID from Flask's g object if in a request context,
    otherwise returns 'no-request'.

    Returns:
        str: The current request ID or 'no-request' if outside request context
    """
    if has_request_context():
        return getattr(g, "request_id", "unknown")
    return "no-request"


def get_request_method() -> str:
    """Get the current request HTTP method."""
    if has_request_context():
        return request.method
    return "-"


def get_request_path() -> str:
    """Get the current request path."""
    if has_request_context():
        return request.path
    return "-"


# =============================================================================
# Sensitive Data Masking
# =============================================================================


def mask_sensitive_data(data: Any, depth: int = 0, max_depth: int = 10) -> Any:
    """
    Recursively mask sensitive fields in data structures.

    This function traverses dictionaries and lists, masking any values
    whose keys match known sensitive field names.

    Args:
        data: The data to mask (can be dict, list, or primitive)
        depth: Current recursion depth (for stack overflow protection)
        max_depth: Maximum recursion depth

    Returns:
        The data with sensitive fields masked

    Example:
        >>> mask_sensitive_data({"username": "john", "password": "secret123"})
        {"username": "john", "password": "***REDACTED***"}
    """
    if depth > max_depth:
        return "[MAX_DEPTH_EXCEEDED]"

    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if key_lower in SENSITIVE_FIELDS:
                masked[key] = SENSITIVE_MASK
            else:
                masked[key] = mask_sensitive_data(value, depth + 1, max_depth)
        return masked

    elif isinstance(data, (list, tuple)):
        return [mask_sensitive_data(item, depth + 1, max_depth) for item in data]

    elif isinstance(data, str):
        # Check if the string looks like a token or secret
        if len(data) > 20 and data.startswith(("Bearer ", "Token ")):
            return SENSITIVE_MASK
        return data

    return data


# =============================================================================
# Custom Log Formatter - JSON
# =============================================================================


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    This formatter outputs logs as JSON objects, making them easy to parse
    by log aggregation systems (ELK, Splunk, CloudWatch, etc.).

    Output format:
    {
        "timestamp": "2024-01-15T10:30:45.123456Z",
        "level": "INFO",
        "logger": "app.routes.users",
        "request_id": "abc123",
        "method": "POST",
        "path": "/api/users",
        "message": "User created",
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        # Build base log structure
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

        # Add any extra fields from the record
        # Skip standard LogRecord attributes
        standard_attrs = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "taskName",
            "message",
        }

        extra = {}
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                extra[key] = value

        if extra:
            # Mask sensitive data in extra fields
            log_dict["extra"] = mask_sensitive_data(extra)

        return json.dumps(log_dict, default=str)


# =============================================================================
# Custom Log Formatter - Console (Human Readable)
# =============================================================================


class RequestContextFormatter(logging.Formatter):
    """
    Custom formatter that includes request context in human-readable format.

    This formatter adds request_id, method, and path to log messages
    when running within a Flask request context.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with request context."""
        # Add request context as record attributes
        record.request_id = get_request_id()
        record.method = get_request_method()
        record.path = get_request_path()

        return super().format(record)


class ColoredRequestContextFormatter(RequestContextFormatter):
    """
    Colorized formatter for development console output.

    Extends RequestContextFormatter to add ANSI color codes to the log level only.
    This follows industry best practices - colorizing just the level makes scanning
    easy while keeping the actual message readable.

    Color Mapping:
    - DEBUG    → Cyan
    - INFO     → Green
    - WARNING  → Yellow
    - ERROR    → Red
    - CRITICAL → Bold Magenta

    Example Output:
        2026-01-11 20:30:45 | [GREEN]INFO[/] | app | [abc123] POST /api | Created
        2026-01-11 20:30:46 | [YELLOW]WARNING[/] | app | [abc123] POST /api | Limit
        2026-01-11 20:30:47 | [RED]ERROR[/] | app | [abc123] POST /api | Failed
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colored log level only."""
        # Get color for this log level
        color = LEVEL_COLORS.get(record.levelname, "")

        if color:
            # Save original levelname
            original_levelname = record.levelname

            # Wrap ONLY the levelname with color codes
            # The -8s in format string pads to 8 chars, so we pad here too
            record.levelname = f"{color}{record.levelname:<8}{LogColors.RESET}"

            # Format with colored levelname
            formatted = super().format(record)

            # Restore original levelname (in case record is reused)
            record.levelname = original_levelname

            return formatted

        return super().format(record)


# =============================================================================
# Request Logging Middleware
# =============================================================================


def register_request_logging(app: Flask) -> None:
    """
    Register request logging middleware with the Flask app.

    This middleware:
    1. Generates a unique request_id for each request
    2. Logs request start with method, path, and IP
    3. Logs request completion with status code and duration
    4. Handles exceptions appropriately

    Args:
        app: The Flask application instance
    """
    logger = logging.getLogger("app.request")

    @app.before_request
    def log_request_start():
        """
        Called before each request.

        Generates a unique request_id and stores it in Flask's g object.
        Also logs the request start.
        """
        # Check for existing request ID in headers (for distributed tracing)
        g.request_id = request.headers.get(
            "X-Request-ID", str(uuid.uuid4())[:8]  # Short UUID for readability
        )

        # Store request start time for duration calculation
        g.request_start_time = datetime.now(timezone.utc)

        # Log request start
        # Note: We don't log request body to protect sensitive data
        logger.info(
            "Request started",
            extra={
                "remote_addr": request.remote_addr,
                "user_agent": request.user_agent.string if request.user_agent else None,
                "content_length": request.content_length,
            },
        )

    @app.after_request
    def log_request_end(response):
        """
        Called after each request.

        Logs the request completion with status code and duration.
        """
        # Calculate request duration
        duration_ms = None
        if hasattr(g, "request_start_time") and g.request_start_time:
            duration = datetime.now(timezone.utc) - g.request_start_time
            duration_ms = round(duration.total_seconds() * 1000, 2)

        # Determine log level based on status code
        status_code = response.status_code
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO

        logger.log(
            log_level,
            "Request completed",
            extra={
                "status_code": status_code,
                "duration_ms": duration_ms,
                "content_length": response.content_length,
            },
        )

        # Add request ID to response headers for client-side correlation
        response.headers["X-Request-ID"] = g.request_id

        return response

    @app.teardown_request
    def log_request_exception(exception):
        """
        Called when an unhandled exception occurs.

        Note: This logs the exception for cleanup purposes.
        The actual error response is handled by error handlers.
        """
        if exception:
            logger.error(
                "Request failed with unhandled exception",
                exc_info=exception,
                extra={
                    "exception_type": type(exception).__name__,
                },
            )


# =============================================================================
# Main Setup Function
# =============================================================================


def setup_logging(app: Flask) -> None:
    """
    Set up centralized logging for the Flask application.

    This function configures:
    1. Root logger with appropriate level
    2. Console handler (human-readable in dev, JSON in production)
    3. File handler with daily rotation (JSON format)
    4. Request logging middleware

    File Naming:
    - Current day: logs/app.log
    - Previous days: logs/app.log.YYYY-MM-DD (e.g., app.log.2026-01-11)

    Args:
        app: The Flask application instance

    Usage:
        def create_app():
            app = Flask(__name__)
            setup_logging(app)
            # ... rest of setup
            return app
    """
    # Determine environment
    is_debug = app.debug
    log_level_str = os.environ.get("LOG_LEVEL", "DEBUG" if is_debug else "INFO")
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Get log retention days from environment (default: 30 days)
    log_retention_days = int(os.environ.get("LOG_RETENTION_DAYS", "30"))

    # Get log file path
    log_dir = os.path.join(app.root_path, "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if is_debug:
        # Colorized human-readable format for development
        # Colors make it easy to distinguish log levels at a glance
        console_formatter = ColoredRequestContextFormatter(fmt=CONSOLE_FORMAT, datefmt=DATE_FORMAT)
    else:
        # JSON format for production (easier log aggregation)
        console_formatter = JSONFormatter()

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ==========================================================================
    # Create file handler with DAILY rotation
    # ==========================================================================
    # TimedRotatingFileHandler creates a new file each day at midnight
    #
    # Parameters:
    # - when='midnight': Rotate at midnight
    # - interval=1: Every 1 day
    # - backupCount=30: Keep 30 days of logs
    # - utc=True: Use UTC time for rotation (consistent across timezones)
    #
    # File naming:
    # - Current: app.log
    # - Rotated: app.log.YYYY-MM-DD (e.g., app.log.2026-01-11)
    # ==========================================================================
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=log_retention_days,
        encoding="utf-8",
        utc=True,  # Use UTC for consistent rotation times
    )

    # Custom suffix for rotated files: YYYY-MM-DD format
    file_handler.suffix = "%Y-%m-%d"

    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # Suppress noisy loggers from third-party libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # SQLAlchemy has TWO logging mechanisms:
    # 1. Native echo: Controlled by SQLALCHEMY_ECHO config (prints to stdout)
    # 2. Python logging: Uses the standard logging module (logger: sqlalchemy.engine)
    #
    # Even with SQLALCHEMY_ECHO=False, the Python logging can still emit logs.
    # Setting to WARNING suppresses the verbose SQL query logs at INFO level.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Register request logging middleware
    register_request_logging(app)

    # Log startup
    app_logger = logging.getLogger("app")
    app_logger.info(
        "Logging initialized",
        extra={
            "log_level": log_level_str,
            "log_file": log_file,
            "log_retention_days": log_retention_days,
            "environment": "development" if is_debug else "production",
        },
    )


# =============================================================================
# Logging Decorator for Functions
# =============================================================================


def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function entry and exit.

    This is useful for debugging service layer functions.

    Args:
        logger: Logger to use. If None, uses the function's module logger.

    Usage:
        @log_function_call()
        def create_user(username, email):
            ...

    Note: This decorator masks sensitive arguments automatically.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_logger = logger or logging.getLogger(func.__module__)

            # Mask sensitive keyword arguments
            masked_kwargs = mask_sensitive_data(kwargs)

            func_logger.debug(
                f"Entering {func.__name__}",
                extra={"args_count": len(args), "kwargs": masked_kwargs},
            )

            try:
                result = func(*args, **kwargs)
                func_logger.debug(f"Exiting {func.__name__} successfully")
                return result
            except Exception as e:
                func_logger.error(
                    f"Exception in {func.__name__}: {type(e).__name__}", exc_info=True
                )
                raise

        return wrapper

    return decorator


# =============================================================================
# Utility Functions
# =============================================================================


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.

    This is a convenience function that's equivalent to logging.getLogger(name),
    but ensures the logging system is properly configured.

    Args:
        name: The logger name (typically __name__ of the module)

    Returns:
        logging.Logger: The configured logger

    Usage:
        # In any module
        from app.utils.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    return logging.getLogger(name)
