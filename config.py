"""
Application configuration module.

This module defines configuration classes for different environments.
Configuration values are loaded from environment variables with sensible
defaults for development.

Usage:
    from config import config
    app.config.from_object(config['development'])
"""

import os
from typing import List, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_bool(key: str, default: bool = False) -> bool:
    """Convert environment variable to boolean."""
    value = os.environ.get(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_int(key: str, default: int = 0) -> int:
    """Convert environment variable to integer."""
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def get_env_list(key: str, default: str = "") -> List[str]:
    """Convert comma-separated environment variable to list."""
    value = os.environ.get(key, default)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_database_uri() -> str:
    """
    Build database URI from environment variables.

    Supports both direct DATABASE_URL or individual components.
    This is a module-level function (not a method) so it can be called
    at class definition time.
    """
    # Check for direct DATABASE_URL first
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Handle Heroku-style postgres:// URLs (SQLAlchemy requires postgresql://)
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url

    # Build from individual components
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "flaskwithpsql")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


class Config:
    """
    Base configuration class.

    Contains default settings that are common across all environments.
    Environment-specific classes should inherit from this and override as needed.
    """

    APP_VERSION: str = os.environ.get("APP_VERSION", "1.0.0")

    # ==========================================================================
    # SECURITY SETTINGS
    # ==========================================================================

    # Secret key for session signing - MUST be set in production
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Session cookie settings
    SESSION_COOKIE_SECURE: bool = False  # Set to True in production (HTTPS only)
    SESSION_COOKIE_HTTPONLY: bool = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE: str = "Lax"  # CSRF protection

    # ==========================================================================
    # CORS SETTINGS
    # ==========================================================================

    # Allowed origins - empty list means allow all (not recommended for production)
    CORS_ORIGINS: List[str] = get_env_list("CORS_ORIGINS")

    # Allowed HTTP methods
    CORS_METHODS: List[str] = get_env_list("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS")

    # Allowed request headers
    CORS_ALLOW_HEADERS: List[str] = get_env_list("CORS_ALLOW_HEADERS", "Content-Type,Authorization")

    # Headers exposed to the browser
    CORS_EXPOSE_HEADERS: List[str] = get_env_list(
        "CORS_EXPOSE_HEADERS", "Content-Type,Authorization"
    )

    # Allow credentials (cookies, authorization headers)
    CORS_CREDENTIALS: bool = get_env_bool("CORS_CREDENTIALS", False)

    # Preflight cache duration in seconds
    CORS_MAX_AGE: int = get_env_int("CORS_MAX_AGE", 3600)

    # ==========================================================================
    # DATABASE SETTINGS
    # ==========================================================================

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False  # Disable event system (saves memory)
    SQLALCHEMY_ECHO: bool = False  # Don't log SQL queries by default

    # Database connection pool settings
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 300,  # Recycle connections after 5 minutes
    }

    # Build database URI from environment
    # Note: We use a class attribute here, not @property, because Flask's
    # from_object() reads class attributes directly and @property only
    # works on instances.
    SQLALCHEMY_DATABASE_URI: str = _build_database_uri()

    # ==========================================================================
    # APPLICATION SETTINGS
    # ==========================================================================

    # URL scheme for url_for() when behind a proxy
    PREFERRED_URL_SCHEME: str = "http"

    # Maximum content length for requests (16MB default)
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024

    # JSON settings
    JSON_SORT_KEYS: bool = False  # Don't sort JSON keys (faster)

    # ==========================================================================
    # SWAGGER UI SETTINGS
    # ==========================================================================
    # Configuration for Swagger UI display
    # See: https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
    SWAGGER_CONFIG: dict = {
        # Layout & Expansion
        "docExpansion": "none",  # "none", "list", or "full" - collapse all by default
        "defaultModelsExpandDepth": 0,  # 0=collapsed, 1=expanded, -1=hidden
        "defaultModelExpandDepth": 3,  # Depth of model expansion when clicked
        # Display Options
        "displayOperationId": False,  # Hide operation IDs (cleaner look)
        "displayRequestDuration": True,  # Show request time after "Try It Out"
        "filter": True,  # Enable search/filter box
        "showExtensions": False,  # Hide vendor extensions
        "showCommonExtensions": False,  # Hide common extensions
        # Navigation & UX
        "deepLinking": True,  # Enable deep linking (shareable URLs)
        "persistAuthorization": True,  # Remember auth across page refreshes!
        "tryItOutEnabled": False,  # Don't auto-enable "Try It Out"
        # Syntax Highlighting
        "syntaxHighlight.activate": True,  # Enable syntax highlighting
        "syntaxHighlight.theme": "monokai",  # Theme: monokai, agate, nord, obsidian
    }

    @classmethod
    def validate(cls) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages. Empty list means configuration is valid.
        """
        errors = []

        # Check for default secret key
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            errors.append("SECRET_KEY is using default value - set a secure key!")

        # Check secret key length
        if len(cls.SECRET_KEY) < 32:
            errors.append("SECRET_KEY should be at least 32 characters long")

        return errors


class DevelopmentConfig(Config):
    """
    Development configuration.

    Enables debug mode and verbose logging for easier development.
    """

    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = False  # Log SQL queries for debugging

    # Allow all localhost origins in development
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React default
        "http://localhost:5173",  # Vite default
        "http://localhost:8080",  # Vue CLI default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ]

    CORS_CREDENTIALS: bool = True

    @classmethod
    def validate(cls) -> List[str]:
        """Development config - shows warnings but doesn't require fixes."""
        import warnings

        # Call parent validation to show warnings
        errors = super().validate()
        # In development, we use warnings module (logging may not be initialized yet)
        for error in errors:
            warnings.warn(f"DEV CONFIG WARNING: {error}", UserWarning, stacklevel=2)
        return []  # Allow startup even with warnings


