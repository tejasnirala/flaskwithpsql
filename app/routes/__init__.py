"""Routes Package - API Versioning Hub.

This module provides version management for API routes.
It exports parent blueprints for each API version.

Structure:
    app/routes/
    ├── __init__.py          # This file - exports version parent blueprints
    └── v1/                   # API Version 1
        ├── __init__.py      # Creates api_v1 parent blueprint
        ├── main.py          # /api/v1/ and /api/v1/health
        └── users.py         # /api/v1/users/*

Usage:
    from app.routes.v1 import api_v1
    app.register_api(api_v1)  # Registers ALL v1 routes!

API Versioning Strategy:
------------------------
This project uses URL-based API versioning with parent blueprints.
Each version has a parent blueprint that defines the version prefix.
Child blueprints are nested under the parent.

Benefits:
1. Version prefix defined in ONE place
2. Easy to add new route modules
3. Clean separation between versions
4. Similar to Express.js nested routers

Adding a New Version:
--------------------
1. Create app/routes/v2/
2. Create a parent blueprint with url_prefix="/api/v2"
3. Register child blueprints under the parent
4. Import and register in app/__init__.py
"""

# Import versioned parent blueprints
from app.routes.v1 import api_v1

__all__ = ["api_v1"]
