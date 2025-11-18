"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.utils.cache import cache
from app.clients.freqtrade import freqtrade_client


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis cache."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = None
    mock.ping.return_value = True
    return mock


@pytest.fixture
def mock_freqtrade():
    """Mock Freqtrade client."""
    mock = AsyncMock()
    mock.get_health.return_value = {"status": "healthy"}
    mock.get_candles.return_value = []
    mock.get_open_positions.return_value = []
    mock.create_order.return_value = {"order_id": "test-order-123"}
    mock.dry_run_order.return_value = {
        "valid": True,
        "estimated_cost": 1000.0,
        "estimated_fee": 1.0,
    }
    return mock


@pytest.fixture(autouse=True)
async def setup_mocks(mock_redis, mock_freqtrade, monkeypatch):
    """Auto-setup mocks for all tests."""
    # Mock Redis
    monkeypatch.setattr(cache, "_redis", mock_redis)

    # Mock Freqtrade
    monkeypatch.setattr(freqtrade_client, "_client", mock_freqtrade)
    monkeypatch.setattr(freqtrade_client, "get_health", mock_freqtrade.get_health)
    monkeypatch.setattr(freqtrade_client, "get_candles", mock_freqtrade.get_candles)
    monkeypatch.setattr(freqtrade_client, "get_open_positions", mock_freqtrade.get_open_positions)
    monkeypatch.setattr(freqtrade_client, "create_order", mock_freqtrade.create_order)
    monkeypatch.setattr(freqtrade_client, "dry_run_order", mock_freqtrade.dry_run_order)


@pytest.fixture
def valid_jwt_token():
    """Generate valid JWT token for testing."""
    from app.auth.jwt import create_access_token

    return create_access_token({"sub": "test-user"})


@pytest.fixture
def auth_headers(valid_jwt_token):
    """Authentication headers with valid JWT."""
    return {"Authorization": f"Bearer {valid_jwt_token}"}


@pytest.fixture
def sample_order_request():
    """Sample order request payload."""
    return {
        "request_id": "123e4567-e89b-12d3-a456-426614174000",
        "agent": "test-agent",
        "pair": "BTC/USDT",
        "side": "buy",
        "amount": 0.001,
        "order_type": "market",
    }
