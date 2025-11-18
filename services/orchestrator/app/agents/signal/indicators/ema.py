"""EMA (Exponential Moving Average) Crossover Indicator."""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class EMAIndicator:
    """
    EMA Crossover indicator for trend identification.

    Generates buy/sell signals based on EMA crossovers.
    """

    def __init__(
        self,
        fast_period: int = 9,
        slow_period: int = 21,
        signal_period: int = 50,
    ):
        """
        Initialize EMA indicator.

        Args:
            fast_period: Fast EMA period (default: 9)
            slow_period: Slow EMA period (default: 21)
            signal_period: Signal line EMA period (default: 50)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate EMAs on dataframe.

        Args:
            df: DataFrame with 'close' column

        Returns:
            DataFrame with EMA columns added
        """
        df = df.copy()

        # Calculate EMAs
        df["ema_fast"] = df["close"].ewm(span=self.fast_period, adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=self.slow_period, adjust=False).mean()
        df["ema_signal"] = df["close"].ewm(span=self.signal_period, adjust=False).mean()

        return df

    def generate_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal based on EMA crossover.

        Args:
            df: DataFrame with price data

        Returns:
            Signal dictionary with action, strength, and metadata
        """
        if len(df) < max(self.fast_period, self.slow_period, self.signal_period):
            return {
                "action": "hold",
                "strength": 0.0,
                "reason": "Insufficient data for EMA calculation",
                "metadata": {},
            }

        # Calculate EMAs
        df = self.calculate(df)

        # Get last values
        fast_ema = df["ema_fast"].iloc[-1]
        slow_ema = df["ema_slow"].iloc[-1]
        signal_ema = df["ema_signal"].iloc[-1]
        close_price = df["close"].iloc[-1]

        # Get previous values for crossover detection
        fast_ema_prev = df["ema_fast"].iloc[-2]
        slow_ema_prev = df["ema_slow"].iloc[-2]

        # Detect crossover
        bullish_cross = (fast_ema > slow_ema) and (fast_ema_prev <= slow_ema_prev)
        bearish_cross = (fast_ema < slow_ema) and (fast_ema_prev >= slow_ema_prev)

        # Calculate signal strength (0-1)
        ema_diff = abs(fast_ema - slow_ema)
        ema_diff_pct = (ema_diff / close_price) * 100

        # Normalize strength (0.1% diff = 0.5 strength, 1% diff = 1.0 strength)
        strength = min(ema_diff_pct / 1.0, 1.0)

        # Check if price is above/below signal line for trend confirmation
        above_signal = close_price > signal_ema
        below_signal = close_price < signal_ema

        # Determine action
        action = "hold"
        reason = "No clear signal"

        if bullish_cross and above_signal:
            action = "buy"
            reason = "Bullish EMA crossover with price above signal line"
            strength = min(strength * 1.2, 1.0)  # Boost strength for confirmed signal
        elif bullish_cross:
            action = "buy"
            reason = "Bullish EMA crossover (weak - price below signal line)"
            strength = strength * 0.7  # Reduce strength for unconfirmed signal
        elif bearish_cross and below_signal:
            action = "sell"
            reason = "Bearish EMA crossover with price below signal line"
            strength = min(strength * 1.2, 1.0)
        elif bearish_cross:
            action = "sell"
            reason = "Bearish EMA crossover (weak - price above signal line)"
            strength = strength * 0.7
        elif fast_ema > slow_ema and above_signal:
            action = "hold"
            reason = "Bullish trend continues"
            strength = strength * 0.3  # Lower strength for continuation
        elif fast_ema < slow_ema and below_signal:
            action = "hold"
            reason = "Bearish trend continues"
            strength = strength * 0.3

        return {
            "action": action,
            "strength": round(strength, 3),
            "reason": reason,
            "metadata": {
                "fast_ema": round(fast_ema, 2),
                "slow_ema": round(slow_ema, 2),
                "signal_ema": round(signal_ema, 2),
                "ema_diff_pct": round(ema_diff_pct, 3),
                "bullish_cross": bullish_cross,
                "bearish_cross": bearish_cross,
                "above_signal": above_signal,
            },
        }
