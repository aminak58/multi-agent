"""MACD (Moving Average Convergence Divergence) Indicator."""

from typing import Dict, Any
import pandas as pd
import numpy as np


class MACDIndicator:
    """
    MACD indicator for trend following and momentum.

    MACD signals:
    - MACD line crosses above signal line: Bullish
    - MACD line crosses below signal line: Bearish
    - Histogram increasing: Bullish momentum
    - Histogram decreasing: Bearish momentum
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ):
        """
        Initialize MACD indicator.

        Args:
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD on dataframe.

        Args:
            df: DataFrame with 'close' column

        Returns:
            DataFrame with MACD columns added
        """
        df = df.copy()

        # Calculate EMAs
        ema_fast = df["close"].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.slow_period, adjust=False).mean()

        # Calculate MACD line
        df["macd"] = ema_fast - ema_slow

        # Calculate signal line
        df["macd_signal"] = df["macd"].ewm(span=self.signal_period, adjust=False).mean()

        # Calculate histogram
        df["macd_histogram"] = df["macd"] - df["macd_signal"]

        return df

    def generate_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal based on MACD.

        Args:
            df: DataFrame with price data

        Returns:
            Signal dictionary with action, strength, and metadata
        """
        min_periods = self.slow_period + self.signal_period
        if len(df) < min_periods:
            return {
                "action": "hold",
                "strength": 0.0,
                "reason": "Insufficient data for MACD calculation",
                "metadata": {},
            }

        # Calculate MACD
        df = self.calculate(df)

        # Get last values
        macd = df["macd"].iloc[-1]
        macd_signal = df["macd_signal"].iloc[-1]
        histogram = df["macd_histogram"].iloc[-1]

        # Get previous values for crossover detection
        macd_prev = df["macd"].iloc[-2]
        macd_signal_prev = df["macd_signal"].iloc[-2]
        histogram_prev = df["macd_histogram"].iloc[-2]

        # Detect crossovers
        bullish_cross = (macd > macd_signal) and (macd_prev <= macd_signal_prev)
        bearish_cross = (macd < macd_signal) and (macd_prev >= macd_signal_prev)

        # Check histogram momentum
        histogram_increasing = histogram > histogram_prev
        histogram_decreasing = histogram < histogram_prev

        # Check if histogram is changing direction
        histogram_turning_positive = (histogram > 0) and (histogram_prev <= 0)
        histogram_turning_negative = (histogram < 0) and (histogram_prev >= 0)

        # Calculate signal strength based on histogram size
        # Normalize by recent price range
        close_price = df["close"].iloc[-1]
        histogram_pct = abs(histogram) / close_price * 100

        # Normalize strength (0.1% = 0.5 strength, 0.5% = 1.0 strength)
        strength = min(histogram_pct / 0.5, 1.0)

        # Determine action
        action = "hold"
        reason = "MACD neutral"

        if bullish_cross:
            action = "buy"
            reason = "MACD bullish crossover"
            if macd > 0:
                strength = min(strength * 1.3, 1.0)  # Stronger signal above zero
                reason += " (above zero line)"
            else:
                strength = strength * 0.9
                reason += " (below zero line)"
        elif bearish_cross:
            action = "sell"
            reason = "MACD bearish crossover"
            if macd < 0:
                strength = min(strength * 1.3, 1.0)  # Stronger signal below zero
                reason += " (below zero line)"
            else:
                strength = strength * 0.9
                reason += " (above zero line)"
        elif histogram_turning_positive:
            action = "buy"
            reason = "MACD histogram turning positive"
            strength = strength * 0.7  # Moderate signal
        elif histogram_turning_negative:
            action = "sell"
            reason = "MACD histogram turning negative"
            strength = strength * 0.7  # Moderate signal
        elif macd > macd_signal and histogram_increasing:
            action = "hold"
            reason = "MACD bullish with increasing momentum"
            strength = strength * 0.4  # Weak continuation signal
        elif macd < macd_signal and histogram_decreasing:
            action = "hold"
            reason = "MACD bearish with decreasing momentum"
            strength = strength * 0.4  # Weak continuation signal
        else:
            strength = 0.0

        return {
            "action": action,
            "strength": round(strength, 3),
            "reason": reason,
            "metadata": {
                "macd": round(macd, 4),
                "macd_signal": round(macd_signal, 4),
                "histogram": round(histogram, 4),
                "histogram_pct": round(histogram_pct, 4),
                "bullish_cross": bullish_cross,
                "bearish_cross": bearish_cross,
                "histogram_increasing": histogram_increasing,
                "above_zero": macd > 0,
            },
        }
