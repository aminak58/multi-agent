"""Test configuration and fixtures."""

import os
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

# Set environment variables before importing app modules
os.environ.setdefault("RABBITMQ_USER", "test_user")
os.environ.setdefault("RABBITMQ_PASSWORD", "test_password")
os.environ.setdefault("REDIS_PASSWORD", "test_redis_password")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("MCP_JWT_SECRET", "test-jwt-secret-for-testing")
os.environ.setdefault("MCP_GATEWAY_URL", "http://localhost:8000/api/v1")

from fastapi.testclient import TestClient
from app.main import app
from app.celery_app import celery_app


@pytest.fixture(scope="session")
def celery_config():
    """Celery test configuration."""
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,  # Execute tasks synchronously
        "task_eager_propagates": True,  # Propagate exceptions
    }


@pytest.fixture(scope="session")
def celery_enable_logging():
    """Enable Celery logging in tests."""
    return True


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Test client for FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_celery_task():
    """Mock Celery task result."""
    mock_result = Mock()
    mock_result.id = "test-task-id-123"
    mock_result.status = "PENDING"
    return mock_result


@pytest.fixture
def sample_candle_data():
    """Sample candle data for testing."""
    return {
        "pair": "BTC/USDT",
        "timeframe": "1h",
        "timestamp": 1704067200,  # Unix timestamp for 2024-01-01T00:00:00Z
        "open": 42000.0,
        "high": 42500.0,
        "low": 41800.0,
        "close": 42300.0,
        "volume": 1000.0,
    }


@pytest.fixture
def sample_signal_decision():
    """Sample signal decision for testing."""
    return {
        "action": "buy",
        "confidence": 0.8,
        "reasoning": "Strong bullish signal",
        "indicators": {
            "ema_cross": True,
            "rsi": 65.0,
            "macd": 120.0,
        },
        "llm_used": False,
    }


@pytest.fixture
def sample_risk_decision():
    """Sample risk decision for testing."""
    return {
        "approved": True,
        "position_size": 0.1,
        "stop_loss": 41000.0,
        "take_profit": 44000.0,
        "risk_score": 0.3,
        "warnings": [],
    }


@pytest.fixture
def sample_order_execution():
    """Sample order execution result for testing."""
    return {
        "status": "executed",
        "order_id": "order-123",
        "pair": "BTC/USDT",
        "side": "buy",
        "amount": 0.1,
        "price": 42300.0,
        "stop_loss": 41000.0,
        "take_profit": 44000.0,
    }
