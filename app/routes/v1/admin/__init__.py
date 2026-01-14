"""
Admin Routes Package
====================
Administrative routes for managing RBAC and other admin operations.

All routes in this package require admin privileges.
"""

from flask_openapi3 import APIBlueprint, Tag

# Tag for grouping admin endpoints in Swagger UI
admin_tag = Tag(
    name="Admin (v1)",
    description="Administrative operations - Requires admin privileges",
)

# Parent blueprint for all admin routes
admin_bp = APIBlueprint(
    "admin_v1",
    __name__,
    url_prefix="/admin",
    abp_tags=[admin_tag],
)

from app.routes.v1.admin.permissions import permissions_bp  # noqa: E402

# Import and register child blueprints
from app.routes.v1.admin.roles import roles_bp  # noqa: E402

admin_bp.register_api(roles_bp)
admin_bp.register_api(permissions_bp)
