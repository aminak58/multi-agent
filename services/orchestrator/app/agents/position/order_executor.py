"""Order execution with retry logic and validation."""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class OrderExecutor:
    """
    Handles order execution with validation and retry logic.
    """

    def __init__(
        self,
        mcp_client,
        enable_dry_run: bool = True,
        max_retries: int = 3,
    ):
        """
        Initialize OrderExecutor.

        Args:
            mcp_client: MCP Gateway client instance
            enable_dry_run: Always validate with dry-run before execution
            max_retries: Maximum retry attempts for failed orders
        """
        self.mcp_client = mcp_client
        self.enable_dry_run = enable_dry_run
        self.max_retries = max_retries

    async def execute_order(
        self,
        pair: str,
        action: str,
        amount: float,
        entry_price: float,
        order_type: str = "market",
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        leverage: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute order with optional dry-run validation.

        Args:
            pair: Trading pair
            action: "buy" or "sell"
            amount: Order amount
            entry_price: Expected entry price
            order_type: Order type ("market" or "limit")
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            leverage: Leverage multiplier
            meta: Additional metadata

        Returns:
            Order execution result
        """
        request_id = str(uuid.uuid4())

        # Prepare order parameters
        order_params = {
            "pair": pair,
            "side": action,
            "amount": amount,
            "order_type": order_type,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "leverage": leverage,
            "request_id": request_id,
            "agent": "PositionManager",
            "meta": meta or {},
        }

        # Add limit price for limit orders
        if order_type == "limit":
            order_params["price"] = entry_price

        # Dry-run validation
        if self.enable_dry_run:
            dry_run_result = await self._dry_run_validation(order_params)

            if not dry_run_result["valid"]:
                return {
                    "success": False,
                    "status": "rejected",
                    "reason": "Dry-run validation failed",
                    "dry_run_result": dry_run_result,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        # Execute order with retry logic
        for attempt in range(self.max_retries):
            try:
                result = await self.mcp_client.create_order(**order_params)

                return {
                    "success": True,
                    "status": "executed",
                    "order_id": result.get("order_id"),
                    "request_id": request_id,
                    "pair": pair,
                    "side": action,
                    "amount": amount,
                    "filled_amount": result.get("filled_amount", 0.0),
                    "price": result.get("price"),
                    "average_price": result.get("average_price"),
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "timestamp": datetime.utcnow().isoformat(),
                    "attempt": attempt + 1,
                }

            except Exception as e:
                if attempt == self.max_retries - 1:
                    # Final attempt failed
                    return {
                        "success": False,
                        "status": "failed",
                        "reason": f"Order execution failed after {self.max_retries} attempts: {str(e)}",
                        "request_id": request_id,
                        "attempts": self.max_retries,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    }

                # Wait before retry (exponential backoff handled by caller)
                continue

    async def _dry_run_validation(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform dry-run validation.

        Args:
            order_params: Order parameters

        Returns:
            Dry-run validation result
        """
        try:
            result = await self.mcp_client.dry_run_order(
                pair=order_params["pair"],
                side=order_params["side"],
                amount=order_params["amount"],
                order_type=order_params["order_type"],
                price=order_params.get("price"),
                request_id=order_params["request_id"],
                agent=order_params["agent"],
            )

            return result

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Dry-run request failed: {str(e)}"],
                "warnings": [],
            }

    async def execute_market_order(
        self,
        pair: str,
        action: str,
        amount: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute market order (convenience method).

        Args:
            pair: Trading pair
            action: "buy" or "sell"
            amount: Order amount
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            meta: Additional metadata

        Returns:
            Order execution result
        """
        return await self.execute_order(
            pair=pair,
            action=action,
            amount=amount,
            entry_price=0.0,  # Not used for market orders
            order_type="market",
            stop_loss=stop_loss,
            take_profit=take_profit,
            meta=meta,
        )

    async def execute_limit_order(
        self,
        pair: str,
        action: str,
        amount: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute limit order (convenience method).

        Args:
            pair: Trading pair
            action: "buy" or "sell"
            amount: Order amount
            price: Limit price
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            meta: Additional metadata

        Returns:
            Order execution result
        """
        return await self.execute_order(
            pair=pair,
            action=action,
            amount=amount,
            entry_price=price,
            order_type="limit",
            stop_loss=stop_loss,
            take_profit=take_profit,
            meta=meta,
        )
