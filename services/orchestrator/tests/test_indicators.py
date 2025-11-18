"""Unit tests for technical indicators."""

import pytest
import pandas as pd
import numpy as np
from app.agents.signal.indicators import (
    EMAIndicator,
    RSIIndicator,
    MACDIndicator,
    SupportResistanceIndicator,
)


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1h")

    # Generate synthetic price data with trend
    base_price = 42000
    trend = np.linspace(0, 2000, 100)
    noise = np.random.randn(100) * 200

    close_prices = base_price + trend + noise

    df = pd.DataFrame({
        "timestamp": dates,
        "open": close_prices * (1 + np.random.randn(100) * 0.002),
        "high": close_prices * (1 + abs(np.random.randn(100)) * 0.005),
        "low": close_prices * (1 - abs(np.random.randn(100)) * 0.005),
        "close": close_prices,
        "volume": np.random.randint(100, 1000, 100),
    })

    return df


class TestEMAIndicator:
    """Test EMA Indicator."""

    def test_ema_initialization(self):
        """Test EMA indicator initialization."""
        ema = EMAIndicator(fast_period=9, slow_period=21, signal_period=50)

        assert ema.fast_period == 9
        assert ema.slow_period == 21
        assert ema.signal_period == 50

    def test_ema_calculate(self, sample_price_data):
        """Test EMA calculation."""
        ema = EMAIndicator()
        df = ema.calculate(sample_price_data)

        assert "ema_fast" in df.columns
        assert "ema_slow" in df.columns
        assert "ema_signal" in df.columns
        assert not df["ema_fast"].isna().all()

    def test_ema_generate_signal_bullish_cross(self, sample_price_data):
        """Test bullish crossover signal."""
        ema = EMAIndicator()

        # Create bullish crossover scenario
        df = sample_price_data.copy()
        signal = ema.generate_signal(df)

        assert signal["action"] in ["buy", "sell", "hold"]
        assert 0 <= signal["strength"] <= 1
        assert "reason" in signal
        assert "metadata" in signal

    def test_ema_insufficient_data(self):
        """Test with insufficient data."""
        ema = EMAIndicator()
        df = pd.DataFrame({"close": [42000, 42100]})

        signal = ema.generate_signal(df)

        assert signal["action"] == "hold"
        assert signal["strength"] == 0.0

    def test_ema_metadata_complete(self, sample_price_data):
        """Test that metadata is complete."""
        ema = EMAIndicator()
        signal = ema.generate_signal(sample_price_data)

        metadata = signal["metadata"]
        assert "fast_ema" in metadata
        assert "slow_ema" in metadata
        assert "signal_ema" in metadata
        assert "bullish_cross" in metadata
        assert "bearish_cross" in metadata


class TestRSIIndicator:
    """Test RSI Indicator."""

    def test_rsi_initialization(self):
        """Test RSI indicator initialization."""
        rsi = RSIIndicator(period=14, overbought=70, oversold=30)

        assert rsi.period == 14
        assert rsi.overbought == 70
        assert rsi.oversold == 30

    def test_rsi_calculate(self, sample_price_data):
        """Test RSI calculation."""
        rsi = RSIIndicator()
        df = rsi.calculate(sample_price_data)

        assert "rsi" in df.columns
        assert not df["rsi"].isna().all()

        # RSI should be between 0 and 100
        valid_rsi = df["rsi"].dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_overbought_signal(self):
        """Test overbought signal generation."""
        rsi = RSIIndicator(oversold=30, overbought=70)

        # Create overbought scenario (strong uptrend)
        df = pd.DataFrame({
            "close": [100 + i * 2 for i in range(50)]  # Strong uptrend
        })

        signal = rsi.generate_signal(df)

        # Should generate sell signal or hold with high RSI
        assert signal["action"] in ["sell", "hold"]
        assert "rsi" in signal["metadata"]

    def test_rsi_oversold_signal(self):
        """Test oversold signal generation."""
        rsi = RSIIndicator(oversold=30, overbought=70)

        # Create oversold scenario (strong downtrend)
        df = pd.DataFrame({
            "close": [100 - i * 2 for i in range(50)]  # Strong downtrend
        })

        signal = rsi.generate_signal(df)

        # Should generate buy signal or hold with low RSI
        assert signal["action"] in ["buy", "hold"]
        assert "rsi" in signal["metadata"]

    def test_rsi_insufficient_data(self):
        """Test with insufficient data."""
        rsi = RSIIndicator(period=14)
        df = pd.DataFrame({"close": [42000, 42100]})

        signal = rsi.generate_signal(df)

        assert signal["action"] == "hold"
        assert signal["strength"] == 0.0


