"""
Standardized API Response Utilities.

This module provides centralized helper functions and schemas for generating
consistent API responses across the entire application.

Standard Response Envelope Format:
----------------------------------
{
    "success": boolean,        # True for success, False for errors
    "data": object|array|null, # Response payload (null on error)
    "error": {                 # Error details (null on success)
        "code": string,        # Machine-readable error code
        "message": string,     # Human-readable error message
        "details": object      # Optional field-level errors
    } | null,
    "meta": {                  # Optional metadata
        "page": int,
        "total": int,
        "request_id": string,
        ...
    } | null
}

Why Standardize Responses?
--------------------------
1. **Predictability**: Frontend can rely on consistent structure
2. **Error Handling**: Unified error format makes debugging easier
3. **API Contracts**: Clear documentation for API consumers
4. **Maintainability**: Single point of change for response format

Usage Examples:
---------------
# Success response
return success_response(
    data={"id": 1, "name": "John"},
    message="User created successfully",
    status_code=201
)

# Error response
return error_response(
    code=ErrorCode.NOT_FOUND,
    message="User not found",
    status_code=404
)

# Error with details (e.g., validation errors)
return error_response(
    code=ErrorCode.VALIDATION_ERROR,
    message="Validation failed",
    details={"email": "Invalid email format"},
    status_code=422
)

# Success with metadata (e.g., pagination)
return success_response(
    data=users_list,
    meta={"page": 1, "per_page": 10, "total": 100}
)
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from flask import Response, jsonify
from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Error Codes Enum
# =============================================================================


class ErrorCode(str, Enum):
    """
    Machine-readable error codes for API responses.

    These codes are designed to be:
    1. Consistent across the entire API
    2. Easy to handle programmatically on the frontend
    3. Self-documenting (the name explains the error type)

    Naming Convention:
    - UPPER_SNAKE_CASE
    - Category-specific prefixes (e.g., VALIDATION_, AUTH_)
    - Descriptive but concise
    """

    # General Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"

    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"

    # Authentication/Authorization Errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"

    # Resource Errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"

    # Database Errors
    DATABASE_ERROR = "DATABASE_ERROR"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


# =============================================================================
# Response Schemas for OpenAPI Documentation
# =============================================================================


class ErrorDetail(BaseModel):
    """
    Error detail object containing error information.

    This schema is used in error responses to provide structured
    error information that frontends can parse and display.
    """

    code: str = Field(
        ...,
        description="Machine-readable error code (e.g., VALIDATION_ERROR)",
        examples=["VALIDATION_ERROR", "NOT_FOUND", "UNAUTHORIZED"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["User not found", "Invalid email format"],
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details (e.g., field-level validation errors)",
        examples=[{"email": "Invalid email format", "password": "Too short"}],
    )


class MetaInfo(BaseModel):
    """
    Optional metadata for responses.

    Common use cases:
    - Pagination info (page, per_page, total)
    - Request tracking (request_id)
    - Performance metrics (response_time)
    """

    page: Optional[int] = Field(default=None, description="Current page number (1-indexed)", ge=1)
    per_page: Optional[int] = Field(default=None, description="Number of items per page", ge=1)
    total: Optional[int] = Field(
        default=None, description="Total number of items across all pages", ge=0
    )
    total_pages: Optional[int] = Field(default=None, description="Total number of pages", ge=0)
    request_id: Optional[str] = Field(
        default=None, description="Unique request identifier for debugging"
    )

    # Pydantic v2: Use model_config instead of inner Config class
    # extra="allow" means additional fields beyond those defined can be included
    model_config = ConfigDict(extra="allow")


class StandardSuccessResponse(BaseModel):
    """
    Standard success response schema for OpenAPI documentation.

    This is the base schema - specific endpoints can extend this
    with their own data types if needed.
    """

    success: bool = Field(default=True, description="Indicates the request was successful")
    data: Optional[Any] = Field(
        default=None, description="Response payload - can be object, array, or null"
    )
    error: None = Field(default=None, description="Always null for success responses")
    meta: Optional[MetaInfo] = Field(
        default=None, description="Optional metadata (pagination, request_id, etc.)"
    )


class StandardErrorResponse(BaseModel):
    """
    Standard error response schema for OpenAPI documentation.
    """

    success: bool = Field(default=False, description="Always false for error responses")
    data: None = Field(default=None, description="Always null for error responses")
    error: ErrorDetail = Field(
        ..., description="Error details including code, message, and optional details"
    )
    meta: Optional[MetaInfo] = Field(
        default=None, description="Optional metadata (e.g., request_id for debugging)"
    )


# =============================================================================
# Response Helper Functions
# =============================================================================


def success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
) -> tuple[Response, int]:
    """
    Create a standardized success response.

    This function ensures all successful API responses follow the same
    envelope format, making the API predictable for consumers.

    Args:
        data: The response payload. Can be:
            - A dictionary (single object)
            - A list (multiple objects)
            - None (for operations with no return data)
            - A Pydantic model (will be converted to dict)
        message: Optional success message to include in the response.
            Useful for operations like "User created successfully".
        meta: Optional metadata dictionary containing:
            - Pagination info (page, per_page, total, total_pages)
            - Request tracking (request_id)
            - Any other metadata
        status_code: HTTP status code (default: 200)
            Common values: 200 (OK), 201 (Created), 204 (No Content)

    Returns:
        Tuple of (Flask Response, status_code)

    Response Format:
        {
            "success": true,
            "data": <payload>,
            "error": null,
            "meta": <metadata> | null
        }

    Examples:
        # Simple success
        return success_response(data={"id": 1, "name": "John"})

        # Success with message (for creation)
        return success_response(
            data=user.to_dict(),
            message="User created successfully",
            status_code=201
        )

        # List with pagination
        return success_response(
            data=users_list,
            meta={"page": 1, "per_page": 10, "total": 100}
        )

    Flow Diagram:
        ┌─────────────────┐
        │   Route Handler │
        │                 │
        │  - Business     │
        │    logic        │
        │  - DB queries   │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │ success_response│
        │                 │
        │  - Wrap data    │
        │  - Add meta     │
        │  - Format JSON  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  JSON Response  │
        │  {              │
        │    success:true │
        │    data: {...}  │
        │    error: null  │
        │    meta: {...}  │
        │  }              │
        └─────────────────┘
    """
    # Handle Pydantic models - convert to dict
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif hasattr(data, "to_dict"):
        data = data.to_dict()

    # If message is provided, include it in the data
    # This is for backward compatibility with existing responses
    if message and isinstance(data, dict):
        data = {"message": message, **data}
    elif message and data is None:
        data = {"message": message}

    response_body = {
        "success": True,
        "data": data,
        "error": None,
    }

    # Only include meta if it's provided and not empty
    if meta:
        response_body["meta"] = meta
    else:
        response_body["meta"] = None

    return jsonify(response_body), status_code


def error_response(
    code: Union[ErrorCode, str],
    message: str,
    details: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = 400,
) -> tuple[Response, int]:
    """
    Create a standardized error response.

    This function ensures all error responses follow the same envelope
    format, making error handling consistent and predictable.

    Args:
        code: Machine-readable error code. Use ErrorCode enum values
            for consistency. Examples:
            - ErrorCode.VALIDATION_ERROR
            - ErrorCode.NOT_FOUND
            - ErrorCode.UNAUTHORIZED
        message: Human-readable error message that can be displayed
            to users. Should be clear and actionable when possible.
        details: Optional dictionary with additional error information.
            Common uses:
            - Field-level validation errors: {"email": "Invalid format"}
            - Technical details for debugging
            - Suggestions for fixing the error
        meta: Optional metadata (e.g., request_id for debugging)
        status_code: HTTP status code (default: 400)
            Common values:
            - 400: Bad Request (invalid input)
            - 401: Unauthorized (not logged in)
            - 403: Forbidden (no permission)
            - 404: Not Found
            - 409: Conflict (duplicate resource)
            - 422: Unprocessable Entity (validation error)
            - 500: Internal Server Error

    Returns:
        Tuple of (Flask Response, status_code)

    Response Format:
        {
            "success": false,
            "data": null,
            "error": {
                "code": "ERROR_CODE",
                "message": "Human readable message",
                "details": {...} | null
            },
            "meta": null
        }

    Examples:
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

    Flow Diagram:
        ┌─────────────────┐
        │   Route Handler │
        │                 │
        │  - Validation   │
        │    fails        │
        │  - DB error     │
        │  - Auth fails   │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  error_response │
        │                 │
        │  - Wrap error   │
        │  - Add details  │
        │  - Format JSON  │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  JSON Response  │
        │  {              │
        │   success:false │
        │   data: null    │
        │   error: {...}  │
        │   meta: null    │
        │  }              │
        └─────────────────┘
    """
    # Convert ErrorCode enum to string value
    if isinstance(code, ErrorCode):
        code = code.value

    error_body = {
        "code": code,
        "message": message,
    }

    # Only include details if provided
    if details is not None:
        error_body["details"] = details

    response_body = {
        "success": False,
        "data": None,
        "error": error_body,
    }

    # Only include meta if provided
    if meta:
        response_body["meta"] = meta
    else:
        response_body["meta"] = None

    return jsonify(response_body), status_code


# =============================================================================
# Type-Specific Response Schemas for OpenAPI
# =============================================================================
# These are reusable response schemas that can be used in route definitions
# for better OpenAPI documentation.


class UserDataSuccessResponse(StandardSuccessResponse):
    """Success response containing user data."""

    data: Optional[Dict[str, Any]] = Field(..., description="User object data")


class UsersListSuccessResponse(StandardSuccessResponse):
    """Success response containing a list of users."""

    data: Optional[List[Dict[str, Any]]] = Field(..., description="List of user objects")


# =============================================================================
# Validation Error Response Builder
# =============================================================================


def validation_error_response(
    errors: List[Dict[str, str]], message: str = "Validation failed"
) -> tuple[Response, int]:
    """
    Create a validation error response from a list of field errors.

    This is a convenience function for handling Pydantic validation errors
    or custom validation failures.

    Args:
        errors: List of error dictionaries, each containing:
            - field: The field name that failed validation
            - message: The validation error message
            - type (optional): The error type/code
        message: Overall error message (default: "Validation failed")

    Returns:
        Tuple of (Flask Response, 422 status code)

    Example:
        errors = [
            {"field": "email", "message": "Invalid email format"},
            {"field": "password", "message": "Too short"}
        ]
        return validation_error_response(errors)
    """
    # Convert list to field-keyed dictionary for details
    details = {}
    for error in errors:
        field = error.get("field", "unknown")
        msg = error.get("message", "Validation failed")
        if field in details:
            # Multiple errors for same field
            if isinstance(details[field], list):
                details[field].append(msg)
            else:
                details[field] = [details[field], msg]
        else:
            details[field] = msg

    return error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message=message,
        details=details,
        status_code=422,
    )
