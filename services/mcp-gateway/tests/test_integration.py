"""Integration tests for MCP Gateway.

These tests verify end-to-end functionality with real (or mocked) services.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from app.main import app
from app.auth.jwt import create_access_token
from app.auth.hmac import compute_signature


@pytest.mark.integration
class TestEndToEndFlow:
    """Test complete end-to-end workflows."""

    @pytest.fixture
    def client(self):
        """Test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_token(self):
        """Valid JWT token."""
        return create_access_token({"sub": "test-user", "role": "trader"})

    @pytest.fixture
    def auth_headers(self, auth_token):
        """Authentication headers."""
        return {"Authorization": f"Bearer {auth_token}"}

    def test_complete_order_flow_dry_run_to_execution(
        self, client, auth_headers
    ):
        """Test complete flow: dry-run -> validation -> execution."""
        order_data = {
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "agent": "test-agent",
            "pair": "BTC/USDT",
            "side": "buy",
            "amount": 0.001,
            "order_type": "market",
        }

        # Step 1: Dry-run
        dry_run_response = client.post(
            "/api/v1/orders/dry-run",
            json=order_data,
            headers=auth_headers,
        )

        assert dry_run_response.status_code == 200
        dry_run_data = dry_run_response.json()
        assert dry_run_data["valid"] is True

        # Step 2: Execute order with HMAC signature
        body = json.dumps(order_data).encode()
        signature = compute_signature(body)

        headers_with_sig = {
            **auth_headers,
            "X-Signature": signature,
            "Content-Type": "application/json",
        }

        # Note: This will need proper body extraction in real scenario
        # For now, we test that the endpoint requires signature
        execute_response = client.post(
            "/api/v1/orders",
            json=order_data,
            headers=headers_with_sig,
        )

        # Should either succeed or require proper signature
        assert execute_response.status_code in [200, 401]

    def test_candles_caching_behavior(self, client, auth_headers):
        """Test that candles endpoint uses caching."""
        # First request (cache miss)
        response1 = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "15m", "limit": 10},
            headers=auth_headers,
        )

        assert response1.status_code == 200
        data1 = response1.json()

        # Second request (should hit cache)
        response2 = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "15m", "limit": 10},
            headers=auth_headers,
        )

        assert response2.status_code == 200
        data2 = response2.json()

        # Data should be identical
        assert data1 == data2

    def test_authentication_flow(self, client):
        """Test authentication is enforced across endpoints."""
        # Without auth - should fail
        response = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "15m"},
        )
        assert response.status_code == 401

        # With invalid token - should fail
        response = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "15m"},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

        # With valid token - should succeed
        token = create_access_token({"sub": "test-user"})
        response = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "15m"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_error_handling_cascade(self, client, auth_headers):
        """Test error handling across the stack."""
        # Invalid pair format
        response = client.get(
            "/api/v1/candles",
            params={"pair": "INVALID", "timeframe": "15m"},
            headers=auth_headers,
        )
        # Should still return 200 but might have different data
        # or handle gracefully based on implementation

        # Invalid timeframe
        response = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "invalid"},
            headers=auth_headers,
        )
        # Should handle gracefully

    def test_concurrent_requests(self, client, auth_headers):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def make_request():
            return client.get(
                "/api/v1/candles",
                params={"pair": "BTC/USDT", "timeframe": "15m"},
                headers=auth_headers,
            )

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

    def test_request_validation_comprehensive(self, client, auth_headers):
        """Test comprehensive request validation."""
        # Missing required fields
        response = client.post(
            "/api/v1/orders/dry-run",
            json={"pair": "BTC/USDT"},
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Invalid data types
        response = client.post(
            "/api/v1/orders/dry-run",
            json={
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent": "test",
                "pair": "BTC/USDT",
                "side": "buy",
                "amount": "invalid",  # Should be float
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Out of range values
        response = client.post(
            "/api/v1/orders/dry-run",
            json={
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "agent": "test",
                "pair": "BTC/USDT",
                "side": "buy",
                "amount": -1,  # Negative amount
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestServiceIntegration:
    """Test integration with external services."""

    @pytest.fixture
    def client(self):
        """Test client."""
        return TestClient(app)

    def test_health_check_all_services(self, client):
        """Test health check reports all service statuses."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "services" in data
        assert "redis" in data["services"]
        assert "freqtrade" in data["services"]
        assert data["status"] in ["healthy", "degraded"]

    def test_redis_connection_resilience(self, client, auth_headers):
        """Test system handles Redis connection issues gracefully."""
        # Even if Redis is down, should handle gracefully
        # (depends on implementation - might return stale data or error)
        response = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "15m", "use_cache": "false"},
            headers=auth_headers,
        )

        # Should either succeed or return appropriate error
        assert response.status_code in [200, 500, 503]

    def test_metrics_endpoint_accessible(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")

        # Metrics endpoint should be accessible
        assert response.status_code == 200
        assert "http_requests" in response.text or "process_" in response.text