class TestMACDIndicator:
    """Test MACD Indicator."""

    def test_macd_initialization(self):
        """Test MACD indicator initialization."""
        macd = MACDIndicator(fast_period=12, slow_period=26, signal_period=9)

        assert macd.fast_period == 12
        assert macd.slow_period == 26
        assert macd.signal_period == 9

    def test_macd_calculate(self, sample_price_data):
        """Test MACD calculation."""
        macd = MACDIndicator()
        df = macd.calculate(sample_price_data)

        assert "macd" in df.columns
        assert "macd_signal" in df.columns
        assert "macd_histogram" in df.columns
        assert not df["macd"].isna().all()

    def test_macd_generate_signal(self, sample_price_data):
        """Test MACD signal generation."""
        macd = MACDIndicator()
        signal = macd.generate_signal(sample_price_data)

        assert signal["action"] in ["buy", "sell", "hold"]
        assert 0 <= signal["strength"] <= 1
        assert "reason" in signal
        assert "metadata" in signal

    def test_macd_bullish_crossover(self):
        """Test bullish crossover detection."""
        macd = MACDIndicator()

        # Create price data with bullish pattern
        df = pd.DataFrame({
            "close": [100 + i * 0.5 for i in range(60)]  # Gradual uptrend
        })

        signal = macd.generate_signal(df)

        # Should detect trend (either crossover or continuation)
        assert signal["action"] in ["buy", "sell", "hold"]
        assert "macd" in signal["metadata"]
        assert "histogram" in signal["metadata"]

    def test_macd_insufficient_data(self):
        """Test with insufficient data."""
        macd = MACDIndicator()
        df = pd.DataFrame({"close": [42000, 42100]})

        signal = macd.generate_signal(df)

        assert signal["action"] == "hold"
        assert signal["strength"] == 0.0


class TestSupportResistanceIndicator:
    """Test Support/Resistance Indicator."""

    def test_sr_initialization(self):
        """Test S/R indicator initialization."""
        sr = SupportResistanceIndicator(
            lookback_period=50,
            num_levels=3,
            proximity_threshold=0.015
        )

        assert sr.lookback_period == 50
        assert sr.num_levels == 3
        assert sr.proximity_threshold == 0.015

    def test_sr_find_pivot_points(self, sample_price_data):
        """Test pivot point detection."""
        sr = SupportResistanceIndicator()
        df = sr.find_pivot_points(sample_price_data)

        assert "pivot_high" in df.columns
        assert "pivot_low" in df.columns

    def test_sr_calculate(self, sample_price_data):
        """Test S/R level calculation."""
        sr = SupportResistanceIndicator()
        levels = sr.calculate(sample_price_data)

        assert "support_levels" in levels
        assert "resistance_levels" in levels
        assert isinstance(levels["support_levels"], list)
        assert isinstance(levels["resistance_levels"], list)

    def test_sr_generate_signal(self, sample_price_data):
        """Test S/R signal generation."""
        sr = SupportResistanceIndicator()
        signal = sr.generate_signal(sample_price_data)

        assert signal["action"] in ["buy", "sell", "hold"]
        assert 0 <= signal["strength"] <= 1
        assert "metadata" in signal
        assert "support_levels" in signal["metadata"]
        assert "resistance_levels" in signal["metadata"]

    def test_sr_insufficient_data(self):
        """Test with insufficient data."""
        sr = SupportResistanceIndicator(lookback_period=50)
        df = pd.DataFrame({
            "open": [42000],
            "high": [42500],
            "low": [41800],
            "close": [42300],
        })

        signal = sr.generate_signal(df)

        assert signal["action"] == "hold"
        assert signal["strength"] == 0.0

    def test_sr_cluster_levels(self):
        """Test level clustering."""
        sr = SupportResistanceIndicator(proximity_threshold=0.01)

        # Test with similar prices
        prices = [100, 101, 102, 110, 111, 120]
        current_price = 105

        levels = sr.cluster_levels(prices, current_price)

        # Should cluster similar prices
        assert isinstance(levels, list)
        for price, strength in levels:
            assert isinstance(price, (int, float))
            assert isinstance(strength, int)
            assert strength >= sr.strength_threshold
