"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, validator


# Enums
class OrderSide(str, Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


# Health
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    services: dict


# Candles
class Candle(BaseModel):
    """OHLCV candle data."""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class CandlesResponse(BaseModel):
    """Response for candles endpoint."""
    pair: str
    timeframe: str
    candles: List[Candle]
    count: int


# Positions
class Position(BaseModel):
    """Open position."""
    pair: str
    side: OrderSide
    amount: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    open_date: datetime


class PositionsResponse(BaseModel):
    """Response for positions endpoint."""
    positions: List[Position]
    total_count: int


# Orders
class OrderRequest(BaseModel):
    """Order creation/dry-run request."""
    request_id: str = Field(..., description="Unique request ID for idempotency")
    agent: str = Field(..., description="Agent identifier")
    pair: str = Field(..., description="Trading pair (e.g., BTC/USDT)")
    side: OrderSide
    amount: float = Field(..., gt=0, description="Order amount")
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = Field(None, description="Limit price (for limit orders)")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    leverage: Optional[int] = Field(None, ge=1, le=125)
    meta: Optional[dict] = Field(None, description="Additional metadata")

    @validator("price")
    def validate_limit_price(cls, v, values):
        """Validate that limit orders have a price."""
        if values.get("order_type") == OrderType.LIMIT and v is None:
            raise ValueError("price is required for limit orders")
        return v


class OrderResponse(BaseModel):
    """Order execution response."""
    order_id: str
    request_id: str
    status: OrderStatus
    pair: str
    side: OrderSide
    amount: float
    filled_amount: float
    price: Optional[float] = None
    average_price: Optional[float] = None
    timestamp: datetime
    message: Optional[str] = None


class DryRunResponse(BaseModel):
    """Dry-run response."""
    valid: bool
    estimated_cost: Optional[float] = None
    estimated_fee: Optional[float] = None
    warnings: List[str] = []
    errors: List[str] = []


# Authentication
class TokenRequest(BaseModel):
    """JWT token request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Error
class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
