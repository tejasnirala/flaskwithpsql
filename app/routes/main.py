"""Main routes for the application.

These routes provide health checks and basic status endpoints.
Using APIBlueprint from flask-openapi3 instead of regular Blueprint
for automatic OpenAPI documentation generation.
"""

import logging
from typing import Optional

from flask import render_template
from flask_openapi3 import APIBlueprint, Tag
from pydantic import BaseModel, Field

from app.utils.responses import StandardSuccessResponse, success_response
from app.version import __version__

# Module-level logger
logger = logging.getLogger(__name__)


# =============================================================================
# API Blueprint Setup
# =============================================================================

# Tag for grouping these endpoints in Swagger UI
tag = Tag(name="Health", description="Health check and status endpoints")

# APIBlueprint is a drop-in replacement for Blueprint with OpenAPI support
main_bp = APIBlueprint(
    "main",
    __name__,
    # abp_tags defines which tags apply to ALL routes in this blueprint
    abp_tags=[tag],
)


# =============================================================================
# Response Schemas (for OpenAPI documentation)
# =============================================================================


class WelcomeDataResponse(StandardSuccessResponse):
    """Response schema for the welcome/root endpoint."""

    class WelcomeData(BaseModel):
        message: str = Field(
            ...,
            description="Welcome message",
            examples=["Welcome to Flask with PostgreSQL!"],
        )
        status: str = Field(..., description="Application status", examples=["running"])
        version: str = Field(..., description="API version", examples=["1.0.0"])

    data: Optional[WelcomeData] = Field(..., description="Welcome data")


class HealthDataResponse(StandardSuccessResponse):
    """Response schema for health check endpoint."""

    class HealthData(BaseModel):
        status: str = Field(..., description="Health status", examples=["healthy"])
        database: str = Field(..., description="Database connection status", examples=["connected"])

    data: Optional[HealthData] = Field(..., description="Health check data")


# =============================================================================
# Routes
# =============================================================================


@main_bp.get(
    "/",
    summary="Root Endpoint",
    description="Returns a welcome message and basic API information.",
    responses={
        200: WelcomeDataResponse,
    },
)
def index():
    """
    Root endpoint - Welcome message.

    Returns:
        JSON response with welcome message and API status
    """
    return success_response(
        data={
            "message": "Welcome to Flask with PostgreSQL!",
            "status": "running",
            "version": __version__,
        }
    )


@main_bp.get("/template")
def test_template():
    """
    Test template route - demonstrates HTML templating.

    Note: This route returns HTML, not JSON, so we don't define
    response schemas for it. It won't appear in API docs.

    Returns:
        Rendered HTML template
    """
    return render_template("test.html")


@main_bp.get(
    "/health",
    summary="Health Check",
    description="Returns the health status of the API and database connection.",
    responses={
        200: HealthDataResponse,
    },
)
def health():
    """
    Health check endpoint.

    Actually verifies database connectivity by executing a simple query.

    Returns:
        JSON response indicating service health
    """
    from app import db

    # Actually check database connection
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    return success_response(
        data={
            "status": "healthy" if db_status == "connected" else "degraded",
            "database": db_status,
        }
    )
