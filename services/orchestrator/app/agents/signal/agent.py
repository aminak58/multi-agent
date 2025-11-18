"""SignalAgent - Main signal generation agent."""

from typing import Dict, Any
import pandas as pd
from datetime import datetime

from app.agents.base import BaseAgent
from app.agents.signal.indicators import (
    EMAIndicator,
    RSIIndicator,
    MACDIndicator,
    SupportResistanceIndicator,
)
from app.agents.signal.fusion import SignalFusion, FusionMethod
from app.agents.signal.confidence import ConfidenceScorer


class SignalAgent(BaseAgent):
    """
    Signal Agent for generating trading signals.

    Combines multiple technical indicators and uses fusion logic
    to generate high-quality trading signals.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize SignalAgent.

        Args:
            config: Configuration dictionary
                - fusion_method: Fusion method to use (default: weighted_average)
                - min_confidence: Minimum confidence for trading (default: 0.5)
                - indicator_weights: Custom indicator weights
                - enable_ema: Enable EMA indicator (default: True)
                - enable_rsi: Enable RSI indicator (default: True)
                - enable_macd: Enable MACD indicator (default: True)
                - enable_sr: Enable S/R indicator (default: True)
        """
        super().__init__(config)

        # Get fusion method from config
        fusion_method_str = self.get_config_value("fusion_method", "weighted_average")
        fusion_method = FusionMethod(fusion_method_str)

        # Get indicator weights
        indicator_weights = self.get_config_value("indicator_weights", {})

        # Initialize fusion and confidence scoring
        self.fusion = SignalFusion(
            method=fusion_method,
            weights=indicator_weights,
        )
        self.confidence_scorer = ConfidenceScorer()

        # Minimum confidence for trading
        self.min_confidence = self.get_config_value("min_confidence", 0.5)

        # Initialize indicators based on config
        self.indicators = {}

        if self.get_config_value("enable_ema", True):
            self.indicators["ema"] = EMAIndicator()

        if self.get_config_value("enable_rsi", True):
            self.indicators["rsi"] = RSIIndicator()

        if self.get_config_value("enable_macd", True):
            self.indicators["macd"] = MACDIndicator()

        if self.get_config_value("enable_sr", True):
            self.indicators["support_resistance"] = SupportResistanceIndicator()

    def prepare_dataframe(self, candle_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepare DataFrame from candle data.

        Args:
            candle_data: Candle data dictionary

        Returns:
            DataFrame with OHLCV data
        """
        # Check if we have historical data or just single candle
        if "candles" in candle_data:
            # Historical data provided
            df = pd.DataFrame(candle_data["candles"])
        else:
            # Single candle - need to fetch history (placeholder)
            # In production, this would fetch from MCP Gateway or Redis cache
            df = pd.DataFrame([{
                "timestamp": candle_data.get("timestamp"),
                "open": candle_data.get("open"),
                "high": candle_data.get("high"),
                "low": candle_data.get("low"),
                "close": candle_data.get("close"),
                "volume": candle_data.get("volume", 0),
            }])

        # Ensure required columns
        required_columns = ["open", "high", "low", "close"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame missing required columns: {required_columns}")

        return df

    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Generate signals from all indicators.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary of indicator signals
        """
        signals = {}

        for name, indicator in self.indicators.items():
            try:
                signal = indicator.generate_signal(df)
                signals[name] = signal
            except Exception as e:
                # Log error but continue with other indicators
                signals[name] = {
                    "action": "hold",
                    "strength": 0.0,
                    "reason": f"Error: {str(e)}",
                    "metadata": {"error": str(e)},
                }

        return signals

    def process(self, candle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process candle data and generate trading signal.

        Args:
            candle_data: Candle update data with OHLCV info

        Returns:
            Signal decision with action, confidence, and reasoning
        """
        # Validate input
        required_fields = ["pair"]
        if not self.validate_input(candle_data, required_fields):
            return {
                "action": "hold",
                "confidence": 0.0,
                "confidence_level": "very_low",
                "reasoning": "Missing required field: pair",
                "indicators": {},
                "fusion_method": self.fusion.method.value,
                "confidence_factors": {
                    "strength": 0.0,
                    "agreement": 0.0,
                    "volatility": 0.5,
                    "volume": 0.5,
                },
                "should_trade": False,
                "llm_used": False,
                "timestamp": datetime.utcnow().isoformat(),
                "pair": candle_data.get("pair"),
                "timeframe": candle_data.get("timeframe"),
            }

        # Check if we have candles or single candle data
        has_candles = "candles" in candle_data
        has_ohlc = all(k in candle_data for k in ["open", "high", "low", "close"])

        if not has_candles and not has_ohlc:
            return {
                "action": "hold",
                "confidence": 0.0,
                "confidence_level": "very_low",
                "reasoning": "Invalid input data",
                "indicators": {},
                "fusion_method": self.fusion.method.value,
                "confidence_factors": {
                    "strength": 0.0,
                    "agreement": 0.0,
                    "volatility": 0.5,
                    "volume": 0.5,
                },
                "should_trade": False,
                "llm_used": False,
                "timestamp": datetime.utcnow().isoformat(),
                "pair": candle_data.get("pair"),
                "timeframe": candle_data.get("timeframe"),
            }

        try:
            # Prepare DataFrame
            df = self.prepare_dataframe(candle_data)

            # Generate signals from all indicators
            signals = self.generate_signals(df)

            # Fuse signals
            fused_decision = self.fusion.fuse(signals)

            # Calculate confidence
            confidence_result = self.confidence_scorer.calculate_confidence(
                base_confidence=fused_decision["confidence"],
                signals=signals,
                df=df,
            )

            # Build final decision
            final_decision = {
                "action": fused_decision["action"],
                "confidence": confidence_result["confidence"],
                "confidence_level": confidence_result["confidence_level"],
                "reasoning": fused_decision["reasoning"],
                "indicators": fused_decision["indicators"],
                "fusion_method": fused_decision["method"],
                "confidence_factors": confidence_result["factors"],
                "should_trade": confidence_result["confidence"] >= self.min_confidence,
                "llm_used": False,  # Phase 3 will add LLM integration
                "timestamp": datetime.utcnow().isoformat(),
                "pair": candle_data.get("pair"),
                "timeframe": candle_data.get("timeframe"),
            }

            # Add metadata if available
            if "metadata" in fused_decision:
                final_decision["metadata"] = fused_decision["metadata"]

            return final_decision

        except Exception as e:
            # Return safe default on error
            return {
                "action": "hold",
                "confidence": 0.0,
                "confidence_level": "very_low",
                "reasoning": f"Error processing signal: {str(e)}",
                "indicators": {},
                "fusion_method": self.fusion.method.value,
                "confidence_factors": {
                    "strength": 0.0,
                    "agreement": 0.0,
                    "volatility": 0.5,
                    "volume": 0.5,
                },
                "should_trade": False,
                "llm_used": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "pair": candle_data.get("pair"),
                "timeframe": candle_data.get("timeframe"),
            }
