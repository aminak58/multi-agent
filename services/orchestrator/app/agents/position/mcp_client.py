"""MCP Gateway client for order execution."""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional
import httpx
from datetime import datetime

from app.config import settings


class MCPGatewayClient:
    """Client for interacting with MCP Gateway API."""

    def __init__(self, base_url: Optional[str] = None, jwt_secret: Optional[str] = None):
        """
        Initialize MCP Gateway client.

        Args:
            base_url: MCP Gateway base URL (default: from settings)
            jwt_secret: JWT secret for HMAC signing (default: from settings)
        """
        self.base_url = base_url or settings.mcp_gateway_url
        self.jwt_secret = jwt_secret or settings.mcp_jwt_secret
        self.timeout = 30.0  # seconds

    def compute_hmac_signature(self, payload: Dict[str, Any]) -> str:
        """
        Compute HMAC-SHA256 signature for request payload.

        Args:
            payload: Request payload dictionary

        Returns:
            Hex-encoded HMAC signature
        """
        # Convert payload to JSON bytes
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')

        # Compute HMAC-SHA256
        signature = hmac.new(
            self.jwt_secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        return signature

    async def dry_run_order(
        self,
        pair: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        request_id: Optional[str] = None,
        agent: str = "PositionManager",
    ) -> Dict[str, Any]:
        """
        Validate order via dry-run without execution.

        Args:
            pair: Trading pair (e.g., "BTC/USDT")
            side: Order side ("buy" or "sell")
            amount: Order amount
            order_type: Order type ("market" or "limit")
            price: Limit price (required for limit orders)
            request_id: Unique request ID (generated if not provided)
            agent: Agent identifier

        Returns:
            Dry-run validation result

        Raises:
            httpx.HTTPError: If request fails
        """
        if not request_id:
            request_id = f"dryrun_{datetime.utcnow().timestamp()}"

        payload = {
            "request_id": request_id,
            "agent": agent,
            "pair": pair,
            "side": side,
            "amount": amount,
            "order_type": order_type,
        }

        if price is not None:
            payload["price"] = price

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/orders/dry-run",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def create_order(
        self,
        pair: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        leverage: Optional[int] = None,
        request_id: Optional[str] = None,
        agent: str = "PositionManager",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create and execute order via MCP Gateway.

        This endpoint requires HMAC signature for security.

        Args:
            pair: Trading pair (e.g., "BTC/USDT")
            side: Order side ("buy" or "sell")
            amount: Order amount
            order_type: Order type ("market" or "limit")
            price: Limit price (required for limit orders)
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            leverage: Leverage multiplier (1-125)
            request_id: Unique request ID (generated if not provided)
            agent: Agent identifier
            meta: Additional metadata

        Returns:
            Order execution result

        Raises:
            httpx.HTTPError: If request fails
        """
        if not request_id:
            request_id = f"order_{datetime.utcnow().timestamp()}"

        payload = {
            "request_id": request_id,
            "agent": agent,
            "pair": pair,
            "side": side,
            "amount": amount,
            "order_type": order_type,
        }

        # Add optional fields
        if price is not None:
            payload["price"] = price
        if stop_loss is not None:
            payload["stop_loss"] = stop_loss
        if take_profit is not None:
            payload["take_profit"] = take_profit
        if leverage is not None:
            payload["leverage"] = leverage
        if meta is not None:
            payload["meta"] = meta

        # Compute HMAC signature
        signature = self.compute_hmac_signature(payload)

        # Make request with signature
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/orders",
                json=payload,
                headers={"X-Signature": signature},
            )
            response.raise_for_status()
            return response.json()

    async def get_positions(self) -> Dict[str, Any]:
        """
        Get current open positions.

        Returns:
            List of open positions
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/positions")
            response.raise_for_status()
            return response.json()

    async def update_position(
        self,
        pair: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Update existing position's stop-loss or take-profit.

        Args:
            pair: Trading pair
            stop_loss: New stop-loss price
            take_profit: New take-profit price

        Returns:
            Update result
        """
        payload = {"pair": pair}

        if stop_loss is not None:
            payload["stop_loss"] = stop_loss
        if take_profit is not None:
            payload["take_profit"] = take_profit

        # Compute HMAC signature
        signature = self.compute_hmac_signature(payload)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.patch(
                f"{self.base_url}/positions/{pair}",
                json=payload,
                headers={"X-Signature": signature},
            )
            response.raise_for_status()
            return response.json()
