"""RSI (Relative Strength Index) Indicator."""

from typing import Dict, Any
import pandas as pd
import numpy as np


class RSIIndicator:
    """
    RSI indicator for overbought/oversold conditions.

    RSI values:
    - Above 70: Overbought (potential sell signal)
    - Below 30: Oversold (potential buy signal)
    - 50: Neutral
    """

    def __init__(
        self,
        period: int = 14,
        overbought: float = 70.0,
        oversold: float = 30.0,
        extreme_overbought: float = 80.0,
        extreme_oversold: float = 20.0,
    ):
        """
        Initialize RSI indicator.

        Args:
            period: RSI calculation period (default: 14)
            overbought: Overbought threshold (default: 70)
            oversold: Oversold threshold (default: 30)
            extreme_overbought: Extreme overbought threshold (default: 80)
            extreme_oversold: Extreme oversold threshold (default: 20)
        """
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.extreme_overbought = extreme_overbought
        self.extreme_oversold = extreme_oversold

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI on dataframe.

        Args:
            df: DataFrame with 'close' column

        Returns:
            DataFrame with RSI column added
        """
        df = df.copy()

        # Calculate price changes
        delta = df["close"].diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate average gain and loss
        avg_gain = gain.ewm(span=self.period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.period, adjust=False).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

        return df

    def generate_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal based on RSI.

        Args:
            df: DataFrame with price data

        Returns:
            Signal dictionary with action, strength, and metadata
        """
        if len(df) < self.period + 1:
            return {
                "action": "hold",
                "strength": 0.0,
                "reason": "Insufficient data for RSI calculation",
                "metadata": {},
            }

        # Calculate RSI
        df = self.calculate(df)

        # Get last values
        rsi = df["rsi"].iloc[-1]
        rsi_prev = df["rsi"].iloc[-2]

        # Check for divergence (optional, needs price trend comparison)
        # For now, we'll focus on overbought/oversold conditions

        # Calculate signal strength based on how extreme the RSI is
        action = "hold"
        reason = "RSI in neutral zone"
        strength = 0.0

        if rsi < self.extreme_oversold:
            # Extremely oversold - strong buy signal
            action = "buy"
            reason = f"RSI extremely oversold ({rsi:.1f})"
            strength = min((self.oversold - rsi) / self.oversold, 1.0)
        elif rsi < self.oversold:
            # Oversold - buy signal
            action = "buy"
            reason = f"RSI oversold ({rsi:.1f})"
            strength = (self.oversold - rsi) / (self.oversold - self.extreme_oversold)
        elif rsi > self.extreme_overbought:
            # Extremely overbought - strong sell signal
            action = "sell"
            reason = f"RSI extremely overbought ({rsi:.1f})"
            strength = min((rsi - self.overbought) / (100 - self.overbought), 1.0)
        elif rsi > self.overbought:
            # Overbought - sell signal
            action = "sell"
            reason = f"RSI overbought ({rsi:.1f})"
            strength = (rsi - self.overbought) / (self.extreme_overbought - self.overbought)
        else:
            # Neutral zone - check for momentum
            if 45 <= rsi <= 55:
                strength = 0.0
                reason = f"RSI neutral ({rsi:.1f})"
            elif rsi > 55:
                action = "hold"
                strength = (rsi - 50) / 20 * 0.3  # Weak bullish
                reason = f"RSI slightly bullish ({rsi:.1f})"
            else:
                action = "hold"
                strength = (50 - rsi) / 20 * 0.3  # Weak bearish
                reason = f"RSI slightly bearish ({rsi:.1f})"

        # Check for RSI crossing thresholds (additional signal)
        crossing_up_oversold = (rsi > self.oversold) and (rsi_prev <= self.oversold)
        crossing_down_overbought = (rsi < self.overbought) and (rsi_prev >= self.overbought)

        if crossing_up_oversold:
            action = "buy"
            reason = f"RSI crossing up from oversold ({rsi:.1f})"
            strength = min(strength * 1.3, 1.0)  # Boost signal
        elif crossing_down_overbought:
            action = "sell"
            reason = f"RSI crossing down from overbought ({rsi:.1f})"
            strength = min(strength * 1.3, 1.0)  # Boost signal

        return {
            "action": action,
            "strength": round(strength, 3),
            "reason": reason,
            "metadata": {
                "rsi": round(rsi, 2),
                "rsi_prev": round(rsi_prev, 2),
                "overbought_threshold": self.overbought,
                "oversold_threshold": self.oversold,
                "crossing_up_oversold": crossing_up_oversold,
                "crossing_down_overbought": crossing_down_overbought,
            },
        }
