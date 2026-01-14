"""
Global Error Handlers for Flask Application.

This module registers global error handlers to ensure that ALL errors
(including unhandled exceptions) return responses in the standard format.

Why Global Error Handlers?
--------------------------
1. **Consistency**: Even unexpected errors follow the same format
2. **Security**: Prevents leaking stack traces to API consumers
3. **Debugging**: Logs detailed info server-side, returns safe info to client
4. **UX**: Users always get machine-parseable error responses

Error Handler Registration:
---------------------------
Call `register_error_handlers(app)` in your application factory to register
all handlers. This should be done after initializing extensions but before
returning the app.

How Flask Error Handlers Work:
------------------------------
Flask allows registering functions to handle specific HTTP error codes
or exception types. When an error occurs:

1. Flask looks for a handler matching the exact error code/type
2. If found, the handler is called with the error object
3. The handler returns a Response (must be standard format)
4. If no handler found, Flask uses its default error page

Our Approach:
-------------
- Register handlers for common HTTP errors (400, 401, 403, 404, 405, 500)
- Register a catch-all handler for Exception
- Register handlers for Werkzeug HTTP exceptions
- Register handler for Pydantic validation errors (flask-openapi3)

Flow Diagram:
    ┌─────────────────────────────────────────────────────────────┐
    │                     HTTP Request                            │
    └─────────────────────────────────────────────────────────────┘
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    Flask Routing                            │
    └─────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
            ┌───────────────┐       ┌───────────────┐
            │  Route Found  │       │ Route Not     │
            │               │       │ Found (404)   │
            └───────┬───────┘       └───────┬───────┘
                    │                       │
                    ▼                       ▼
            ┌───────────────┐       ┌───────────────┐
            │ Route Handler │       │ 404 Handler   │
            └───────┬───────┘       │               │
                    │               │ Returns:      │
            ┌───────┴───────┐       │ {             │
            │               │       │  success:false│
            ▼               ▼       │  error:{...}  │
    ┌───────────────┐ ┌─────────────┐ }             │
    │   Success     │ │  Exception  │└───────────────┘
    │               │ │   Raised    │
    └───────────────┘ └──────┬──────┘
                             │
                             ▼
                    ┌───────────────┐
                    │ Error Handler │
                    │               │
                    │ Returns:      │
                    │ {             │
                    │  success:false│
                    │  error:{...}  │
                    │ }             │
                    └───────────────┘
"""

import logging

from flask import Flask, jsonify, make_response
from pydantic import ValidationError

# SQLAlchemy exception imports for database error handling
# These allow us to catch specific database errors and provide user-friendly messages
from sqlalchemy.exc import DataError  # Invalid data for column type
from sqlalchemy.exc import IntegrityError  # Constraint violations (unique, foreign key, etc.)
from sqlalchemy.exc import OperationalError  # Database connection issues
from sqlalchemy.exc import ProgrammingError  # SQL syntax errors, missing tables, etc.
from sqlalchemy.exc import SQLAlchemyError  # Base class for all SQLAlchemy exceptions
from werkzeug.exceptions import HTTPException

# RBAC exception imports for access control error handling
from app.rbac.exceptions import (
    DirectPermissionError,
    PermissionDeniedError,
    PermissionNotFoundError,
    RBACError,
    RoleAssignmentError,
    RoleNotFoundError,
    SystemRoleError,
)
from app.utils.responses import ErrorCode, error_response

# Configure logging for error handlers
logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Validation Error Callback (for flask-openapi3)
# =============================================================================


