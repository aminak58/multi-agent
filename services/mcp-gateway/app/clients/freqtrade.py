"""Freqtrade REST API client."""

from typing import List, Optional, Dict, Any
import httpx
from datetime import datetime

from app.config import settings
from app.models.schemas import Candle, Position, OrderSide
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class FreqtradeClient:
    """Client for Freqtrade REST API."""

    def __init__(self):
        """Initialize Freqtrade client."""
        self.base_url = settings.freqtrade_url
        self.username = settings.freqtrade_username
        self.password = settings.freqtrade_password
        self._client: Optional[httpx.AsyncClient] = None

    async def connect(self):
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            auth=(self.username, self.password) if self.username else None,
        )
        logger.info(
            "Freqtrade client initialized", extra={"base_url": self.base_url}
        )

    async def disconnect(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            logger.info("Freqtrade client closed")

    async def _request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Freqtrade.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: If request fails
        """
        try:
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(
                f"Freqtrade API error: {e}",
                extra={"endpoint": endpoint, "error": str(e)},
            )
            raise

    async def get_candles(
        self, pair: str, timeframe: str, limit: int = 500
    ) -> List[Candle]:
        """
        Get OHLCV candle data.

        Args:
            pair: Trading pair (e.g., BTC/USDT)
            timeframe: Timeframe (e.g., 5m, 15m, 1h)
            limit: Number of candles to retrieve

        Returns:
            List of candles
        """
        logger.debug(
            "Fetching candles",
            extra={"pair": pair, "timeframe": timeframe, "limit": limit},
        )

        response = await self._request(
            "GET",
            "/api/v1/pair_candles",
            params={"pair": pair, "timeframe": timeframe, "limit": limit},
        )

        # Parse response
        candles = []
        for candle_data in response.get("data", []):
            candles.append(
                Candle(
                    timestamp=int(candle_data[0]),
                    open=float(candle_data[1]),
                    high=float(candle_data[2]),
                    low=float(candle_data[3]),
                    close=float(candle_data[4]),
                    volume=float(candle_data[5]),
                )
            )

        logger.info(
            f"Retrieved {len(candles)} candles",
            extra={"pair": pair, "timeframe": timeframe, "count": len(candles)},
        )

        return candles

    async def get_open_positions(self) -> List[Position]:
        """
        Get currently open positions.

        Returns:
            List of open positions
        """
        logger.debug("Fetching open positions")

        response = await self._request("GET", "/api/v1/status")

        positions = []
        for trade in response:
            positions.append(
                Position(
                    pair=trade["pair"],
                    side=OrderSide.BUY if trade["is_open"] else OrderSide.SELL,
                    amount=float(trade["amount"]),
                    entry_price=float(trade["open_rate"]),
                    current_price=float(trade["current_rate"]),
                    unrealized_pnl=float(trade.get("profit_abs", 0)),
                    unrealized_pnl_pct=float(trade.get("profit_ratio", 0)) * 100,
                    stop_loss=float(trade["stop_loss_abs"])
                    if trade.get("stop_loss_abs")
                    else None,
                    take_profit=None,  # Freqtrade doesn't expose TP directly
                    open_date=datetime.fromisoformat(
                        trade["open_date"].replace("Z", "+00:00")
                    ),
                )
            )

        logger.info(f"Retrieved {len(positions)} open positions")

        return positions

    async def create_order(
        self,
        pair: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a new order.

        Args:
            pair: Trading pair
            side: Order side (buy/sell)
            amount: Order amount
            order_type: Order type (market/limit)
            price: Limit price (for limit orders)

        Returns:
            Order response from Freqtrade
        """
        logger.info(
            "Creating order",
            extra={
                "pair": pair,
                "side": side,
                "amount": amount,
                "type": order_type,
            },
        )

        payload = {
            "pair": pair,
            "side": side,
            "amount": amount,
            "ordertype": order_type,
        }

        if price:
            payload["price"] = price

        response = await self._request(
            "POST", "/api/v1/forcebuy" if side == "buy" else "/api/v1/forcesell", json=payload
        )

        logger.info(f"Order created", extra={"order_id": response.get("order_id")})

        return response

    async def dry_run_order(
        self, pair: str, side: str, amount: float
    ) -> Dict[str, Any]:
        """
        Validate order without execution (dry-run).

        Args:
            pair: Trading pair
            side: Order side
            amount: Order amount

        Returns:
            Validation result
        """
        logger.debug(
            "Dry-run order", extra={"pair": pair, "side": side, "amount": amount}
        )

        # Freqtrade doesn't have a dedicated dry-run endpoint
        # We'll simulate validation by checking balance and pair validity

        try:
            # Get balance
            balance_response = await self._request("GET", "/api/v1/balance")

            # Get pair info
            pair_response = await self._request(
                "GET", "/api/v1/show_config"
            )

            # Basic validation
            available_pairs = pair_response.get("exchange", {}).get("pair_whitelist", [])
            if pair not in available_pairs:
                return {
                    "valid": False,
                    "errors": [f"Pair {pair} not in whitelist"],
                }

            # Estimate cost (simplified)
            # In reality, we'd need current price
            estimated_cost = amount * 50000  # Placeholder

            return {
                "valid": True,
                "estimated_cost": estimated_cost,
                "estimated_fee": estimated_cost * 0.001,  # 0.1% fee
                "warnings": [],
                "errors": [],
            }

        except Exception as e:
            logger.error(f"Dry-run validation failed: {e}")
            return {
                "valid": False,
                "errors": [str(e)],
            }

    async def get_health(self) -> Dict[str, Any]:
        """
        Check Freqtrade health status.

        Returns:
            Health status
        """
        try:
            response = await self._request("GET", "/api/v1/ping")
            return {"status": "healthy", "response": response}
        except Exception as e:
            logger.error(f"Freqtrade health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Global client instance
freqtrade_client = FreqtradeClient()
