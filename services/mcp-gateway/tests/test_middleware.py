"""Tests for middleware components."""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter
from slowapi.util import get_remote_address


class TestRateLimiting:
    """Test rate limiting middleware."""

    @pytest.fixture
    def app_with_rate_limit(self):
        """Create app with rate limiting."""
        from app.middleware.rate_limit import limiter

        app = FastAPI()
        app.state.limiter = limiter

        @app.get("/test")
        @limiter.limit("2/minute")
        async def test_endpoint(request: Request):
            return {"message": "success"}

        return app

    def test_rate_limit_allows_within_limit(self, app_with_rate_limit):
        """Test requests within rate limit are allowed."""
        client = TestClient(app_with_rate_limit)

        # First request should succeed
        response1 = client.get("/test")
        assert response1.status_code == 200

        # Second request should succeed
        response2 = client.get("/test")
        assert response2.status_code == 200

    def test_rate_limit_blocks_over_limit(self, app_with_rate_limit):
        """Test requests over rate limit are blocked."""
        client = TestClient(app_with_rate_limit)

        # First two requests succeed
        client.get("/test")
        client.get("/test")

        # Third request should be rate limited
        response3 = client.get("/test")
        assert response3.status_code == 429

    def test_rate_limit_headers(self, app_with_rate_limit):
        """Test rate limit headers are present."""
        client = TestClient(app_with_rate_limit)

        response = client.get("/test")

        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers or "Retry-After" in response.headers
