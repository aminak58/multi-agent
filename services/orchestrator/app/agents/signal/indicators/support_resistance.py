"""Support and Resistance Level Indicator."""

from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np


class SupportResistanceIndicator:
    """
    Support and Resistance level detector.

    Identifies key price levels where price has historically bounced or broken through.
    """

    def __init__(
        self,
        lookback_period: int = 50,
        num_levels: int = 3,
        proximity_threshold: float = 0.015,  # 1.5%
        strength_threshold: int = 2,  # Minimum touches required
    ):
        """
        Initialize S/R indicator.

        Args:
            lookback_period: Number of candles to look back (default: 50)
            num_levels: Number of S/R levels to identify (default: 3)
            proximity_threshold: Price proximity threshold as percentage (default: 0.015 = 1.5%)
            strength_threshold: Minimum number of touches for valid level (default: 2)
        """
        self.lookback_period = lookback_period
        self.num_levels = num_levels
        self.proximity_threshold = proximity_threshold
        self.strength_threshold = strength_threshold

    def find_pivot_points(self, df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """
        Find pivot highs and lows.

        Args:
            df: DataFrame with OHLC data
            window: Window size for pivot detection

        Returns:
            DataFrame with pivot columns added
        """
        df = df.copy()

        # Find pivot highs (local maxima)
        df["pivot_high"] = (
            df["high"]
            .rolling(window=window * 2 + 1, center=True)
            .apply(lambda x: x[window] == x.max(), raw=True)
        )

        # Find pivot lows (local minima)
        df["pivot_low"] = (
            df["low"]
            .rolling(window=window * 2 + 1, center=True)
            .apply(lambda x: x[window] == x.min(), raw=True)
        )

        return df

    def cluster_levels(self, prices: List[float], current_price: float) -> List[Tuple[float, int]]:
        """
        Cluster nearby price levels.

        Args:
            prices: List of price levels
            current_price: Current market price

        Returns:
            List of (price, strength) tuples
        """
        if not prices:
            return []

        # Sort prices
        prices = sorted(prices)

        # Cluster nearby levels
        clusters = []
        current_cluster = [prices[0]]

        for price in prices[1:]:
            # Check if price is within proximity threshold of cluster
            cluster_avg = np.mean(current_cluster)
            if abs(price - cluster_avg) / cluster_avg < self.proximity_threshold:
                current_cluster.append(price)
            else:
                # Start new cluster
                clusters.append(current_cluster)
                current_cluster = [price]

        # Add last cluster
        clusters.append(current_cluster)

        # Calculate cluster centers and strengths
        levels = []
        for cluster in clusters:
            center = np.mean(cluster)
            strength = len(cluster)
            if strength >= self.strength_threshold:
                levels.append((center, strength))

        # Sort by strength and take top N
        levels = sorted(levels, key=lambda x: x[1], reverse=True)[: self.num_levels]

        # Sort by distance from current price
        levels = sorted(levels, key=lambda x: abs(x[0] - current_price))

        return levels

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate support and resistance levels.

        Args:
            df: DataFrame with OHLC data

        Returns:
            Dictionary with S/R levels
        """
        if len(df) < self.lookback_period:
            return {"support_levels": [], "resistance_levels": []}

        # Get recent data
        recent_df = df.tail(self.lookback_period).copy()

        # Find pivot points
        recent_df = self.find_pivot_points(recent_df)

        # Extract pivot highs and lows
        pivot_highs = recent_df[recent_df["pivot_high"] == 1]["high"].tolist()
        pivot_lows = recent_df[recent_df["pivot_low"] == 1]["low"].tolist()

        # Get current price
        current_price = df["close"].iloc[-1]

        # Cluster levels
        resistance_levels = self.cluster_levels(
            [p for p in pivot_highs if p > current_price], current_price
        )
        support_levels = self.cluster_levels(
            [p for p in pivot_lows if p < current_price], current_price
        )

        return {
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
        }

    def generate_signal(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate trading signal based on S/R levels.

        Args:
            df: DataFrame with OHLC data

        Returns:
            Signal dictionary with action, strength, and metadata
        """
        if len(df) < self.lookback_period:
            return {
                "action": "hold",
                "strength": 0.0,
                "reason": "Insufficient data for S/R calculation",
                "metadata": {},
            }

        # Calculate S/R levels
        levels = self.calculate(df)
        support_levels = levels["support_levels"]
        resistance_levels = levels["resistance_levels"]

        # Get current price and recent price action
        current_price = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2]
        current_high = df["high"].iloc[-1]
        current_low = df["low"].iloc[-1]

        action = "hold"
        reason = "No clear S/R signal"
        strength = 0.0

        # Check proximity to support levels
        for support_price, support_strength in support_levels:
            distance_pct = abs(current_price - support_price) / support_price

            if distance_pct < self.proximity_threshold / 2:  # Very close to support
                if current_low <= support_price and current_price > support_price:
                    # Bounced off support
                    action = "buy"
                    reason = f"Bouncing off support at {support_price:.2f}"
                    strength = min(support_strength / 5.0, 1.0)  # Strength based on level strength
                    break
                elif prev_close > support_price and current_price < support_price:
                    # Broke below support
                    action = "sell"
                    reason = f"Broke below support at {support_price:.2f}"
                    strength = min(support_strength / 5.0 * 0.8, 1.0)
                    break

        # Check proximity to resistance levels
        for resistance_price, resistance_strength in resistance_levels:
            distance_pct = abs(current_price - resistance_price) / resistance_price

            if distance_pct < self.proximity_threshold / 2:  # Very close to resistance
                if current_high >= resistance_price and current_price < resistance_price:
                    # Rejected at resistance
                    action = "sell"
                    reason = f"Rejected at resistance at {resistance_price:.2f}"
                    strength = min(resistance_strength / 5.0, 1.0)
                    break
                elif prev_close < resistance_price and current_price > resistance_price:
                    # Broke above resistance
                    action = "buy"
                    reason = f"Broke above resistance at {resistance_price:.2f}"
                    strength = min(resistance_strength / 5.0 * 0.8, 1.0)
                    break

        # Format levels for metadata
        support_list = [{"price": round(p, 2), "strength": s} for p, s in support_levels]
        resistance_list = [{"price": round(p, 2), "strength": s} for p, s in resistance_levels]

        return {
            "action": action,
            "strength": round(strength, 3),
            "reason": reason,
            "metadata": {
                "current_price": round(current_price, 2),
                "support_levels": support_list,
                "resistance_levels": resistance_list,
                "nearest_support": support_list[0] if support_list else None,
                "nearest_resistance": resistance_list[0] if resistance_list else None,
            },
        }
