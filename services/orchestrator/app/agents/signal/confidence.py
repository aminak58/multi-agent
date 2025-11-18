"""Confidence scoring system for signal quality assessment."""

from typing import Dict, Any
import pandas as pd


class ConfidenceScorer:
    """
    Calculates confidence score for trading signals.

    Factors considered:
    - Signal strength from indicators
    - Market volatility
    - Volume
    - Indicator agreement
    - Historical success rate (future enhancement)
    """

    def __init__(
        self,
        volatility_weight: float = 0.2,
        volume_weight: float = 0.15,
        agreement_weight: float = 0.35,
        strength_weight: float = 0.3,
    ):
        """
        Initialize confidence scorer.

        Args:
            volatility_weight: Weight for volatility factor (default: 0.2)
            volume_weight: Weight for volume factor (default: 0.15)
            agreement_weight: Weight for indicator agreement (default: 0.35)
            strength_weight: Weight for signal strength (default: 0.3)
        """
        self.volatility_weight = volatility_weight
        self.volume_weight = volume_weight
        self.agreement_weight = agreement_weight
        self.strength_weight = strength_weight

        # Normalize weights
        total = sum([volatility_weight, volume_weight, agreement_weight, strength_weight])
        if total > 0:
            self.volatility_weight /= total
            self.volume_weight /= total
            self.agreement_weight /= total
            self.strength_weight /= total

    def calculate_volatility_factor(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        Calculate volatility factor (lower volatility = higher confidence).

        Args:
            df: DataFrame with price data
            period: Period for volatility calculation (default: 20)

        Returns:
            Volatility factor (0-1)
        """
        if len(df) < period:
            return 0.5  # Neutral if insufficient data

        # Calculate ATR (Average True Range)
        high = df["high"].tail(period)
        low = df["low"].tail(period)
        close = df["close"].tail(period)

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.mean()

        # Normalize by price
        current_price = df["close"].iloc[-1]
        atr_pct = (atr / current_price) * 100

        # Convert to factor (lower volatility = higher confidence)
        # Typical ATR: 1-5% - map to 0-1 scale (inverted)
        volatility_factor = max(0.0, min(1.0, 1.0 - (atr_pct / 5.0)))

        return volatility_factor

    def calculate_volume_factor(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        Calculate volume factor (higher volume = higher confidence).

        Args:
            df: DataFrame with volume data
            period: Period for volume comparison (default: 20)

        Returns:
            Volume factor (0-1)
        """
        if len(df) < period or "volume" not in df.columns:
            return 0.5  # Neutral if insufficient data

        # Get recent volumes
        recent_volume = df["volume"].iloc[-1]
        avg_volume = df["volume"].tail(period).mean()

        if avg_volume == 0:
            return 0.5  # Neutral if no volume data

        # Calculate volume ratio
        volume_ratio = recent_volume / avg_volume

        # Convert to factor (higher volume = higher confidence)
        # Map volume ratio to 0-1 scale
        # 0.5x = 0.3, 1x = 0.5, 2x = 0.8, 3x+ = 1.0
        if volume_ratio < 0.5:
            volume_factor = 0.3
        elif volume_ratio < 1.0:
            volume_factor = 0.3 + (volume_ratio - 0.5) * 0.4
        elif volume_ratio < 2.0:
            volume_factor = 0.5 + (volume_ratio - 1.0) * 0.3
        else:
            volume_factor = min(0.8 + (volume_ratio - 2.0) * 0.2, 1.0)

        return volume_factor

    def calculate_agreement_factor(self, signals: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate indicator agreement factor.

        Args:
            signals: Dictionary of indicator signals

        Returns:
            Agreement factor (0-1)
        """
        if not signals or len(signals) < 2:
            return 0.5  # Neutral if insufficient indicators

        # Count actions
        actions = [signal["action"] for signal in signals.values()]
        action_counts = {"buy": 0, "sell": 0, "hold": 0}

        for action in actions:
            action_counts[action] += 1

        # Calculate agreement percentage
        max_count = max(action_counts.values())
        agreement = max_count / len(actions)

        return agreement

    def calculate_strength_factor(self, base_confidence: float) -> float:
        """
        Normalize base confidence from fusion.

        Args:
            base_confidence: Base confidence from signal fusion

        Returns:
            Normalized strength factor (0-1)
        """
        # Base confidence is already 0-1, just ensure bounds
        return max(0.0, min(1.0, base_confidence))

    def calculate_confidence(
        self,
        base_confidence: float,
        signals: Dict[str, Dict[str, Any]],
        df: pd.DataFrame = None,
    ) -> Dict[str, Any]:
        """
        Calculate final confidence score.

        Args:
            base_confidence: Base confidence from signal fusion
            signals: Dictionary of indicator signals
            df: Optional DataFrame for market context

        Returns:
            Confidence score and breakdown
        """
        # Calculate individual factors
        strength_factor = self.calculate_strength_factor(base_confidence)
        agreement_factor = self.calculate_agreement_factor(signals)

        volatility_factor = 0.5  # Default
        volume_factor = 0.5  # Default

        if df is not None and len(df) > 0:
            volatility_factor = self.calculate_volatility_factor(df)
            volume_factor = self.calculate_volume_factor(df)

        # Calculate weighted confidence
        final_confidence = (
            strength_factor * self.strength_weight
            + agreement_factor * self.agreement_weight
            + volatility_factor * self.volatility_weight
            + volume_factor * self.volume_weight
        )

        # Apply confidence thresholds
        confidence_level = self.get_confidence_level(final_confidence)

        return {
            "confidence": round(final_confidence, 3),
            "confidence_level": confidence_level,
            "factors": {
                "strength": round(strength_factor, 3),
                "agreement": round(agreement_factor, 3),
                "volatility": round(volatility_factor, 3),
                "volume": round(volume_factor, 3),
            },
            "weights": {
                "strength": self.strength_weight,
                "agreement": self.agreement_weight,
                "volatility": self.volatility_weight,
                "volume": self.volume_weight,
            },
        }

    def get_confidence_level(self, confidence: float) -> str:
        """
        Convert confidence score to qualitative level.

        Args:
            confidence: Confidence score (0-1)

        Returns:
            Confidence level string
        """
        if confidence >= 0.8:
            return "very_high"
        elif confidence >= 0.6:
            return "high"
        elif confidence >= 0.4:
            return "medium"
        elif confidence >= 0.2:
            return "low"
        else:
            return "very_low"

    def should_trade(self, confidence: float, min_confidence: float = 0.5) -> bool:
        """
        Determine if confidence is sufficient for trading.

        Args:
            confidence: Confidence score
            min_confidence: Minimum required confidence (default: 0.5)

        Returns:
            True if should trade, False otherwise
        """
        return confidence >= min_confidence
