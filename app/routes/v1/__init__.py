"""API Version 1 Routes Package.

This module creates a parent blueprint for API v1 that aggregates ALL v1 routes
including authentication. The version prefix (/api/v1) is defined ONCE here,
and all child blueprints are registered under it.

This pattern is similar to Express.js nested routers:
```javascript
const v1Router = express.Router();
v1Router.use('/', mainRouter);      // Health check routes
v1Router.use('/users', usersRouter);
v1Router.use('/auth', authRouter);
app.use('/api/v1', v1Router);       // Version defined ONCE!
```

Usage:
    from app.routes.v1 import api_v1
    app.register_api(api_v1)  # Registers ALL v1 routes with /api/v1 prefix

Benefits:
---------
1. Single source of truth for version prefix
2. Easy to add new route modules
3. Clean separation between versions
4. Similar to Express.js pattern you're familiar with
"""

from flask_openapi3 import APIBlueprint

from app.auth.v1.routes import auth_bp_v1
from app.routes.v1.main import main_bp_v1
from app.routes.v1.users import users_bp_v1

# =============================================================================
# Parent Blueprint for API v1
# =============================================================================
# This is the ONLY place where /api/v1 prefix is defined.
# All child blueprints are nested under this parent.

api_v1 = APIBlueprint(
    "api_v1",  # Parent blueprint name
    __name__,
    url_prefix="/api/v1",  # Version prefix - defined ONCE here!
)

# =============================================================================
# Register All v1 Child Blueprints
# =============================================================================
# Each blueprint's url_prefix gets appended to /api/v1
# Example: users_bp_v1 has url_prefix="/users" → final URL is /api/v1/users

api_v1.register_api(main_bp_v1)  # /api/v1/ and /api/v1/health
api_v1.register_api(users_bp_v1)  # /api/v1/users/*
api_v1.register_api(auth_bp_v1)  # /api/v1/auth/*


# Export for use in app factory
__all__ = ["api_v1"]
