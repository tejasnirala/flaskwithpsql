"""
Utils Package - Centralized utility functions for the application.

This package contains:
1. Response utilities for standardized API responses
2. Error handlers for global exception handling
3. Logging configuration for centralized, structured logging

The goal is to ensure ALL API endpoints return consistent,
predictable JSON responses following a standard envelope format.
"""

from app.utils.error_handlers import pydantic_validation_error_callback, register_error_handlers
from app.utils.logging_config import (
    get_logger,
    get_request_id,
    log_function_call,
    mask_sensitive_data,
    setup_logging,
)
from app.utils.responses import (  # Response Schemas for OpenAPI
    ErrorCode,
    ErrorDetail,
    MetaInfo,
    StandardErrorResponse,
    StandardSuccessResponse,
    error_response,
    success_response,
)

__all__ = [
    # Response utilities
    "success_response",
    "error_response",
    "ErrorCode",
    # Response schemas
    "StandardSuccessResponse",
    "StandardErrorResponse",
    "ErrorDetail",
    "MetaInfo",
    # Error handlers
    "register_error_handlers",
    "pydantic_validation_error_callback",
    # Logging utilities
    "setup_logging",
    "get_logger",
    "get_request_id",
    "mask_sensitive_data",
    "log_function_call",
]