class ProductionConfig(Config):
    """
    Production configuration.

    Optimized for security and performance.
    """

    DEBUG: bool = False
    TESTING: bool = False
    SQLALCHEMY_ECHO: bool = False

    # Security settings
    SESSION_COOKIE_SECURE: bool = True  # Require HTTPS
    PREFERRED_URL_SCHEME: str = "https"

    # CORS - should be set via environment variable
    CORS_CREDENTIALS: bool = get_env_bool("CORS_CREDENTIALS", True)

    # Production database pool settings
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,  # Larger pool for production
        "max_overflow": 20,  # Allow more connections under load
    }

    @classmethod
    def validate(cls) -> List[str]:
        """Strict validation for production."""
        errors = super().validate()

        # Secret key is mandatory in production
        if not os.environ.get("SECRET_KEY"):
            errors.append("SECRET_KEY environment variable is required in production")

        # CORS origins should be explicitly set
        if not cls.CORS_ORIGINS:
            errors.append("CORS_ORIGINS must be set in production (not wildcard)")

        # Database password should be set
        if not os.environ.get("DATABASE_URL") and not os.environ.get("DB_PASSWORD"):
            errors.append("Database password must be set in production")

        return errors


class TestingConfig(Config):
    """
    Testing configuration.

    Used for automated tests with isolated test database.
    """

    TESTING: bool = True
    DEBUG: bool = True

    # Use separate test database
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/flaskwithpsql_test",
    )

    # Disable CSRF for testing
    WTF_CSRF_ENABLED: bool = False

    # Allow all origins in tests
    CORS_ORIGINS: List[str] = ["*"]

    @classmethod
    def validate(cls) -> List[str]:
        """Testing config is lenient."""
        return []


# ==========================================================================
# CONFIGURATION REGISTRY
# ==========================================================================

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(env: Optional[str] = None) -> type:
    """
    Get configuration class for the specified environment.

    Args:
        env: Environment name ('development', 'production', 'testing').
             Defaults to FLASK_ENV environment variable or 'development'.

    Returns:
        Configuration class for the environment.
    """
    if env is None:
        env = os.environ.get("FLASK_ENV", "development").lower().strip()

    return config.get(env, config["default"])
