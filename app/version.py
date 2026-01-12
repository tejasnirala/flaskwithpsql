"""
Version information for the application.

Single source of truth for version number to avoid inconsistencies.

Usage:
    from app.version import __version__
"""

__version__ = "1.0.0"
__version_info__ = tuple(int(x) for x in __version__.split("."))
