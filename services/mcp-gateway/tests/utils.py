"""Test utilities and helpers."""

import random
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import uuid4

from app.models.schemas import Candle, Position, OrderSide


def generate_request_id() -> str:
    """Generate a random request ID."""
    return str(uuid4())


def generate_random_string(length: int = 10) -> str:
    """Generate random alphanumeric string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_candles(
    count: int = 100,
    start_price: float = 50000.0,
    volatility: float = 0.02,
    start_timestamp: int = None,
) -> List[Candle]:
    """
    Generate realistic candle data for testing.

    Args:
        count: Number of candles to generate
        start_price: Starting price
        volatility: Price volatility (0.02 = 2%)
        start_timestamp: Starting timestamp (default: 30 days ago)

    Returns:
        List of Candle objects
    """
    if start_timestamp is None:
        start_timestamp = int(
            (datetime.utcnow() - timedelta(days=30)).timestamp() * 1000
        )

    candles = []
    current_price = start_price
    timestamp = start_timestamp

    for _ in range(count):
        # Generate OHLCV with realistic relationships
        price_change = random.uniform(-volatility, volatility)
        close = current_price * (1 + price_change)

        high = max(current_price, close) * (1 + random.uniform(0, volatility / 2))
        low = min(current_price, close) * (1 - random.uniform(0, volatility / 2))
        volume = random.uniform(50, 200)

        candle = Candle(
            timestamp=timestamp,
            open=current_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )

        candles.append(candle)
        current_price = close
        timestamp += 900000  # 15 minutes in milliseconds

    return candles


def generate_position(
    pair: str = "BTC/USDT",
    side: OrderSide = OrderSide.BUY,
    entry_price: float = 50000.0,
    current_price: float = 51000.0,
    amount: float = 0.01,
) -> Position:
    """
    Generate a position for testing.

    Args:
        pair: Trading pair
        side: Order side
        entry_price: Entry price
        current_price: Current price
        amount: Position amount

    Returns:
        Position object
    """
    unrealized_pnl = (current_price - entry_price) * amount
    unrealized_pnl_pct = (current_price - entry_price) / entry_price * 100

    return Position(
        pair=pair,
        side=side,
        amount=amount,
        entry_price=entry_price,
        current_price=current_price,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=unrealized_pnl_pct,
        stop_loss=entry_price * 0.98,
        take_profit=entry_price * 1.05,
        open_date=datetime.utcnow() - timedelta(hours=2),
    )


def generate_order_request(
    pair: str = "BTC/USDT",
    side: str = "buy",
    amount: float = 0.001,
    order_type: str = "market",
) -> Dict[str, Any]:
    """
    Generate an order request payload.

    Args:
        pair: Trading pair
        side: Order side (buy/sell)
        amount: Order amount
        order_type: Order type (market/limit)

    Returns:
        Order request dictionary
    """
    return {
        "request_id": generate_request_id(),
        "agent": f"test-agent-{generate_random_string(5)}",
        "pair": pair,
        "side": side,
        "amount": amount,
        "order_type": order_type,
    }


def assert_candle_valid(candle: Dict[str, Any]):
    """
    Assert that a candle has valid structure and relationships.

    Args:
        candle: Candle dictionary to validate
    """
    required_fields = ["timestamp", "open", "high", "low", "close", "volume"]

    for field in required_fields:
        assert field in candle, f"Missing field: {field}"

    # High should be >= Open, Close, Low
    assert candle["high"] >= candle["open"], "High < Open"
    assert candle["high"] >= candle["close"], "High < Close"
    assert candle["high"] >= candle["low"], "High < Low"

    # Low should be <= Open, Close, High
    assert candle["low"] <= candle["open"], "Low > Open"
    assert candle["low"] <= candle["close"], "Low > Close"
    assert candle["low"] <= candle["high"], "Low > High"

    # Volume should be positive
    assert candle["volume"] > 0, "Volume <= 0"


def assert_position_valid(position: Dict[str, Any]):
    """
    Assert that a position has valid structure.

    Args:
        position: Position dictionary to validate
    """
    required_fields = [
        "pair",
        "side",
        "amount",
        "entry_price",
        "current_price",
        "unrealized_pnl",
        "unrealized_pnl_pct",
    ]

    for field in required_fields:
        assert field in position, f"Missing field: {field}"

    # Amount should be positive
    assert position["amount"] > 0, "Amount <= 0"

    # Prices should be positive
    assert position["entry_price"] > 0, "Entry price <= 0"
    assert position["current_price"] > 0, "Current price <= 0"

    # Side should be valid
    assert position["side"] in ["buy", "sell"], f"Invalid side: {position['side']}"


def assert_order_response_valid(order: Dict[str, Any]):
    """
    Assert that an order response has valid structure.

    Args:
        order: Order response dictionary to validate
    """
    required_fields = [
        "order_id",
        "request_id",
        "status",
        "pair",
        "side",
        "amount",
        "timestamp",
    ]

    for field in required_fields:
        assert field in order, f"Missing field: {field}"

    # Status should be valid
    valid_statuses = ["pending", "submitted", "filled", "cancelled", "rejected"]
    assert order["status"] in valid_statuses, f"Invalid status: {order['status']}"

    # Side should be valid
    assert order["side"] in ["buy", "sell"], f"Invalid side: {order['side']}"

    # Amount should be positive
    assert order["amount"] > 0, "Amount <= 0"


class MockFreqtradeResponse:
    """Mock Freqtrade API responses."""

    @staticmethod
    def candles(count: int = 100) -> Dict[str, Any]:
        """Mock candles response."""
        candles = generate_candles(count)
        return {
            "data": [
                [
                    c.timestamp,
                    c.open,
                    c.high,
                    c.low,
                    c.close,
                    c.volume,
                ]
                for c in candles
            ]
        }

    @staticmethod
    def positions(count: int = 2) -> List[Dict[str, Any]]:
        """Mock positions response."""
        positions = []
        pairs = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

        for i in range(count):
            positions.append({
                "pair": pairs[i % len(pairs)],
                "is_open": True,
                "amount": random.uniform(0.001, 0.1),
                "open_rate": random.uniform(40000, 60000),
                "current_rate": random.uniform(40000, 60000),
                "profit_abs": random.uniform(-100, 100),
                "profit_ratio": random.uniform(-0.05, 0.05),
                "stop_loss_abs": random.uniform(39000, 41000),
                "open_date": datetime.utcnow().isoformat() + "Z",
            })

        return positions

    @staticmethod
    def order_success(order_id: str = None) -> Dict[str, Any]:
        """Mock successful order response."""
        return {
            "order_id": order_id or f"order-{generate_random_string(8)}",
            "status": "submitted",
        }

    @staticmethod
    def order_error(error_message: str = "Order failed") -> Dict[str, Any]:
        """Mock error order response."""
        return {"error": error_message}


class Timer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start = None
        self.end = None
        self.duration = None

    def __enter__(self):
        import time

        self.start = time.time()
        return self

    def __exit__(self, *args):
        import time

        self.end = time.time()
        self.duration = (self.end - self.start) * 1000  # Convert to ms

    @property
    def ms(self) -> float:
        """Get duration in milliseconds."""
        return self.duration

    @property
    def seconds(self) -> float:
        """Get duration in seconds."""
        return self.duration / 1000
