"""Flask application factory with OpenAPI support.

This module creates the Flask application using flask-openapi3's OpenAPI class
instead of the regular Flask class. This enables:
1. Automatic OpenAPI specification generation
2. Built-in Swagger UI at /openapi/swagger
3. Built-in ReDoc UI at /openapi/redoc
4. Built-in RapiDoc UI at /openapi/rapidoc
5. JSON specification at /openapi/openapi.json

The application factory pattern remains the same - we just swap Flask for OpenAPI.
"""

from flask_cors import CORS
from flask_migrate import Migrate

# Import OpenAPI instead of Flask
from flask_openapi3 import Info, OpenAPI
from flask_sqlalchemy import SQLAlchemy

from app.version import __version__
from config import config

# Initialize extensions (without app)
db = SQLAlchemy()
migrate = Migrate()

# =============================================================================
# OpenAPI Metadata Configuration
# =============================================================================

# API Information - This appears in Swagger UI header
info = Info(
    title="Flask PostgreSQL Learning API",
    version=__version__,
    description="""""",
)


def create_app(config_name="default"):
    """
    Application factory function with OpenAPI support.

    Args:
        config_name: Configuration to use (development, production, testing)

    Returns:
        OpenAPI application instance (drop-in replacement for Flask)

    What Changed from Regular Flask:
    --------------------------------
    1. `Flask(__name__)` → `OpenAPI(__name__, info=info)`
    2. Added `info` parameter for API metadata
    3. Everything else works exactly the same!

    Available Documentation URLs:
    -----------------------------
    - /docs         → Swagger UI (interactive)
    - /redoc        → ReDoc (clean documentation)
    - /rapidoc      → RapiDoc (alternative UI)
    - /openapi.json → Raw OpenAPI specification
    """
    import logging

    config_class = config[config_name]

    # Validate configuration
    errors = config_class.validate()
    if errors:
        # Use logger for config errors (basic logging until full setup)
        logger = logging.getLogger(__name__)
        for error in errors:
            logger.error(f"CONFIG ERROR: {error}")
        if config_name == "production":
            raise ValueError("Invalid production configuration")

    # Import the centralized validation error callback
    # This ensures all error responses follow the same format
    from app.utils.error_handlers import pydantic_validation_error_callback

    # Use OpenAPI instead of Flask
    # This is a drop-in replacement that adds OpenAPI capabilities
    app = OpenAPI(
        __name__,
        info=info,
        # Custom validation error handling to match our standard response format
        # The callback is defined in error_handlers.py for centralization
        validation_error_callback=pydantic_validation_error_callback,
    )

    # Load configuration - works exactly like Flask
    app.config.from_object(config_class)

    # ==========================================================================
    # Initialize Centralized Logging System
    # ==========================================================================
    # This must be done early, after config is loaded but before other setup
    from app.utils.logging_config import setup_logging

    setup_logging(app)

    # Now we can get the app logger
    logger = logging.getLogger(__name__)
    logger.info(f"Creating Flask app with config: {config_name}")

    # Initialize extensions with app - no changes needed
    db.init_app(app)
    migrate.init_app(app, db)

    # ==========================================================================
    # Initialize JWT Authentication
    # ==========================================================================
    from app.auth import init_jwt

    init_jwt(app)

    # ==========================================================================
    # Initialize Rate Limiting
    # ==========================================================================
    from app.utils.rate_limiter import init_limiter

    init_limiter(app)

    # Configure CORS - no changes needed
    cors_config = config[config_name]
    CORS(
        app,
        origins=cors_config.CORS_ORIGINS or ["*"],
        methods=cors_config.CORS_METHODS,
        allow_headers=cors_config.CORS_ALLOW_HEADERS,
        expose_headers=cors_config.CORS_EXPOSE_HEADERS,
        supports_credentials=cors_config.CORS_CREDENTIALS,
        max_age=cors_config.CORS_MAX_AGE,
    )

    # Register APIBlueprints using register_api() instead of register_blueprint()
    # This is CRITICAL - register_api() makes routes appear in OpenAPI spec
    from app.auth.routes import auth_bp
    from app.routes.main import main_bp
    from app.routes.users import users_bp

    app.register_api(main_bp)
    app.register_api(users_bp)  # url_prefix is set in APIBlueprint constructor
    app.register_api(auth_bp)  # Authentication routes

    # Register global error handlers for consistent error responses
    from app.utils.error_handlers import register_error_handlers

    register_error_handlers(app)

    # Shell context for flask shell - no changes needed
    @app.shell_context_processor
    def make_shell_context():
        return {"db": db, "User": User}

    from app.models.user import User

    return app
