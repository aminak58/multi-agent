"""Pydantic schemas for Orchestrator."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


# Enums
class DecisionAction(str, Enum):
    """Agent decision actions."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


# Webhook Payloads
class CandleUpdate(BaseModel):
    """Candle update webhook payload."""
    pair: str
    timeframe: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class WebhookResponse(BaseModel):
    """Webhook response."""
    status: str
    message: str
    task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Agent Decisions
class SignalDecision(BaseModel):
    """Signal agent decision."""
    action: DecisionAction
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    indicators: Dict[str, Any]
    llm_used: bool = False


class RiskDecision(BaseModel):
    """Risk agent decision."""
    approved: bool
    position_size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_score: float
    warnings: List[str] = []


class OrderExecution(BaseModel):
    """Order execution result."""
    order_id: str
    status: str
    filled_amount: float
    average_price: Optional[float] = None
    timestamp: datetime


# Task Models
class TaskResult(BaseModel):
    """Generic task result."""
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# State Management
class TradingState(BaseModel):
    """Current trading state."""
    pair: str
    last_candle: CandleUpdate
    last_signal: Optional[SignalDecision] = None
    last_risk: Optional[RiskDecision] = None
    last_order: Optional[OrderExecution] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
