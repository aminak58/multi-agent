"""Unit tests for PositionManager components."""

import pytest
import httpx
from unittest.mock import AsyncMock, Mock, patch
from app.agents.position import (
    PositionManager,
    MCPGatewayClient,
    OrderExecutor,
    TakeProfitManager,
    TrailingStopManager,
)


class TestMCPGatewayClient:
    """Test MCP Gateway Client."""

    def test_initialization(self):
        """Test client initialization."""
        client = MCPGatewayClient(
            base_url="http://test:8000",
            jwt_secret="test-secret"
        )

        assert client.base_url == "http://test:8000"
        assert client.jwt_secret == "test-secret"
        assert client.timeout == 30.0

    def test_compute_hmac_signature(self):
        """Test HMAC signature computation."""
        client = MCPGatewayClient(jwt_secret="test-secret")

        payload = {
            "pair": "BTC/USDT",
            "side": "buy",
            "amount": 0.001,
        }

        signature = client.compute_hmac_signature(payload)

        # Signature should be hex string
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 produces 64 hex chars

        # Same payload should produce same signature
        signature2 = client.compute_hmac_signature(payload)
        assert signature == signature2

    @pytest.mark.asyncio
    async def test_dry_run_order_success(self):
        """Test successful dry-run order."""
        client = MCPGatewayClient(
            base_url="http://test:8000",
            jwt_secret="test-secret"
        )

        mock_response = {
            "valid": True,
            "estimated_cost": 42000.0,
            "estimated_fee": 21.0,
            "warnings": [],
            "errors": [],
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.json = Mock(return_value=mock_response)
            mock_response_obj.raise_for_status = Mock()
            mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response_obj)
            mock_client_cls.return_value = mock_client

            result = await client.dry_run_order(
                pair="BTC/USDT",
                side="buy",
                amount=0.001,
            )

            assert result["valid"] is True
            assert result["estimated_cost"] == 42000.0

    @pytest.mark.asyncio
    async def test_create_order_with_signature(self):
        """Test create order with HMAC signature."""
        client = MCPGatewayClient(
            base_url="http://test:8000",
            jwt_secret="test-secret"
        )

        mock_response = {
            "order_id": "test-order-123",
            "status": "submitted",
            "filled_amount": 0.0,
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.json = Mock(return_value=mock_response)
            mock_response_obj.raise_for_status = Mock()
            mock_post = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__.return_value.post = mock_post
            mock_client_cls.return_value = mock_client

            result = await client.create_order(
                pair="BTC/USDT",
                side="buy",
                amount=0.001,
                stop_loss=41000.0,
                take_profit=43000.0,
            )

            assert result["order_id"] == "test-order-123"

            # Verify X-Signature header was set
            call_kwargs = mock_post.call_args[1]
            assert "headers" in call_kwargs
            assert "X-Signature" in call_kwargs["headers"]


class TestOrderExecutor:
    """Test Order Executor."""

    @pytest.mark.asyncio
    async def test_execute_market_order_success(self):
        """Test successful market order execution."""
        mock_client = Mock()
        mock_client.dry_run_order = AsyncMock(return_value={
            "valid": True,
            "warnings": [],
            "errors": [],
        })
        mock_client.create_order = AsyncMock(return_value={
            "order_id": "order-123",
            "filled_amount": 0.001,
            "price": 42000.0,
            "average_price": 42000.0,
        })

        executor = OrderExecutor(
            mcp_client=mock_client,
            enable_dry_run=True,
        )

        result = await executor.execute_market_order(
            pair="BTC/USDT",
            action="buy",
            amount=0.001,
            stop_loss=41000.0,
            take_profit=43000.0,
        )

        assert result["success"] is True
        assert result["status"] == "executed"
        assert result["order_id"] == "order-123"
        mock_client.dry_run_order.assert_called_once()
        mock_client.create_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_order_dry_run_failed(self):
        """Test order execution when dry-run fails."""
        mock_client = Mock()
        mock_client.dry_run_order = AsyncMock(return_value={
            "valid": False,
            "warnings": [],
            "errors": ["Insufficient balance"],
        })

        executor = OrderExecutor(
            mcp_client=mock_client,
            enable_dry_run=True,
        )

        result = await executor.execute_market_order(
            pair="BTC/USDT",
            action="buy",
            amount=0.001,
        )

        assert result["success"] is False
        assert result["status"] == "rejected"
        assert "Dry-run validation failed" in result["reason"]

    @pytest.mark.asyncio
    async def test_execute_limit_order(self):
        """Test limit order execution."""
        mock_client = Mock()
        mock_client.dry_run_order = AsyncMock(return_value={
            "valid": True,
            "warnings": [],
            "errors": [],
        })
        mock_client.create_order = AsyncMock(return_value={
            "order_id": "limit-order-456",
            "filled_amount": 0.0,  # Not filled yet
        })

        executor = OrderExecutor(
            mcp_client=mock_client,
            enable_dry_run=True,
        )

        result = await executor.execute_limit_order(
            pair="BTC/USDT",
            action="buy",
            amount=0.001,
            price=41500.0,
        )

        assert result["success"] is True
        assert result["order_id"] == "limit-order-456"


class TestTakeProfitManager:
    """Test Take-Profit Manager."""

    def test_setup_take_profit_levels(self):
        """Test TP level setup."""
        manager = TakeProfitManager()

        tp_levels = [
            {"price": 43000, "allocation": 60},
            {"price": 44000, "allocation": 40},
        ]

        result = manager.setup_take_profit_levels(
            pair="BTC/USDT",
            position_size=0.001,
            take_profit_levels=tp_levels,
        )

        assert result["enabled"] is True
        assert result["total_targets"] == 2
        assert len(result["targets"]) == 2
        assert result["targets"][0]["amount"] == 0.0006  # 60% of 0.001
        assert result["targets"][1]["amount"] == 0.0004  # 40% of 0.001

    def test_check_take_profit_hits_buy(self):
        """Test TP hit detection for buy position."""
        manager = TakeProfitManager()

        tp_levels = [
            {"price": 43000, "allocation": 60},
            {"price": 44000, "allocation": 40},
        ]

        manager.setup_take_profit_levels(
            pair="BTC/USDT",
            position_size=0.001,
            take_profit_levels=tp_levels,
        )

        # Price reaches first target
        hit_targets = manager.check_take_profit_hits(
            pair="BTC/USDT",
            current_price=43100,
            action="buy",
        )

        assert len(hit_targets) == 1
        assert hit_targets[0]["price"] == 43000

    def test_check_take_profit_hits_sell(self):
        """Test TP hit detection for sell position."""
        manager = TakeProfitManager()

        tp_levels = [
            {"price": 41000, "allocation": 60},
            {"price": 40000, "allocation": 40},
        ]

        manager.setup_take_profit_levels(
            pair="BTC/USDT",
            position_size=0.001,
            take_profit_levels=tp_levels,
        )

        # Price reaches first target
        hit_targets = manager.check_take_profit_hits(
            pair="BTC/USDT",
            current_price=40900,
            action="sell",
        )

        assert len(hit_targets) == 1
        assert hit_targets[0]["price"] == 41000

    def test_get_remaining_position(self):
        """Test remaining position calculation."""
        manager = TakeProfitManager()

        tp_levels = [
            {"price": 43000, "allocation": 60},
            {"price": 44000, "allocation": 40},
        ]

        manager.setup_take_profit_levels(
            pair="BTC/USDT",
            position_size=0.001,
            take_profit_levels=tp_levels,
        )

        # Hit first target
        manager.check_take_profit_hits("BTC/USDT", 43100, "buy")
        manager.mark_target_executed("BTC/USDT", 43000, "order-123")

        remaining = manager.get_remaining_position("BTC/USDT")

        assert remaining["remaining_pct"] == 40.0  # 60% closed
        assert remaining["closed_pct"] == 60.0
        assert remaining["targets_hit"] == 1


class TestTrailingStopManager:
    """Test Trailing Stop Manager."""

    def test_setup_trailing_stop(self):
        """Test trailing stop setup."""
        manager = TrailingStopManager(
            trailing_distance_pct=0.02,
            activation_profit_pct=0.01,
        )

        result = manager.setup_trailing_stop(
            pair="BTC/USDT",
            entry_price=42000,
            action="buy",
            initial_stop_loss=41000,
        )

        assert result["enabled"] is True
        assert result["trailing_distance"] == 2.0  # 2%
        assert result["activation_price"] == 42420.0  # 1% above entry

    def test_update_trailing_stop_buy(self):
        """Test trailing stop update for buy position."""
        manager = TrailingStopManager(
            trailing_distance_pct=0.02,
            activation_profit_pct=0.01,
        )

        manager.setup_trailing_stop(
            pair="BTC/USDT",
            entry_price=42000,
            action="buy",
            initial_stop_loss=41000,
        )

        # Price hasn't reached activation yet (42420 = 42000 * 1.01)
        update1 = manager.update_trailing_stop("BTC/USDT", 42300)
        assert update1 is None  # Not activated yet (42300 < 42420)

        # Price activates trailing (42500 > 42420)
        update2 = manager.update_trailing_stop("BTC/USDT", 42500)
        assert update2 is not None
        assert update2["updated"] is True
        assert update2["new_stop"] > 41000  # Stop moved up

        # Price continues up
        update3 = manager.update_trailing_stop("BTC/USDT", 43000)
        assert update3 is not None
        assert update3["updated"] is True
        assert update3["new_stop"] > update2["new_stop"]  # Stop moved further up

    def test_update_trailing_stop_sell(self):
        """Test trailing stop update for sell position."""
        manager = TrailingStopManager(
            trailing_distance_pct=0.02,
            activation_profit_pct=0.01,
        )

        manager.setup_trailing_stop(
            pair="BTC/USDT",
            entry_price=42000,
            action="sell",
            initial_stop_loss=43000,
        )

        # Price moves down past activation
        manager.update_trailing_stop("BTC/USDT", 41500)

        # Price continues down
        update = manager.update_trailing_stop("BTC/USDT", 41000)
        assert update is not None
        assert update["updated"] is True
        assert update["new_stop"] < 43000  # Stop moved down

    def test_check_stop_hit_buy(self):
        """Test stop hit detection for buy position."""
        manager = TrailingStopManager()

        manager.setup_trailing_stop(
            pair="BTC/USDT",
            entry_price=42000,
            action="buy",
            initial_stop_loss=41000,
        )

        # Price above stop
        assert manager.check_stop_hit("BTC/USDT", 42500) is False

        # Price at stop
        assert manager.check_stop_hit("BTC/USDT", 41000) is True

        # Price below stop
        assert manager.check_stop_hit("BTC/USDT", 40500) is True

    def test_get_status(self):
        """Test trailing stop status."""
        manager = TrailingStopManager()

        manager.setup_trailing_stop(
            pair="BTC/USDT",
            entry_price=42000,
            action="buy",
            initial_stop_loss=41000,
        )

        status = manager.get_status("BTC/USDT")

        assert status["enabled"] is True
        assert status["activated"] is False
        assert status["current_stop"] == 41000
        assert status["entry_price"] == 42000


class TestPositionManager:
    """Test PositionManager agent."""

    @pytest.mark.asyncio
    async def test_process_approved_trade(self):
        """Test processing approved trade."""
        config = {
            "enable_dry_run": True,
            "enable_trailing_stop": True,
        }

        manager = PositionManager(config=config)

        # Mock the order executor
        manager.order_executor.execute_market_order = AsyncMock(return_value={
            "success": True,
            "status": "executed",
            "order_id": "test-order-789",
            "request_id": "req-123",
            "filled_amount": 0.001,
            "average_price": 42000.0,
        })

        risk_decision = {
            "approved": True,
            "pair": "BTC/USDT",
            "action": "buy",
            "position_size": 0.001,
            "entry_price": 42000.0,
            "stop_loss": 41000.0,
            "take_profit": 43000.0,
            "take_profit_levels": [
                {"price": 43000, "allocation": 60},
                {"price": 44000, "allocation": 40},
            ],
            "risk_score": 0.3,
        }

        result = await manager.process(risk_decision)

        assert result["success"] is True
        assert result["status"] == "executed"
        assert result["order_id"] == "test-order-789"
        assert result["take_profit_config"] is not None
        assert result["trailing_stop_config"] is not None

    @pytest.mark.asyncio
    async def test_process_rejected_trade(self):
        """Test processing rejected trade."""
        manager = PositionManager()

        risk_decision = {
            "approved": False,
            "warnings": ["Risk too high"],
        }

        result = await manager.process(risk_decision)

        assert result["success"] is False
        assert result["status"] == "rejected"
        assert "not approved" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_process_missing_required_fields(self):
        """Test with missing required fields."""
        manager = PositionManager()

        risk_decision = {
            "approved": True,
            # Missing pair, action, position_size
        }

        result = await manager.process(risk_decision)

        assert result["success"] is False
        assert "missing required" in result["reason"].lower()

    def test_get_position_status(self):
        """Test get position status."""
        manager = PositionManager(config={"enable_trailing_stop": True})

        # Setup TP and trailing stop
        manager.tp_manager.setup_take_profit_levels(
            pair="BTC/USDT",
            position_size=0.001,
            take_profit_levels=[{"price": 43000, "allocation": 100}],
        )

        manager.trailing_stop.setup_trailing_stop(
            pair="BTC/USDT",
            entry_price=42000,
            action="buy",
            initial_stop_loss=41000,
        )

        status = manager.get_position_status("BTC/USDT")

        assert status["pair"] == "BTC/USDT"
        assert status["take_profit"]["enabled"] is True
        assert status["trailing_stop"]["enabled"] is True
