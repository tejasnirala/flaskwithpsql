"""Web Interface Routes.

These routes serve the HTML pages for the application (Landing Page, Health Dashboard).
They are separate from the API blueprints to keep the clean distinction between
the REST API JSON endpoints and the human-facing HTML pages.

Prefix: / (Root)
"""

import logging
from datetime import datetime

import flask
from flask import current_app, render_template
from flask_openapi3 import APIBlueprint, Tag

from app import db

# Module-level logger
logger = logging.getLogger(__name__)

# =============================================================================
# Web Blueprint Setup
# =============================================================================

web_tag = Tag(name="Web Interface", description="HTML pages for the application")

web_bp = APIBlueprint(
    "web",
    __name__,
    url_prefix="",  # Root routes
    abp_tags=[web_tag],
)


# =============================================================================
# Routes
# =============================================================================


@web_bp.get("/", summary="Landing Page")
def index():
    """Render the professional landing page."""
    # access config from current_app
    app_version = current_app.config.get("APP_VERSION", "1.0.0")
    env = current_app.config.get("ENV", "production")

    return render_template(
        "index.html",
        app_name="Flask API Starter",
        version=app_version,
        env=env,
    )


@web_bp.get("/health", summary="Health Dashboard")
def health_ui():
    """Render the visual health dashboard."""
    # Check database connection
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "connected"
        status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
        status = "degraded"

    env = current_app.config.get("ENV", "production")

    return render_template(
        "health.html",
        app_name="Flask API Starter",
        status=status,
        database=db_status,
        api_version="v1",
        env=env,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        flask_version=flask.__version__,
    )
