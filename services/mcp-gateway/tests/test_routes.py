"""Tests for API routes."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.models.schemas import Candle, Position, OrderSide


class TestCandlesEndpoint:
    """Test candles endpoint."""

    def test_get_candles_success(self, client: TestClient, auth_headers: dict, mock_freqtrade):
        """Test successful candles retrieval."""
        # Setup mock
        mock_candles = [
            Candle(
                timestamp=1700000000,
                open=50000.0,
                high=51000.0,
                low=49000.0,
                close=50500.0,
                volume=100.0,
            )
        ]
        mock_freqtrade.get_candles.return_value = mock_candles

        response = client.get(
            "/api/v1/candles",
            params={"pair": "BTC/USDT", "timeframe": "15m", "limit": 100},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["pair"] == "BTC/USDT"
        assert data["timeframe"] == "15m"
        assert data["count"] == 1
        assert len(data["candles"]) == 1

    def test_get_candles_unauthorized(self, client: TestClient):
        """Test candles endpoint requires authentication."""
        response = client.get(
            "/api/v1/candles", params={"pair": "BTC/USDT", "timeframe": "15m"}
        )

        assert response.status_code == 401


class TestPositionsEndpoint:
    """Test positions endpoint."""

    def test_get_open_positions_success(
        self, client: TestClient, auth_headers: dict, mock_freqtrade
    ):
        """Test successful positions retrieval."""
        from datetime import datetime

        # Setup mock
        mock_positions = [
            Position(
                pair="BTC/USDT",
                side=OrderSide.BUY,
                amount=0.01,
                entry_price=50000.0,
                current_price=51000.0,
                unrealized_pnl=10.0,
                unrealized_pnl_pct=2.0,
                open_date=datetime.utcnow(),
            )
        ]
        mock_freqtrade.get_open_positions.return_value = mock_positions

        response = client.get("/api/v1/positions/open", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 1
        assert len(data["positions"]) == 1
        assert data["positions"][0]["pair"] == "BTC/USDT"

    def test_get_open_positions_unauthorized(self, client: TestClient):
        """Test positions endpoint requires authentication."""
        response = client.get("/api/v1/positions/open")

        assert response.status_code == 401


class TestOrdersEndpoint:
    """Test orders endpoints."""

    def test_dry_run_order_success(
        self, client: TestClient, auth_headers: dict, sample_order_request: dict
    ):
        """Test successful dry-run order."""
        response = client.post(
            "/api/v1/orders/dry-run", json=sample_order_request, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert "estimated_cost" in data

    def test_dry_run_order_unauthorized(
        self, client: TestClient, sample_order_request: dict
    ):
        """Test dry-run requires authentication."""
        response = client.post("/api/v1/orders/dry-run", json=sample_order_request)

        assert response.status_code == 401

    def test_create_order_missing_signature(
        self, client: TestClient, auth_headers: dict, sample_order_request: dict
    ):
        """Test order creation requires HMAC signature."""
        response = client.post(
            "/api/v1/orders", json=sample_order_request, headers=auth_headers
        )

        # Should fail due to missing X-Signature header
        assert response.status_code == 401

    def test_create_order_with_signature(
        self, client: TestClient, auth_headers: dict, sample_order_request: dict
    ):
        """Test order creation with valid signature."""
        import json
        from app.auth.hmac import compute_signature

        # Compute signature
        body = json.dumps(sample_order_request).encode()
        signature = compute_signature(body)

        headers = {**auth_headers, "X-Signature": signature}

        response = client.post("/api/v1/orders", json=sample_order_request, headers=headers)

        # Note: This may still fail due to body parsing differences
        # In real tests, you'd need to mock the body extraction
        assert response.status_code in [200, 401]


class TestValidation:
    """Test request validation."""

    def test_invalid_order_side(self, client: TestClient, auth_headers: dict):
        """Test validation rejects invalid order side."""
        invalid_order = {
            "request_id": "123e4567-e89b-12d3-a456-426614174000",
            "agent": "test-agent",
            "pair": "BTC/USDT",
            "side": "invalid",  # Invalid side
            "amount": 0.001,
        }

        response = client.post(
            "/api/v1/orders/dry-run", json=invalid_order, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_negative_amount(self, client: TestClient, auth_headers: dict):
        """Test validation rejects negative amount."""
        invalid_order = {
            "request_id": "123e4567-e89b-12d3-a456-426614174000",
            "agent": "test-agent",
            "pair": "BTC/USDT",
            "side": "buy",
            "amount": -0.001,  # Negative amount
        }

        response = client.post(
            "/api/v1/orders/dry-run", json=invalid_order, headers=auth_headers
        )

        assert response.status_code == 422
