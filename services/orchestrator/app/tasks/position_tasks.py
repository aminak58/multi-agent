"""Position Manager tasks - Order execution and position management."""

from typing import Dict, Any
import asyncio
from app.celery_app import celery_app
from app.agents.position import PositionManager


# Initialize PositionManager with default configuration
position_manager = PositionManager(config={
    "enable_dry_run": True,
    "enable_trailing_stop": True,
    "trailing_distance_pct": 0.02,  # 2% trailing distance
    "trailing_activation_pct": 0.01,  # Activate after 1% profit
    "max_retries": 3,
})


@celery_app.task(name="execute_order", bind=True, max_retries=3)
def execute_order(self, risk_decision: Dict[str, Any], candle_data: Dict[str, Any] = None):
    """
    Execute order if approved by RiskAgent (PositionManager).

    This task:
    - Validates the risk decision
    - Performs dry-run validation via MCP Gateway
    - Computes HMAC signature for secure requests
    - Executes the order
    - Sets up partial take-profit levels
    - Configures trailing stop-loss

    Args:
        risk_decision: Decision from RiskAgent with position sizing and levels
        candle_data: Optional candle data for additional context

    Returns:
        Order execution result with position management configuration
    """
    try:
        # Check if trade is approved
        if not risk_decision.get("approved"):
            print(f"[PositionManager] Trade rejected by RiskAgent: {risk_decision.get('warnings', [])}")
            return {
                "success": False,
                "status": "skipped",
                "reason": "Not approved by RiskAgent",
                "risk_decision": risk_decision,
            }

        # Log the order attempt
        pair = risk_decision.get("pair")
        action = risk_decision.get("action")
        position_size = risk_decision.get("position_size")

        print(f"[PositionManager] Executing {action.upper()} order for {pair}: "
              f"{position_size} units, risk score: {risk_decision.get('risk_score', 'N/A')}")

        # Execute order using PositionManager (async operation)
        result = asyncio.run(
            position_manager.process(risk_decision, candle_data)
        )

        # Log the result
        if result["success"]:
            print(f"[PositionManager] Order executed successfully: "
                  f"Order ID {result['order_id']}, "
                  f"filled: {result['filled_amount']}")

            # Log take-profit configuration
            if result.get("take_profit_config"):
                tp_config = result["take_profit_config"]
                if tp_config.get("enabled"):
                    print(f"[PositionManager] Take-profit configured: "
                          f"{tp_config['total_targets']} targets")

            # Log trailing stop configuration
            if result.get("trailing_stop_config"):
                ts_config = result["trailing_stop_config"]
                if ts_config.get("enabled"):
                    print(f"[PositionManager] Trailing stop enabled: "
                          f"{ts_config['trailing_distance']}% distance, "
                          f"activates at {ts_config['activation_price']}")
        else:
            print(f"[PositionManager] Order execution failed: {result.get('reason')}")

        return result

    except Exception as exc:
        # Log error
        print(f"[PositionManager] Error executing order: {exc}")

        # Return safe default on final failure
        if self.request.retries >= self.max_retries:
            return {
                "success": False,
                "status": "failed",
                "reason": f"Failed to execute order after retries: {str(exc)}",
                "error": str(exc),
            }

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
