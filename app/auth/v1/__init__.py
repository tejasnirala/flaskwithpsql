"""API Version 1 Authentication Routes Package.

This module creates a parent blueprint for auth v1 that can be nested
under the main v1 blueprint.

The auth routes are registered with just /auth prefix, and the parent
v1 blueprint adds the /api/v1 prefix.

Usage:
    # Option 1: Register directly with app (will use its own prefix)
    from app.auth.v1 import auth_bp_v1
    app.register_api(auth_bp_v1)  # Would be /auth/*

    # Option 2: Register under v1 parent (recommended)
    from app.routes.v1 import api_v1
    api_v1.register_api(auth_bp_v1)  # Will be /api/v1/auth/*
"""

from app.auth.v1.routes import auth_bp_v1

__all__ = ["auth_bp_v1"]
