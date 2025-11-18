"""Tests for health endpoint."""

import pytest
from fastapi.testclient import TestClient


def test_health_check_success(client: TestClient):
    """Test health check returns 200 when all services are healthy."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["healthy", "degraded"]
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data
    assert "redis" in data["services"]
    assert "freqtrade" in data["services"]


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns service info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["service"] == "MCP Gateway"
    assert "version" in data
    assert data["status"] == "running"
