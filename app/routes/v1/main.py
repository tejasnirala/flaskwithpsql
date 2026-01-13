"""Main routes for API v1.

These routes provide health checks and basic status endpoints.
Using APIBlueprint from flask-openapi3 for automatic OpenAPI documentation.

Version: 1
Prefix: /api/v1
"""

import logging
from typing import Optional


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
tag = Tag(name="Health (v1)", description="Health check and status endpoints - Version 1")

# APIBlueprint with just the resource prefix (empty for root)
# Version prefix (/api/v1) is added during registration in app/__init__.py
main_bp_v1 = APIBlueprint(
    "main_v1",  # Unique name for v1
    __name__,
    url_prefix="/",  # Root routes - version added at registration
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
        api_version: str = Field(..., description="API version number", examples=["v1"])

    data: Optional[WelcomeData] = Field(..., description="Welcome data")


class HealthDataResponse(StandardSuccessResponse):
    """Response schema for health check endpoint."""

    class HealthData(BaseModel):
        status: str = Field(..., description="Health status", examples=["healthy"])
        database: str = Field(..., description="Database connection status", examples=["connected"])
        api_version: str = Field(..., description="API version", examples=["v1"])

    data: Optional[HealthData] = Field(..., description="Health check data")


# =============================================================================
# Routes
# =============================================================================


@main_bp_v1.get(
    "/",
    summary="Root Endpoint",
    description="Returns a welcome message and basic API information for v1.",
    responses={
        200: WelcomeDataResponse,
    },
)
def index():
    """
    Root endpoint for API v1 - Welcome message.

    Returns:
        JSON response with welcome message and API status
    """
    return success_response(
        data={
            "message": "Welcome to Flask with PostgreSQL!",
            "status": "running",
            "version": __version__,
            "api_version": "v1",
        }
    )


@main_bp_v1.get(
    "/health",
    summary="Health Check",
    description="Returns the health status of the API and database connection.",
    responses={
        200: HealthDataResponse,
    },
)
def health():
    """
    Health check endpoint for API v1.

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
            "api_version": "v1",
        }
    )
