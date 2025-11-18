"""Risk Agent tasks - Position sizing and risk management."""

from typing import Dict, Any
from app.celery_app import celery_app
from app.agents.risk import RiskAgent


# Initialize RiskAgent with default configuration
risk_agent = RiskAgent(config={
    "account_balance": 10000.0,  # Default account balance
    "risk_per_trade": 0.02,  # 2% risk per trade
    "max_position_size": 1.0,
    "max_open_trades": 5,
    "daily_loss_limit_pct": 0.05,  # 5% daily loss limit
    "stop_loss_method": "atr",  # ATR-based stop-loss
    "risk_reward_ratio": 2.0,  # 1:2 risk-reward
    "use_kelly": False,  # Disable Kelly Criterion by default
})


@celery_app.task(name="validate_and_size", bind=True, max_retries=3)
def validate_and_size(self, signal_decision: Dict[str, Any], candle_data: Dict[str, Any]):
    """
    Validate trading signal and calculate position size using RiskAgent.

    Performs comprehensive risk management:
    - ATR-based position sizing
    - Risk limit validation (max position, max trades, daily loss)
    - Stop-loss and take-profit calculation
    - Risk-reward ratio optimization

    Args:
        signal_decision: Signal decision from SignalAgent
        candle_data: Market data with OHLC information

    Returns:
        Risk decision with position size, stop-loss, take-profit, and approval status
    """
    try:
        # Process with RiskAgent
        decision = risk_agent.process(signal_decision, candle_data)

        # Log the decision
        if decision.get("approved"):
            print(f"[RiskAgent] APPROVED trade for {decision.get('pair')}: "
                  f"{decision['action']} {decision['position_size']} units "
                  f"at {decision['entry_price']} "
                  f"(SL: {decision['stop_loss']}, TP: {decision['take_profit']})")
        else:
            warnings_str = ", ".join(decision.get("warnings", ["Unknown reason"]))
            print(f"[RiskAgent] REJECTED trade for {candle_data.get('pair')}: {warnings_str}")

        return decision

    except Exception as exc:
        # Log error and retry
        print(f"[RiskAgent] Error validating trade: {exc}")

        # Return safe default on final failure
        if self.request.retries >= self.max_retries:
            return {
                "approved": False,
                "action": "hold",
                "position_size": 0.0,
                "stop_loss": None,
                "take_profit": None,
                "risk_score": 1.0,
                "warnings": [f"Failed to validate trade after retries: {str(exc)}"],
                "error": str(exc),
            }

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
