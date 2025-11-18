"""Integration tests for SignalAgent."""

import pytest
import pandas as pd
import numpy as np
from app.agents.signal import SignalAgent, FusionMethod


@pytest.fixture
def sample_candle_with_history():
    """Create sample candle data with historical candles."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1h")

    base_price = 42000
    trend = np.linspace(0, 2000, 100)
    noise = np.random.randn(100) * 200

    close_prices = base_price + trend + noise

    candles = []
    for i in range(100):
        candles.append({
            "timestamp": int(dates[i].timestamp()),
            "open": float(close_prices[i] * (1 + np.random.randn() * 0.002)),
            "high": float(close_prices[i] * (1 + abs(np.random.randn()) * 0.005)),
            "low": float(close_prices[i] * (1 - abs(np.random.randn()) * 0.005)),
            "close": float(close_prices[i]),
            "volume": float(np.random.randint(100, 1000)),
        })

    return {
        "pair": "BTC/USDT",
        "timeframe": "1h",
        "candles": candles,
    }


class TestSignalAgentInitialization:
    """Test SignalAgent initialization."""

    def test_default_initialization(self):
        """Test agent initialization with defaults."""
        agent = SignalAgent()

        assert agent.name == "SignalAgent"
        assert len(agent.indicators) == 4  # All indicators enabled by default
        assert "ema" in agent.indicators
        assert "rsi" in agent.indicators
        assert "macd" in agent.indicators
        assert "support_resistance" in agent.indicators

    def test_custom_configuration(self):
        """Test agent initialization with custom config."""
        config = {
            "fusion_method": "majority_vote",
            "min_confidence": 0.6,
            "enable_ema": True,
            "enable_rsi": True,
            "enable_macd": False,
            "enable_sr": False,
        }

        agent = SignalAgent(config=config)

        assert agent.min_confidence == 0.6
        assert len(agent.indicators) == 2  # Only EMA and RSI
        assert "ema" in agent.indicators
        assert "rsi" in agent.indicators
        assert "macd" not in agent.indicators

    def test_custom_indicator_weights(self):
        """Test custom indicator weights."""
        config = {
            "indicator_weights": {
                "ema": 0.4,
                "rsi": 0.3,
                "macd": 0.2,
                "support_resistance": 0.1,
            }
        }

        agent = SignalAgent(config=config)

        assert agent.fusion.weights["ema"] == 0.4
        assert agent.fusion.weights["rsi"] == 0.3


class TestSignalAgentProcessing:
    """Test SignalAgent signal processing."""

    def test_process_with_history(self, sample_candle_with_history):
        """Test signal generation with historical data."""
        agent = SignalAgent()
        decision = agent.process(sample_candle_with_history)

        # Check response structure
        assert "action" in decision
        assert "confidence" in decision
        assert "confidence_level" in decision
        assert "reasoning" in decision
        assert "indicators" in decision
        assert "fusion_method" in decision
        assert "confidence_factors" in decision
        assert "should_trade" in decision
        assert "llm_used" in decision
        assert "timestamp" in decision

        # Check action is valid
        assert decision["action"] in ["buy", "sell", "hold"]

        # Check confidence is in valid range
        assert 0 <= decision["confidence"] <= 1

        # Check all indicators provided signals
        assert len(decision["indicators"]) == 4

    def test_process_invalid_input(self):
        """Test with invalid input data."""
        agent = SignalAgent()

        invalid_data = {"pair": "BTC/USDT"}  # Missing required fields

        decision = agent.process(invalid_data)

        assert decision["action"] == "hold"
        assert decision["confidence"] == 0.0
        assert "Invalid input" in decision["reasoning"]

    def test_process_single_candle(self):
        """Test with single candle (no history)."""
        agent = SignalAgent()

        candle_data = {
            "pair": "BTC/USDT",
            "timeframe": "1h",
            "timestamp": 1704067200,
            "open": 42000.0,
            "high": 42500.0,
            "low": 41800.0,
            "close": 42300.0,
            "volume": 1000.0,
        }

        decision = agent.process(candle_data)

        # Should still generate decision (though may be low confidence)
        assert "action" in decision
        assert decision["llm_used"] is False

    def test_different_fusion_methods(self, sample_candle_with_history):
        """Test different fusion methods."""
        fusion_methods = ["weighted_average", "majority_vote", "conservative", "aggressive"]

        for method in fusion_methods:
            agent = SignalAgent(config={"fusion_method": method})
            decision = agent.process(sample_candle_with_history)

            assert decision["fusion_method"] == method
            assert "action" in decision


class TestSignalAgentConfidence:
    """Test SignalAgent confidence calculations."""

    def test_confidence_factors(self, sample_candle_with_history):
        """Test that confidence factors are calculated."""
        agent = SignalAgent()
        decision = agent.process(sample_candle_with_history)

        factors = decision["confidence_factors"]

        assert "strength" in factors
        assert "agreement" in factors
        assert "volatility" in factors
        assert "volume" in factors

        # All factors should be in valid range
        for factor_value in factors.values():
            assert 0 <= factor_value <= 1

    def test_confidence_level_mapping(self, sample_candle_with_history):
        """Test confidence level categorization."""
        agent = SignalAgent()
        decision = agent.process(sample_candle_with_history)

        valid_levels = ["very_low", "low", "medium", "high", "very_high"]
        assert decision["confidence_level"] in valid_levels

    def test_should_trade_threshold(self, sample_candle_with_history):
        """Test should_trade flag based on confidence threshold."""
        # High threshold
        agent_conservative = SignalAgent(config={"min_confidence": 0.8})
        decision = agent_conservative.process(sample_candle_with_history)

        if decision["confidence"] < 0.8:
            assert decision["should_trade"] is False

        # Low threshold
        agent_aggressive = SignalAgent(config={"min_confidence": 0.3})
        decision = agent_aggressive.process(sample_candle_with_history)

        if decision["confidence"] >= 0.3:
            assert decision["should_trade"] is True


class TestSignalAgentIndicatorSignals:
    """Test individual indicator signals in agent context."""

    def test_all_indicators_generate_signals(self, sample_candle_with_history):
        """Test that all indicators generate signals."""
        agent = SignalAgent()
        decision = agent.process(sample_candle_with_history)

        indicators = decision["indicators"]

        assert "ema" in indicators
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "support_resistance" in indicators

        # Each indicator should have proper structure
        for indicator_name, indicator_signal in indicators.items():
            assert "action" in indicator_signal
            assert "strength" in indicator_signal
            assert "reason" in indicator_signal

    def test_selective_indicators(self, sample_candle_with_history):
        """Test with selective indicators enabled."""
        config = {
            "enable_ema": True,
            "enable_rsi": False,
            "enable_macd": False,
            "enable_sr": False,
        }

        agent = SignalAgent(config=config)
        decision = agent.process(sample_candle_with_history)

        indicators = decision["indicators"]

        assert "ema" in indicators
        assert "rsi" not in indicators
        assert "macd" not in indicators


class TestSignalAgentErrorHandling:
    """Test SignalAgent error handling."""

    def test_error_handling_malformed_data(self):
        """Test error handling with malformed data."""
        agent = SignalAgent()

        malformed_data = {
            "pair": "BTC/USDT",
            "candles": [
                {"close": "not_a_number"}  # Invalid data type
            ]
        }

        decision = agent.process(malformed_data)

        # Should return safe default
        assert decision["action"] == "hold"
        assert "error" in decision or decision["confidence"] == 0.0

    def test_missing_required_columns(self):
        """Test with missing required columns in DataFrame."""
        agent = SignalAgent()

        invalid_candles = {
            "pair": "BTC/USDT",
            "candles": [
                {"timestamp": 1704067200, "close": 42000}  # Missing OHLC
            ]
        }

        decision = agent.process(invalid_candles)

        # Should handle gracefully
        assert "action" in decision


class TestSignalAgentReproducibility:
    """Test SignalAgent reproducibility."""

    def test_same_input_same_output(self, sample_candle_with_history):
        """Test that same input produces same output."""
        agent = SignalAgent()

        decision1 = agent.process(sample_candle_with_history)
        decision2 = agent.process(sample_candle_with_history)

        # Core decision should be identical
        assert decision1["action"] == decision2["action"]
        assert decision1["confidence"] == decision2["confidence"]
        assert decision1["fusion_method"] == decision2["fusion_method"]

        # Indicators should produce same signals
        for indicator_name in decision1["indicators"]:
            assert decision1["indicators"][indicator_name]["action"] == \
                   decision2["indicators"][indicator_name]["action"]