def pydantic_validation_error_callback(error: ValidationError):
    """
    Custom callback for handling Pydantic validation errors in flask-openapi3.

    This ensures validation errors return responses in our standard envelope format
    instead of the raw Pydantic error format.

    Why This Exists:
    ----------------
    flask-openapi3 validates request bodies using Pydantic BEFORE the request
    reaches your route handler. If validation fails, it calls this callback
    instead of raising an exception.

    This is DIFFERENT from Flask's @app.errorhandler because:
    - @app.errorhandler catches exceptions AFTER they're raised
    - This callback is called INSTEAD OF raising an exception

    IMPORTANT: flask-openapi3 expects this callback to return a Response object
    directly (not a tuple), which it will return to the client.

    Args:
        error: The Pydantic ValidationError instance

    Returns:
        Flask Response object with proper status code

    Example:
        If a request sends {"username": ""}, Pydantic might raise:
        ValidationError with errors like:
        [
            {
                "loc": ("body", "username"),
                "msg": "String should have at least 3 characters",
                "type": "string_too_short"
            }
        ]

        This callback converts it to:
        {
            "success": false,
            "data": null,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {
                    "username": "String should have at least 3 characters"
                }
            }
        }
    """
    # Transform Pydantic errors to our format
    details = {}
    for err in error.errors():
        # Get field name from location tuple
        loc = err.get("loc", ())
        # Skip 'body' in location, take the actual field name
        field = ".".join(str(loc_part) for loc_part in loc if loc_part != "body") or "unknown"
        message = err.get("msg", "Validation failed")

        if field in details:
            # Multiple errors for same field
            if isinstance(details[field], list):
                details[field].append(message)
            else:
                details[field] = [details[field], message]
        else:
            details[field] = message

    # Log the validation error
    logger.warning(f"Pydantic validation failed: {details}")

    # Build the response body in our standard format
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

    # Create and return a proper Response object with 422 status
    response = make_response(jsonify(response_body), 422)
    return response


