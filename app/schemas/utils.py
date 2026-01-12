"""
Validation Utilities - Helper functions for Pydantic validation in Flask.

This module bridges Pydantic validation with Flask's request handling.
It provides:

1. validate_request_body() - Decorator for route functions
2. format_validation_errors() - Converts Pydantic errors to user-friendly messages
3. ValidationError exception handling utilities

Why This Module Exists:
-----------------------
Pydantic and Flask don't integrate automatically. We need to:
- Parse JSON from Flask's request object
- Pass it to Pydantic schemas
- Handle validation errors gracefully
- Return consistent error responses

This module makes that integration clean and reusable.
"""

from functools import wraps
from typing import Any, Dict, List, Tuple, Type, TypeVar, Union  # noqa: F401

from flask import jsonify, request
from pydantic import BaseModel, ValidationError

# BaseSchema is used for type hints in docstrings

# Type variable for generic schema type
T = TypeVar("T", bound=BaseModel)


def format_validation_errors(error: ValidationError) -> List[Dict[str, Any]]:
    """
    Convert Pydantic ValidationError to a user-friendly format.

    Pydantic's default error format is detailed but complex. This function
    transforms it into a simpler, API-friendly format.

    How Pydantic ValidationError Works:
    ------------------------------------
    When validation fails, Pydantic creates a ValidationError containing
    a list of error details. Each error has:
    - type: Error type code (e.g., 'string_too_short', 'missing')
    - loc: Tuple of field path (e.g., ('username',) or ('address', 'city'))
    - msg: Human-readable error message
    - input: The invalid value that was provided
    - ctx: Additional context (like min_length value)

    Our Output Format:
    ------------------
    [
        {
            "field": "username",
            "message": "String should have at least 3 characters",
            "type": "string_too_short"
        },
        ...
    ]

    Args:
        error: Pydantic ValidationError exception

    Returns:
        list: List of simplified error dictionaries

    Example:
        try:
            UserCreateSchema(**data)
        except ValidationError as e:
            errors = format_validation_errors(e)
            # errors = [{"field": "username", "message": "...", "type": "..."}]
    """
    formatted_errors = []

    for err in error.errors():
        # loc is a tuple like ('username',) or ('address', 'city')
        # We join with '.' for nested fields
        field_path = ".".join(str(loc) for loc in err["loc"])

        formatted_errors.append({"field": field_path, "message": err["msg"], "type": err["type"]})

    return formatted_errors


def validate_request(schema_class: Type[T]) -> Union[T, Tuple]:
    """
    Validate Flask request JSON body against a Pydantic schema.

    This is a helper function (not a decorator) that validates request data
    and returns either:
    - A validated schema instance on success
    - A tuple of (error_response, status_code) on failure

    Usage:
        @app.route('/users', methods=['POST'])
        def create_user():
            result = validate_request(UserCreateSchema)
            if isinstance(result, tuple):
                return result  # Return error response

            validated_data = result
            # Use validated_data...

    Args:
        schema_class: The Pydantic schema class to validate against

    Returns:
        schema_class instance: If validation succeeds
        tuple: (jsonify response, status code) if validation fails

    Flow:
    1. Get JSON from request
    2. If no JSON → return 400 error
    3. Try to create schema instance
    4. If validation fails → return 422 error with details
    5. If success → return validated schema instance
    """
    # Step 1: Get JSON data from request
    data = request.get_json()

    # Step 2: Check if data exists
    if data is None:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "No JSON data provided",
                    "message": "Request body must be valid JSON",
                }
            ),
            400,
        )

    # Step 3: Try to validate
    try:
        validated = schema_class(**data)
        return validated

    except ValidationError as e:
        # Step 4: Format errors and return 422
        # 422 Unprocessable Entity - The request was well-formed but
        # had semantic errors (validation failures)
        errors = format_validation_errors(e)

        return (
            jsonify(
                {
                    "success": False,
                    "error": "Validation failed",
                    "message": "One or more fields failed validation",
                    "details": errors,
                }
            ),
            422,
        )


def validate_with_schema(schema_class: Type[T]):
    """
    Decorator that validates request body and injects validated data.

    This decorator wraps a route function and:
    1. Validates the request JSON against the schema
    2. If valid, passes the validated schema as first argument to the function
    3. If invalid, returns an error response without calling the function

    Usage:
        @app.route('/users', methods=['POST'])
        @validate_with_schema(UserCreateSchema)
        def create_user(validated_data: UserCreateSchema):
            # validated_data is guaranteed to be valid
            user = User(
                username=validated_data.username,
                email=validated_data.email,
                ...
            )

    Args:
        schema_class: The Pydantic schema class to validate against

    Returns:
        Decorated function

    How Decorators Work (Quick Refresher):
    --------------------------------------
    A decorator is a function that takes a function and returns a new function.

    @validate_with_schema(UserCreateSchema)
    def my_function():
        pass

    Is equivalent to:
    my_function = validate_with_schema(UserCreateSchema)(my_function)

    The @wraps decorator preserves the original function's metadata
    (name, docstring, etc.) which is important for Flask's routing.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate the request
            result = validate_request(schema_class)

            # If result is a tuple, it's an error response
            if isinstance(result, tuple):
                return result

            # Otherwise, it's the validated schema
            # Add it as the first argument to the wrapped function
            return func(result, *args, **kwargs)

        return wrapper

    return decorator
