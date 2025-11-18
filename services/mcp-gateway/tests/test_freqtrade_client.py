"""Tests for Freqtrade client."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.clients.freqtrade import FreqtradeClient
from app.models.schemas import Candle, Position, OrderSide


@pytest.mark.asyncio
class TestFreqtradeClient:
    """Test FreqtradeClient."""

    @pytest.fixture
    async def client(self):
        """Create Freqtrade client with mocked httpx."""
        client = FreqtradeClient()
        mock_httpx = AsyncMock()
        client._client = mock_httpx
        return client

    async def test_connect(self):
        """Test client connection initialization."""
        client = FreqtradeClient()

        with patch('httpx.AsyncClient') as mock_client:
            await client.connect()

            mock_client.assert_called_once()
            assert client._client is not None

    async def test_disconnect(self, client):
        """Test client disconnection."""
        await client.disconnect()

        client._client.aclose.assert_called_once()

    async def test_get_candles_success(self, client):
        """Test successful candles retrieval."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "data": [
                [1700000000000, 50000.0, 51000.0, 49000.0, 50500.0, 100.0],
                [1700000900000, 50500.0, 51500.0, 50000.0, 51000.0, 150.0],
            ]
        }
        mock_response.raise_for_status = AsyncMock()

        client._client.request.return_value = mock_response

        result = await client.get_candles("BTC/USDT", "15m", limit=2)

        assert len(result) == 2
        assert isinstance(result[0], Candle)
        assert result[0].timestamp == 1700000000000
        assert result[0].open == 50000.0
        assert result[0].close == 50500.0
        assert result[1].timestamp == 1700000900000

    async def test_get_candles_empty_response(self, client):
        """Test candles retrieval with empty response."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = AsyncMock()

        client._client.request.return_value = mock_response

        result = await client.get_candles("BTC/USDT", "15m")

        assert result == []

    async def test_get_candles_http_error(self, client):
        """Test candles retrieval with HTTP error."""
        client._client.request.side_effect = httpx.HTTPError("Connection failed")

        with pytest.raises(httpx.HTTPError):
            await client.get_candles("BTC/USDT", "15m")

    async def test_get_open_positions_success(self, client):
        """Test successful open positions retrieval."""
        mock_response = AsyncMock()
        mock_response.json.return_value = [
            {
                "pair": "BTC/USDT",
                "is_open": True,
                "amount": 0.01,
                "open_rate": 50000.0,
                "current_rate": 51000.0,
                "profit_abs": 10.0,
                "profit_ratio": 0.02,
                "stop_loss_abs": 49000.0,
                "open_date": "2025-11-18T10:00:00Z",
            }
        ]
        mock_response.raise_for_status = AsyncMock()

        client._client.request.return_value = mock_response

        result = await client.get_open_positions()

        assert len(result) == 1
        assert isinstance(result[0], Position)
        assert result[0].pair == "BTC/USDT"
        assert result[0].amount == 0.01
        assert result[0].entry_price == 50000.0
        assert result[0].unrealized_pnl == 10.0

    async def test_get_open_positions_empty(self, client):
        """Test open positions with no positions."""
        mock_response = AsyncMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = AsyncMock()

        client._client.request.return_value = mock_response

        result = await client.get_open_positions()

        assert result == []

    async def test_create_order_buy_success(self, client):
        """Test successful buy order creation."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "order_id": "test-order-123",
            "status": "submitted",
        }
        mock_response.raise_for_status = AsyncMock()

        client._client.request.return_value = mock_response

        result = await client.create_order(
            pair="BTC/USDT",
            side="buy",
            amount=0.001,
            order_type="market",
        )

        assert result["order_id"] == "test-order-123"
        client._client.request.assert_called_once()
        call_args = client._client.request.call_args
        assert call_args[0][0] == "POST"
        assert "forcebuy" in call_args[0][1]

    async def test_create_order_sell_success(self, client):
        """Test successful sell order creation."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "order_id": "test-order-456",
            "status": "submitted",
        }
        mock_response.raise_for_status = AsyncMock()

        client._client.request.return_value = mock_response

        result = await client.create_order(
            pair="BTC/USDT",
            side="sell",
            amount=0.001,
            order_type="market",
        )

        assert result["order_id"] == "test-order-456"
        call_args = client._client.request.call_args
        assert "forcesell" in call_args[0][1]

    async def test_create_order_with_limit_price(self, client):
        """Test order creation with limit price."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"order_id": "limit-order"}
        mock_response.raise_for_status = AsyncMock()

        client._client.request.return_value = mock_response

        result = await client.create_order(
            pair="BTC/USDT",
            side="buy",
            amount=0.001,
            order_type="limit",
            price=50000.0,
        )

        call_args = client._client.request.call_args
        payload = call_args[1]["json"]
        assert payload["price"] == 50000.0
        assert payload["ordertype"] == "limit"

    async def test_create_order_error(self, client):
        """Test order creation error handling."""
        client._client.request.side_effect = httpx.HTTPError("Order failed")

        with pytest.raises(httpx.HTTPError):
            await client.create_order("BTC/USDT", "buy", 0.001)

    async def test_dry_run_order_valid(self, client):
        """Test dry-run with valid order."""
        mock_balance = AsyncMock()
        mock_balance.json.return_value = {"BTC": 1.0, "USDT": 10000.0}
        mock_balance.raise_for_status = AsyncMock()

        mock_config = AsyncMock()
        mock_config.json.return_value = {
            "exchange": {"pair_whitelist": ["BTC/USDT", "ETH/USDT"]}
        }
        mock_config.raise_for_status = AsyncMock()

        client._client.request.side_effect = [mock_balance, mock_config]

        result = await client.dry_run_order("BTC/USDT", "buy", 0.001)

        assert result["valid"] is True
        assert "estimated_cost" in result
        assert "estimated_fee" in result

    async def test_dry_run_order_invalid_pair(self, client):
        """Test dry-run with invalid pair."""
        mock_balance = AsyncMock()
        mock_balance.json.return_value = {}
        mock_balance.raise_for_status = AsyncMock()

        mock_config = AsyncMock()
        mock_config.json.return_value = {
            "exchange": {"pair_whitelist": ["ETH/USDT"]}
        }
        mock_config.raise_for_status = AsyncMock()

        client._client.request.side_effect = [mock_balance, mock_config]

        result = await client.dry_run_order("BTC/USDT", "buy", 0.001)

        assert result["valid"] is False
        assert len(result.get("errors", [])) > 0

    async def test_dry_run_order_error(self, client):
        """Test dry-run with error."""
        client._client.request.side_effect = Exception("API error")

        result = await client.dry_run_order("BTC/USDT", "buy", 0.001)

        assert result["valid"] is False
        assert "API error" in result.get("errors", [])[0]

    async def test_get_health_success(self, client):
        """Test health check success."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = AsyncMock()

        client._client.request.return_value = mock_response

        result = await client.get_health()

        assert result["status"] == "healthy"
        assert "response" in result

    async def test_get_health_failure(self, client):
        """Test health check failure."""
        client._client.request.side_effect = Exception("Connection timeout")

        result = await client.get_health()

        assert result["status"] == "unhealthy"
        assert "error" in result
