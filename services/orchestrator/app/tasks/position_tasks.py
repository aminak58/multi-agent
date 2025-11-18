"""Position Manager tasks - placeholder for Phase 2 Week 5."""

from typing import Dict, Any
from app.celery_app import celery_app


@celery_app.task(name="execute_order", bind=True)
def execute_order(self, risk_decision: Dict[str, Any], candle_data: Dict[str, Any]):
    """
    Execute order if approved by RiskAgent (PositionManager).

    TODO: Implement in Week 5
    - Order execution via MCP Gateway
    - HMAC signing
    - Dry-run validation

    Args:
        risk_decision: Decision from RiskAgent
        candle_data: Candle data

    Returns:
        Order execution result
    """
    # Placeholder implementation
    if not risk_decision.get("approved"):
        return {
            "status": "skipped",
            "message": "Not approved by RiskAgent",
        }

    return {
        "status": "pending",
        "message": "Position manager not implemented yet",
    }
