"""
Rate Limiting Configuration.

This module provides rate limiting to protect the API from abuse.
Uses Flask-Limiter with configurable storage backends.

Rate Limiting Benefits:
-----------------------
1. Prevents brute-force attacks (login endpoint)
2. Protects against DoS attacks
3. Ensures fair usage among clients
4. Reduces server load from misbehaving clients

Usage:
    from app.utils.rate_limiter import limiter

    @app.route("/api/resource")
    @limiter.limit("10 per minute")
    def get_resource():
        ...
"""

import logging
import os

from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)


def get_client_ip():
    """
    Get the real client IP address.

    Handles proxies by checking X-Forwarded-For header first.
    Falls back to remote_addr if no proxy headers present.

    Returns:
        str: Client IP address
    """
    # Check for proxy headers (in order of reliability)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # The first one is the original client
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # No proxy, use direct connection IP
    return get_remote_address()


# Initialize the limiter (without app - will be initialized in factory)
limiter = Limiter(
    key_func=get_client_ip,
    # Use memory storage by default (for development)
    # In production, use Redis: "redis://localhost:6379"
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URL", "memory://"),
    # Default limits applied to all routes
    default_limits=["200 per day", "50 per hour"],
    # Don't fail if storage is unavailable
    storage_options={"socket_connect_timeout": 30},
    # Return proper JSON error responses
    strategy="fixed-window",
)


def init_limiter(app: Flask) -> None:
    """
    Initialize rate limiter with the Flask app.

    Args:
        app: Flask application instance
    """
    limiter.init_app(app)

    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        from app.utils.responses import ErrorCode, error_response

        logger.warning(
            "Rate limit exceeded",
            extra={
                "client_ip": get_client_ip(),
                "limit": e.description,
            },
        )
        return error_response(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=f"Rate limit exceeded: {e.description}",
            status_code=429,
        )

    logger.info("Rate limiter initialized")


# =============================================================================
# Rate Limit Decorators (Shortcuts)
# =============================================================================

# Strict limit for authentication endpoints (prevent brute-force)
auth_limit = limiter.limit("5 per minute")

# Standard API limit
api_limit = limiter.limit("60 per minute")

# Relaxed limit for read-only endpoints
read_limit = limiter.limit("120 per minute")

# Very strict limit for sensitive operations
strict_limit = limiter.limit("3 per minute")
