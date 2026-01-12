"""
Shared Validators - Reusable field validators for Pydantic schemas.

This module provides common validators that can be reused across multiple
schemas to avoid code duplication (DRY principle).

Usage:
    from app.schemas.validators import normalize_name

    class MySchema(BaseSchema):
        first_name: Optional[str] = Field(...)

        # Use the shared validator
        _normalize_names = field_validator(
            "first_name", "last_name", mode="before"
        )(normalize_name)
"""

from typing import Optional


def normalize_name(v: Optional[str]) -> Optional[str]:
    """
    Normalize names to title case.

    This is a reusable validator function that can be applied to any name field.

    Examples:
        - "john" → "John"
        - "JOHN" → "John"
        - "john doe" → "John Doe" (for multi-word names)
        - None → None (for optional fields)

    Why normalize?
        - Consistent formatting in the database
        - Looks professional in user displays
        - Prevents duplicates due to case differences

    Args:
        v: The name value (or None for optional fields)

    Returns:
        str | None: Title-cased name or None
    """
    if v is None:
        return v
    return v.title()


def normalize_username(v: str) -> str:
    """
    Normalize username to lowercase.

    Why lowercase?
        - Prevents duplicate usernames like 'John' and 'john'
        - Makes username comparison consistent
        - Common practice in authentication systems

    Args:
        v: The username value

    Returns:
        str: Lowercase username
    """
    return v.lower()


def validate_password_strength(v: str) -> str:
    """
    Validate password meets strength requirements.

    Requirements:
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit

    Why these rules?
        - Prevents extremely weak passwords
        - Industry standard for basic password security
        - Balances security with user convenience

    Args:
        v: The password value

    Returns:
        str: The validated password (unchanged)

    Raises:
        ValueError: If password doesn't meet strength requirements
    """
    if not any(c.isupper() for c in v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.islower() for c in v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one digit")
    return v
