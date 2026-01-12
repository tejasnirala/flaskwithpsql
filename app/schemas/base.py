"""
Base Schema - Common Pydantic configuration and utilities.

This module provides:
1. BaseSchema - A base class with common configuration for all schemas
2. Utility functions for validation
3. Custom validators that can be reused across schemas

Why use a base schema?
    - Ensures consistent behavior across all schemas
    - Centralizes common configuration (like JSON serialization settings)
    - Provides a single point for shared validation logic
    - Makes it easy to add global features later (like logging, error formatting)
"""

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema class that all other schemas should inherit from.

    This provides common configuration that ensures consistent behavior:

    1. model_config - Pydantic v2 configuration using ConfigDict

    ### Configuration Options Explained:
    --------------------------------

    - str_strip_whitespace:
        Automatically strips leading/trailing whitespace from strings.
        Example: "  john  " becomes "john"
        Why? Prevents accidental whitespace in user inputs.

    - str_min_length:
        Sets minimum length for ALL strings to 1 (no empty strings by default).
        Can be overridden per-field if needed.
        Why? Catches empty strings that might cause issues downstream.

    - extra:
        What to do with extra fields not defined in the schema.
        'ignore' = silently ignore extra fields
        'forbid' = raise error if extra fields are present
        'allow' = allow and store extra fields
        We use 'ignore' to be lenient with input but only process known fields.

    - from_attributes:
        Allows creating a schema instance from ORM models (like SQLAlchemy).
        Example: UserResponseSchema.model_validate(user_orm_instance)
        Why? Makes it easy to convert database objects to response schemas.

    - populate_by_name:
        Allows using either field name or alias when creating instances.
        Why? Flexibility in accepting different naming conventions.
    """

    model_config = ConfigDict(
        # Strip whitespace from all string fields
        str_strip_whitespace=True,
        # Extra fields in input data are ignored (not stored or validated)
        extra="ignore",
        # Allow creating schema from ORM objects (SQLAlchemy models)
        from_attributes=True,
        # Allow using field aliases when populating
        populate_by_name=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert schema to dictionary.

        This is a convenience method that wraps Pydantic's model_dump().
        Using a named method makes the code more readable and consistent
        with our SQLAlchemy model's to_dict() method.

        Returns:
            dict: Dictionary representation of the schema
        """
        return self.model_dump()

    def to_json(self) -> str:
        """
        Convert schema to JSON string.

        Wraps Pydantic's model_dump_json() for consistency.

        Returns:
            str: JSON string representation of the schema
        """
        return self.model_dump_json()
