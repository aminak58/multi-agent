"""Webhook endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


class TestCandleWebhook:
    """Test candle update webhook endpoint."""

    @patch("app.routes.webhooks.process_candle_update")
    def test_receive_candle_update_success(
        self, mock_task, client: TestClient, sample_candle_data
    ):
        """Test successful candle update webhook."""
        # Mock Celery task
        mock_result = Mock()
        mock_result.id = "test-task-123"
        mock_task.delay.return_value = mock_result

        response = client.post("/api/v1/webhooks/candle", json=sample_candle_data)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "accepted"
        assert data["task_id"] == "test-task-123"

        # Verify task was called
        mock_task.delay.assert_called_once()

    def test_receive_candle_update_invalid_data(self, client: TestClient):
        """Test candle update with invalid data."""
        invalid_data = {
            "pair": "BTC/USDT",
            # Missing required fields
        }

        response = client.post("/api/v1/webhooks/candle", json=invalid_data)

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_receive_candle_update_missing_pair(self, client: TestClient):
        """Test candle update with missing pair."""
        invalid_data = {
            "timeframe": "1h",
            "timestamp": "2024-01-01T00:00:00Z",
            "open": 42000.0,
            "high": 42500.0,
            "low": 41800.0,
            "close": 42300.0,
            "volume": 1000.0,
        }

        response = client.post("/api/v1/webhooks/candle", json=invalid_data)
        assert response.status_code == 422

    @patch("app.routes.webhooks.process_candle_update")
    def test_receive_candle_update_task_queued(
        self, mock_task, client: TestClient, sample_candle_data
    ):
        """Test that task is properly queued."""
        mock_result = Mock()
        mock_result.id = "queued-task-456"
        mock_task.delay.return_value = mock_result

        response = client.post("/api/v1/webhooks/candle", json=sample_candle_data)

        assert response.status_code == 200

        # Verify task was called with correct data
        call_args = mock_task.delay.call_args
        assert call_args is not None

        # Task should be called with candle data dict
        task_data = call_args[0][0]
        assert task_data["pair"] == "BTC/USDT"
        assert task_data["timeframe"] == "1h"
