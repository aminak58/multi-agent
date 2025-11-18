"""Health check endpoint tests."""

import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check_success(self, client: TestClient):
        """Test health check returns 200."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_check_has_version(self, client: TestClient):
        """Test health check includes version info."""
        response = client.get("/health")
        data = response.json()

        assert "version" in data
        assert isinstance(data["version"], str)

    def test_health_check_basic_fields(self, client: TestClient):
        """Test health check includes basic fields."""
        response = client.get("/health")
        data = response.json()

        # Basic fields should be present
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
