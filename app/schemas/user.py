"""
User Schemas - Pydantic validation schemas for User operations.

This module contains all schemas related to User CRUD operations:

1. UserCreateSchema   - Validates user registration data
2. UserLoginSchema    - Validates user login data
3. UserUpdateSchema   - Validates user profile update data
4. UserResponseSchema - Formats user data for API responses

Design Philosophy:
------------------
Each operation has its own schema because:
- Different operations require different fields
- Validation rules may differ (e.g., password required for create, not for update)
- Response schemas may exclude sensitive fields (like password)
- Makes the API contract explicit and self-documenting

Naming Convention:
------------------
- [Entity][Operation]Schema
- Examples: UserCreateSchema, UserLoginSchema, UserUpdateSchema
"""

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field, field_validator, model_validator

from app.schemas.base import BaseSchema
from app.schemas.validators import normalize_name, normalize_username, validate_password_strength


class UserCreateSchema(BaseSchema):
    """
    Schema for user registration (POST /users/register).

    All required fields must be provided. Optional fields can be omitted.

    Field Definitions:
    ------------------
    Each Field() call defines:
    - min_length/max_length: String length constraints
    - pattern: Regex pattern the value must match
    - description: Human-readable description for API docs
    - examples: Example values for API documentation

    Validators:
    -----------
    - @field_validator: Validates/transforms a single field
    - @model_validator: Validates multiple fields together (cross-field validation)
    """

    # Required fields
    username: str = Field(
        ...,  # ... means required (no default value)
        min_length=3,
        max_length=80,
        pattern=r"^[a-zA-Z0-9_]+$",  # Only alphanumeric and underscore
        description="Unique username (3-80 chars, alphanumeric and underscore only)",
        examples=["john_doe", "user123"],
    )

    email: EmailStr = Field(..., description="Valid email address", examples=["john@example.com"])

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8-128 characters)",
        examples=["SecurePass123!"],
    )

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="User's first name",
        examples=["John"],
    )

    # Optional fields
    middle_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="User's middle name (optional)",
        examples=["William"],
    )

    last_name: Optional[str] = Field(
        default=None,
        max_length=50,
        description="User's last name (optional)",
        examples=["Doe"],
    )

    bio: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Short bio about the user (optional, max 500 chars)",
        examples=["Software developer passionate about Python"],
    )

    # ==========================================================================
    # FIELD VALIDATORS - Using shared validators for DRY
    # ==========================================================================

    # Normalize username to lowercase
    _normalize_username = field_validator("username")(normalize_username)

    # Validate password strength
    _validate_password = field_validator("password")(validate_password_strength)

    # Normalize names to title case
    _normalize_names = field_validator("first_name", "middle_name", "last_name")(normalize_name)


class UserLoginSchema(BaseSchema):
    """
    Schema for user login (POST /users/login).

    Only requires credentials - no profile data needed.
    """

    email: EmailStr = Field(..., description="User's email address", examples=["john@example.com"])

    password: str = Field(
        ...,
        min_length=1,  # Don't validate password strength on login
        description="User's password",
        examples=["SecurePass123!"],
    )


class UserUpdateSchema(BaseSchema):
    """
    Schema for updating user profile (PUT /users/<id>).

    All fields are optional - only provided fields will be updated.
    This follows the "partial update" pattern common in REST APIs.

    Why all fields optional?
    - Client only sends fields they want to update
    - Prevents accidental overwrites
    - More efficient (less data over the network)
    - Standard REST PATCH/PUT pattern
    """

    first_name: Optional[str] = Field(
        default=None, min_length=1, max_length=50, description="User's first name"
    )

    middle_name: Optional[str] = Field(
        default=None, max_length=50, description="User's middle name"
    )

    last_name: Optional[str] = Field(default=None, max_length=50, description="User's last name")

    bio: Optional[str] = Field(default=None, max_length=500, description="Short bio about the user")

    is_active: Optional[bool] = Field(
        default=None, description="Whether the user account is active"
    )

    # Use shared validator for name normalization
    _normalize_names = field_validator("first_name", "middle_name", "last_name")(normalize_name)

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UserUpdateSchema":
        """
        Ensure at least one field is provided for update.

        This is a model_validator (validates the whole model, not just one field).

        mode='after' means:
        - All field validations have completed
        - We have access to the fully constructed model instance
        - We can compare fields against each other

        Why this validation?
        - Prevents empty update requests
        - Saves a database round-trip for nothing
        - Provides clear error message to the client

        Returns:
            UserUpdateSchema: The validated model instance

        Raises:
            ValueError: If no fields are provided for update
        """
        # Get all fields that were explicitly set (not None)
        values = self.model_dump(exclude_unset=True)
        if not values:
            raise ValueError("At least one field must be provided for update")
        return self


class UserResponseSchema(BaseSchema):
    """
    Schema for user data in API responses.

    Purpose:
    --------
    Controls what user data is exposed in API responses.
    Notice: NO password field! Never expose passwords in responses.

    Key Features:
    - Excludes sensitive fields (password_hash)
    - Includes computed/derived fields if needed
    - Consistent format for all user responses
    - Can be created from SQLAlchemy model using from_attributes

    Usage:
        user = User.query.get(1)  # SQLAlchemy model
        response = UserResponseSchema.model_validate(user)
        return jsonify(response.to_dict())
    """

    id: int = Field(description="Unique user identifier")
    username: str = Field(description="User's username")
    email: EmailStr = Field(description="User's email address")
    first_name: Optional[str] = Field(default=None, description="First name")
    middle_name: Optional[str] = Field(default=None, description="Middle name")
    last_name: Optional[str] = Field(default=None, description="Last name")
    bio: Optional[str] = Field(default=None, description="User bio")
    is_active: bool = Field(description="Whether account is active")
    is_deleted: bool = Field(description="Whether account is deleted (soft delete)")
    created_at: Optional[datetime] = Field(default=None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