def register_error_handlers(app: Flask) -> None:
    """
    Register all global error handlers with the Flask app.

    This function should be called in the application factory after
    initializing extensions.

    Args:
        app: The Flask application instance

    Usage:
        def create_app():
            app = Flask(__name__)
            # ... initialize extensions ...
            register_error_handlers(app)
            return app
    """

    # =========================================================================
    # HTTP Error Handlers (4xx, 5xx)
    # =========================================================================

    @app.errorhandler(400)
    def handle_bad_request(error):
        """
        Handle 400 Bad Request errors.

        Triggered when:
        - Invalid JSON in request body
        - Missing required headers
        - Malformed request syntax
        """
        logger.warning(f"Bad Request: {error}")
        return error_response(
            code=ErrorCode.BAD_REQUEST,
            message=(str(error.description) if hasattr(error, "description") else "Bad request"),
            status_code=400,
        )

    @app.errorhandler(401)
    def handle_unauthorized(error):
        """
        Handle 401 Unauthorized errors.

        Triggered when:
        - Missing authentication token
        - Invalid token
        - Token expired
        """
        logger.warning(f"Unauthorized: {error}")
        return error_response(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication required",
            status_code=401,
        )

    @app.errorhandler(403)
    def handle_forbidden(error):
        """
        Handle 403 Forbidden errors.

        Triggered when:
        - User authenticated but lacks permission
        - Resource access denied
        """
        logger.warning(f"Forbidden: {error}")
        return error_response(
            code=ErrorCode.FORBIDDEN,
            message="You do not have permission to access this resource",
            status_code=403,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        """
        Handle 404 Not Found errors.

        Triggered when:
        - Route doesn't exist
        - Resource not found in database
        - get_or_404() fails
        """
        logger.info(f"Not Found: {error}")
        return error_response(
            code=ErrorCode.NOT_FOUND,
            message="The requested resource was not found",
            status_code=404,
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """
        Handle 405 Method Not Allowed errors.

        Triggered when:
        - POST to a GET-only endpoint
        - DELETE to a read-only resource
        """
        logger.warning(f"Method Not Allowed: {error}")
        return error_response(
            code=ErrorCode.METHOD_NOT_ALLOWED,
            message="Method not allowed for this endpoint",
            status_code=405,
        )

    @app.errorhandler(409)
    def handle_conflict(error):
        """
        Handle 409 Conflict errors.

        Triggered when:
        - Duplicate unique constraint
        - Resource state conflict
        """
        logger.warning(f"Conflict: {error}")
        return error_response(
            code=ErrorCode.CONFLICT,
            message=(
                str(error.description) if hasattr(error, "description") else "Resource conflict"
            ),
            status_code=409,
        )

    @app.errorhandler(422)
    def handle_unprocessable_entity(error):
        """
        Handle 422 Unprocessable Entity errors.

        Triggered when:
        - Request syntax is valid but semantically incorrect
        - Validation fails (Pydantic, custom validators)
        """
        # Extract details if available (from flask-openapi3 validation)
        details = None
        if hasattr(error, "description") and isinstance(error.description, dict):
            details = error.description

        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed",
            details=details,
            status_code=422,
        )

    @app.errorhandler(429)
    def handle_rate_limit(error):
        """
        Handle 429 Too Many Requests errors.

        Triggered when:
        - Rate limiting is exceeded
        """
        logger.warning(f"Rate Limit Exceeded: {error}")
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message="Too many requests. Please try again later.",
            status_code=429,
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        """
        Handle 500 Internal Server Error.

        Triggered when:
        - Unhandled exception in code
        - Database errors
        - External service failures

        SECURITY: Never expose stack traces to clients in production!
        """
        logger.error(f"Internal Server Error: {error}", exc_info=True)

        # In development, include more details
        # In production, return generic message
        message = "An internal error occurred"
        details = None

        if app.debug:
            # Only in development - include error details
            message = str(error)

        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=message,
            details=details,
            status_code=500,
        )

    # =========================================================================
    # Generic Exception Handlers
    # =========================================================================

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        """
        Handle all Werkzeug HTTPException subclasses.

        This is a catch-all for any HTTP exceptions not explicitly handled above.
        Werkzeug raises these for various HTTP errors.
        """
        logger.warning(f"HTTP Exception: {error.code} - {error.description}")

        # Map HTTP status codes to error codes
        code_map = {
            400: ErrorCode.BAD_REQUEST,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            405: ErrorCode.METHOD_NOT_ALLOWED,
            409: ErrorCode.CONFLICT,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR,
        }

        error_code = code_map.get(error.code, ErrorCode.INTERNAL_ERROR)

        return error_response(
            code=error_code,
            message=error.description or "An error occurred",
            status_code=error.code or 500,
        )

    @app.errorhandler(ValidationError)
    def handle_pydantic_validation_error(error: ValidationError):
        """
        Handle Pydantic ValidationError.

        flask-openapi3 uses Pydantic for validation. When validation fails,
        it raises a Pydantic ValidationError. This handler converts it to
        our standard error format.

        The error.errors() method returns a list of dicts like:
        [
            {
                'type': 'string_too_short',
                'loc': ('body', 'password'),
                'msg': 'String should have at least 8 characters',
                'input': 'short',
                ...
            }
        ]
        """
        logger.info(f"Pydantic Validation Error: {error}")

        # Transform Pydantic errors to our format
        details = {}
        for err in error.errors():
            # Get field name from location tuple
            loc = err.get("loc", ())
            # Skip 'body' in location, take the actual field name
            field = ".".join(str(loc_part) for loc_part in loc if loc_part != "body") or "unknown"
            message = err.get("msg", "Validation failed")

            if field in details:
                # Multiple errors for same field
                if isinstance(details[field], list):
                    details[field].append(message)
                else:
                    details[field] = [details[field], message]
            else:
                details[field] = message

        return error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed",
            details=details,
            status_code=422,
        )

    # =========================================================================
    # RBAC Error Handlers
    # =========================================================================
    # These handlers catch RBAC-specific exceptions and return appropriate
    # HTTP status codes with user-friendly messages.
    # =========================================================================

    @app.errorhandler(PermissionDeniedError)
    def handle_permission_denied(error: PermissionDeniedError):
        """
        Handle permission denied errors from RBAC checks.

        Triggered when:
        - User lacks required permission for an operation
        - @permission_required decorator check fails
        """
        logger.warning(
            f"Permission denied: {error.message}",
            extra={
                "error_type": "PermissionDeniedError",
                "required_permissions": error.required_permissions,
            },
        )

        return error_response(
            code=ErrorCode.FORBIDDEN,
            message=error.message,
            details=(
                {"required_permissions": error.required_permissions}
                if error.required_permissions
                else None
            ),
            status_code=403,
        )

    @app.errorhandler(RoleNotFoundError)
    def handle_role_not_found(error: RoleNotFoundError):
        """
        Handle role not found errors.

        Triggered when:
        - Requested role doesn't exist
        - Role lookup fails
        """
        logger.info(
            f"Role not found: {error.message}",
            extra={
                "error_type": "RoleNotFoundError",
                "role_name": error.role_name,
                "role_id": error.role_id,
            },
        )

        return error_response(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=error.message,
            status_code=404,
        )

    @app.errorhandler(PermissionNotFoundError)
    def handle_permission_not_found(error: PermissionNotFoundError):
        """
        Handle permission not found errors.

        Triggered when:
        - Requested permission doesn't exist
        - Permission lookup fails
        """
        logger.info(
            f"Permission not found: {error.message}",
            extra={
                "error_type": "PermissionNotFoundError",
                "permission_name": error.permission_name,
            },
        )

        return error_response(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=error.message,
            status_code=404,
        )

    @app.errorhandler(RoleAssignmentError)
    def handle_role_assignment_error(error: RoleAssignmentError):
        """
        Handle role assignment/revocation errors.

        Triggered when:
        - User already has the role being assigned
        - User doesn't have the role being revoked
        - Role name already exists (when creating)
        """
        logger.warning(
            f"Role assignment error: {error.message}",
            extra={
                "error_type": "RoleAssignmentError",
                "user_id": error.user_id,
                "role_name": error.role_name,
            },
        )

        return error_response(
            code=ErrorCode.BAD_REQUEST,
            message=error.message,
            status_code=400,
        )

    @app.errorhandler(SystemRoleError)
    def handle_system_role_error(error: SystemRoleError):
        """
        Handle system role protection errors.

        Triggered when:
        - Attempting to delete a system role
        - Attempting to modify protected system role
        """
        logger.warning(
            f"System role error: {error.message}",
            extra={
                "error_type": "SystemRoleError",
                "role_name": error.role_name,
            },
        )

        return error_response(
            code=ErrorCode.FORBIDDEN,
            message=error.message,
            status_code=403,
        )

    @app.errorhandler(DirectPermissionError)
    def handle_direct_permission_error(error: DirectPermissionError):
        """
        Handle direct permission assignment errors.

        Triggered when:
        - User already has the direct permission
        - User doesn't have the direct permission being revoked
        """
        logger.warning(
            f"Direct permission error: {error.message}",
            extra={
                "error_type": "DirectPermissionError",
                "user_id": error.user_id,
                "permission_name": error.permission_name,
            },
        )

        return error_response(
            code=ErrorCode.BAD_REQUEST,
            message=error.message,
            status_code=400,
        )

    @app.errorhandler(RBACError)
    def handle_generic_rbac_error(error: RBACError):
        """
        Catch-all for any RBAC errors not handled above.

        This ensures no raw RBAC errors ever reach the client.
        More specific handlers above take precedence.
        """
        logger.error(
            f"Unhandled RBAC Error: {error.message}",
            extra={
                "error_type": type(error).__name__,
                "error_code": error.code,
            },
        )

        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="An access control error occurred. Please try again later.",
            status_code=500,
        )

    # =========================================================================
    # Database Error Handlers (SQLAlchemy)
    # =========================================================================
    # These handlers catch specific database exceptions and return user-friendly
    # messages. Technical details are NEVER exposed to clients (security risk).
    #
    # Why specific handlers?
    # 1. Better UX: "Database unavailable" vs raw SQL error
    # 2. Security: Never expose table names, SQL queries, or schema
    # 3. Debugging: Full details are logged server-side
    # =========================================================================

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error: IntegrityError):
        """
        Handle database integrity constraint violations.

        Triggered when:
        - Unique constraint violation (duplicate email, username, etc.)
        - Foreign key constraint violation (referencing non-existent record)
        - NOT NULL constraint violation
        - Check constraint violation

        Common examples:
        - User tries to register with existing email
        - Deleting a record that has dependent records
        """
        # Log full technical details for debugging
        logger.error(
            "Database IntegrityError",
            exc_info=True,
            extra={
                "error_type": type(error).__name__,
                "original_error": str(error.orig) if error.orig else None,
            },
        )

        # Provide helpful but safe message based on error type
        # Note: We never expose the actual constraint name or table
        if error.orig:
            orig_message = str(error.orig).lower()

            if "unique" in orig_message or "duplicate" in orig_message:
                message = "A record with this information already exists"
            elif "foreign key" in orig_message or "fk_" in orig_message:
                message = "Referenced record does not exist"
            elif "not null" in orig_message or "notnull" in orig_message:
                message = "Required information is missing"
            else:
                message = "The operation could not be completed due to a data conflict"
        else:
            message = "The operation could not be completed due to a data conflict"

        return error_response(
            code=ErrorCode.CONFLICT,
            message=message,
            status_code=409,
        )

    @app.errorhandler(OperationalError)
    def handle_operational_error(error: OperationalError):
        """
        Handle database connection and operational errors.

        Triggered when:
        - Database server is down or unreachable
        - Connection pool exhausted
        - Connection timeout
        - Authentication failure to database

        This is a CRITICAL error - the database is unavailable.
        """
        # Log with CRITICAL level as this affects all users
        logger.critical(
            "Database OperationalError - Database may be unavailable",
            exc_info=True,
            extra={
                "error_type": type(error).__name__,
                "original_error": str(error.orig) if error.orig else None,
            },
        )

        return error_response(
            code=ErrorCode.DATABASE_ERROR,
            message="The service is temporarily unavailable. Please try again later.",
            status_code=503,  # Service Unavailable
        )

    @app.errorhandler(ProgrammingError)
    def handle_programming_error(error: ProgrammingError):
        """
        Handle SQL programming errors.

        Triggered when:
        - Table or column doesn't exist (missing migrations)
        - Invalid SQL syntax
        - Invalid column type operations
        - Schema mismatch

        This usually indicates a deployment or migration issue.
        """
        # Log with ERROR level - this is a developer/deployment issue
        logger.error(
            "Database ProgrammingError - Possible schema mismatch or missing migrations",
            exc_info=True,
            extra={
                "error_type": type(error).__name__,
                "original_error": str(error.orig) if error.orig else None,
                "hint": "Run 'flask db upgrade' to apply pending migrations",
            },
        )

        # User-friendly message - don't expose "table doesn't exist"
        return error_response(
            code=ErrorCode.DATABASE_ERROR,
            message="The service encountered a configuration error. Please try again later.",
            status_code=500,
        )

    @app.errorhandler(DataError)
    def handle_data_error(error: DataError):
        """
        Handle data type errors.

        Triggered when:
        - Value too long for column (e.g., 1000 chars in VARCHAR(255))
        - Invalid data type conversion
        - Numeric overflow
        """
        logger.error(
            "Database DataError - Invalid data for column type",
            exc_info=True,
            extra={
                "error_type": type(error).__name__,
                "original_error": str(error.orig) if error.orig else None,
            },
        )

        return error_response(
            code=ErrorCode.BAD_REQUEST,
            message="The provided data could not be processed. Please check your input.",
            status_code=400,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error: SQLAlchemyError):
        """
        Catch-all for any other SQLAlchemy errors not handled above.

        This ensures no raw SQL errors ever reach the client.
        More specific handlers above take precedence.
        """
        logger.error(
            f"Unhandled SQLAlchemy Error: {type(error).__name__}",
            exc_info=True,
            extra={
                "error_type": type(error).__name__,
            },
        )

        return error_response(
            code=ErrorCode.DATABASE_ERROR,
            message="A database error occurred. Please try again later.",
            status_code=500,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception):
        """
        Catch-all handler for any unhandled exceptions.

        This is the last line of defense. ANY exception not caught
        by more specific handlers will end up here.

        SECURITY: NEVER expose internal error details to clients!
        -----------
        Even in debug mode, we don't expose raw exception messages because:
        1. They may contain sensitive info (file paths, SQL, configs)
        2. They help attackers understand your system
        3. They're not useful for users anyway

        Instead, we log everything server-side where developers can see it.
        """
        logger.error(
            f"Unhandled Exception: {type(error).__name__}: {error}",
            exc_info=True,
            extra={
                "error_type": type(error).__name__,
            },
        )

        # NEVER expose raw error messages to clients
        # Even in debug mode - use the logs for debugging
        message = "An unexpected error occurred. Please try again later."

        # In debug mode, we can add the exception TYPE (not the message)
        # This helps developers identify the issue class without exposing details
        if app.debug:
            error_type = type(error).__name__
            message = f"An unexpected error occurred ({error_type}). Check logs."

        return error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=message,
            status_code=500,
        )

    logger.info("Global error handlers registered successfully")
