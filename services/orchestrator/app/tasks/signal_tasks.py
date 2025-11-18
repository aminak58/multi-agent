"""Signal Agent tasks - Technical indicator based signal generation."""

from typing import Dict, Any
from app.celery_app import celery_app
from app.agents.signal import SignalAgent


# Initialize SignalAgent with default configuration
signal_agent = SignalAgent(config={
    "fusion_method": "weighted_average",
    "min_confidence": 0.5,
    "indicator_weights": {
        "ema": 0.25,
        "rsi": 0.25,
        "macd": 0.25,
        "support_resistance": 0.25,
    },
})


@celery_app.task(name="generate_signal", bind=True, max_retries=3)
def generate_signal(self, candle_data: Dict[str, Any]):
    """
    Generate trading signal using SignalAgent.

    Analyzes candle data using multiple technical indicators:
    - EMA Crossover for trend identification
    - RSI for overbought/oversold conditions
    - MACD for momentum and trend confirmation
    - Support/Resistance for key price levels

    Args:
        candle_data: Candle data with OHLCV information

    Returns:
        Signal decision with action, confidence, and reasoning
    """
    try:
        # Generate signal using SignalAgent
        decision = signal_agent.process(candle_data)

        # Log the decision (in production, this would go to logging system)
        if decision.get("should_trade"):
            print(f"[SignalAgent] {decision['action'].upper()} signal generated "
                  f"for {decision.get('pair')} with confidence {decision['confidence']:.2f}")
        else:
            print(f"[SignalAgent] Confidence too low ({decision['confidence']:.2f}) "
                  f"- holding position for {decision.get('pair')}")

        return decision

    except Exception as exc:
        # Log error and retry
        print(f"[SignalAgent] Error generating signal: {exc}")

        # Return safe default on final failure
        if self.request.retries >= self.max_retries:
            return {
                "action": "hold",
                "confidence": 0.0,
                "reasoning": f"Failed to generate signal after retries: {str(exc)}",
                "indicators": {},
                "llm_used": False,
                "error": str(exc),
            }

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
