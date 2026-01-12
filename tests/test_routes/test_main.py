"""
Tests for Main Routes.

These tests verify the main/health check endpoints.
"""

import json


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "Welcome" in data["data"]["message"]
        assert data["data"]["status"] == "running"

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["status"] in ["healthy", "degraded"]
        assert data["data"]["database"] in ["connected", "disconnected"]
