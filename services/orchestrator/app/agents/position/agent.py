"""PositionManager - Order execution and position management."""

from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.base import BaseAgent
from app.agents.position.mcp_client import MCPGatewayClient
from app.agents.position.order_executor import OrderExecutor
from app.agents.position.take_profit_manager import TakeProfitManager
from app.agents.position.trailing_stop import TrailingStopManager


class PositionManager(BaseAgent):
    """
    Position management agent for order execution and monitoring.

    Responsibilities:
    - Execute orders via MCP Gateway
    - Validate orders with dry-run before execution
    - Manage partial take-profit exits
    - Implement trailing stop-loss
    - HMAC signing for secure requests
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize PositionManager.

        Args:
            config: Configuration dictionary
                - mcp_gateway_url: MCP Gateway URL
                - mcp_jwt_secret: JWT secret for HMAC
                - enable_dry_run: Validate with dry-run (default: True)
                - enable_trailing_stop: Enable trailing stops (default: True)
                - trailing_distance_pct: Trailing distance % (default: 0.02)
                - max_retries: Max order retry attempts (default: 3)
        """
        super().__init__(config)

        # Get configuration
        mcp_gateway_url = self.get_config_value("mcp_gateway_url", None)
        mcp_jwt_secret = self.get_config_value("mcp_jwt_secret", None)
        enable_dry_run = self.get_config_value("enable_dry_run", True)
        max_retries = self.get_config_value("max_retries", 3)

        # Initialize MCP client
        self.mcp_client = MCPGatewayClient(
            base_url=mcp_gateway_url,
            jwt_secret=mcp_jwt_secret,
        )

        # Initialize order executor
        self.order_executor = OrderExecutor(
            mcp_client=self.mcp_client,
            enable_dry_run=enable_dry_run,
            max_retries=max_retries,
        )

        # Initialize take-profit manager
        self.tp_manager = TakeProfitManager()

        # Initialize trailing stop manager
        self.enable_trailing_stop = self.get_config_value("enable_trailing_stop", True)
        if self.enable_trailing_stop:
            trailing_distance = self.get_config_value("trailing_distance_pct", 0.02)
            activation_profit = self.get_config_value("trailing_activation_pct", 0.01)
            self.trailing_stop = TrailingStopManager(
                trailing_distance_pct=trailing_distance,
                activation_profit_pct=activation_profit,
            )
        else:
            self.trailing_stop = None

    async def process(
        self,
        risk_decision: Dict[str, Any],
        candle_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Process risk decision and execute order.

        Args:
            risk_decision: Decision from RiskAgent
            candle_data: Optional candle data for context

        Returns:
            Position execution result
        """
        # Validate input
        if not risk_decision:
            return self._create_rejection("Invalid input: missing risk_decision")

        # Check if trade is approved
        if not risk_decision.get("approved"):
            return self._create_rejection(
                "Trade not approved by RiskAgent",
                risk_decision=risk_decision,
            )

        # Extract order parameters
        pair = risk_decision.get("pair")
        action = risk_decision.get("action")
        position_size = risk_decision.get("position_size")
        entry_price = risk_decision.get("entry_price")
        stop_loss = risk_decision.get("stop_loss")
        take_profit = risk_decision.get("take_profit")
        take_profit_levels = risk_decision.get("take_profit_levels", [])

        # Validate required fields
        if not all([pair, action, position_size]):
            return self._create_rejection("Missing required order fields")

        if action not in ["buy", "sell"]:
            return self._create_rejection(f"Invalid action: {action}")

        try:
            # Prepare metadata
            meta = {
                "risk_score": risk_decision.get("risk_score"),
                "confidence": risk_decision.get("confidence"),
                "risk_reward_ratio": risk_decision.get("risk_reward_ratio"),
                "signal_source": "RiskAgent",
            }

            # Execute order
            execution_result = await self.order_executor.execute_market_order(
                pair=pair,
                action=action,
                amount=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                meta=meta,
            )

            if not execution_result["success"]:
                return self._create_rejection(
                    execution_result.get("reason", "Order execution failed"),
                    execution_result=execution_result,
                )

            # Setup partial take-profit if enabled
            tp_config = None
            if take_profit_levels and len(take_profit_levels) > 0:
                tp_config = self.tp_manager.setup_take_profit_levels(
                    pair=pair,
                    position_size=position_size,
                    take_profit_levels=take_profit_levels,
                )

            # Setup trailing stop if enabled
            trailing_config = None
            if self.enable_trailing_stop and stop_loss:
                trailing_config = self.trailing_stop.setup_trailing_stop(
                    pair=pair,
                    entry_price=entry_price,
                    action=action,
                    initial_stop_loss=stop_loss,
                )

            # Build final result
            result = {
                "success": True,
                "status": "executed",
                "order_id": execution_result["order_id"],
                "request_id": execution_result["request_id"],
                "pair": pair,
                "action": action,
                "position_size": position_size,
                "entry_price": entry_price,
                "filled_amount": execution_result.get("filled_amount", 0.0),
                "average_price": execution_result.get("average_price", entry_price),
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "take_profit_config": tp_config,
                "trailing_stop_config": trailing_config,
                "execution_details": execution_result,
                "timestamp": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as e:
            return self._create_rejection(
                f"Error executing position: {str(e)}",
                error=str(e),
            )

    async def update_position(
        self,
        pair: str,
        current_price: float,
    ) -> Dict[str, Any]:
        """
        Update position with current market price.

        This checks trailing stops and partial take-profit targets.

        Args:
            pair: Trading pair
            current_price: Current market price

        Returns:
            Update result with any actions taken
        """
        result = {
            "pair": pair,
            "current_price": current_price,
            "actions_taken": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Check trailing stop updates
        if self.enable_trailing_stop and self.trailing_stop.is_enabled(pair):
            trailing_update = self.trailing_stop.update_trailing_stop(pair, current_price)
            if trailing_update and trailing_update.get("updated"):
                result["actions_taken"].append({
                    "type": "trailing_stop_updated",
                    "details": trailing_update,
                })

            # Check if stop was hit
            if self.trailing_stop.check_stop_hit(pair, current_price):
                result["actions_taken"].append({
                    "type": "stop_loss_hit",
                    "stop_price": self.trailing_stop.get_current_stop(pair),
                    "current_price": current_price,
                    "action_required": "close_position",
                })

        # Check take-profit hits (would need position action from database)
        # This is a simplified version - full implementation would track position state

        return result

    def get_position_status(self, pair: str) -> Dict[str, Any]:
        """
        Get current status of a position.

        Args:
            pair: Trading pair

        Returns:
            Complete position status
        """
        status = {
            "pair": pair,
            "take_profit": self.tp_manager.get_status(pair),
            "trailing_stop": self.trailing_stop.get_status(pair) if self.trailing_stop else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        return status

    def _create_rejection(
        self,
        reason: str,
        error: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a rejection result."""
        result = {
            "success": False,
            "status": "rejected",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if error:
            result["error"] = error

        # Add any additional fields
        result.update(kwargs)

        return result
