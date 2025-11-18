"""Unit tests for RiskAgent components."""

import pytest
import pandas as pd
import numpy as np
from app.agents.risk import (
    PositionSizer,
    RiskChecker,
    StopLossCalculator,
    KellyCriterion,
)


@pytest.fixture
def sample_ohlc_data():
    """Create sample OHLC data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start="2024-01-01", periods=50, freq="1h")

    base_price = 42000
    trend = np.linspace(0, 1000, 50)
    noise = np.random.randn(50) * 200

    close_prices = base_price + trend + noise

    df = pd.DataFrame({
        "timestamp": dates,
        "open": close_prices * (1 + np.random.randn(50) * 0.002),
        "high": close_prices * (1 + abs(np.random.randn(50)) * 0.005),
        "low": close_prices * (1 - abs(np.random.randn(50)) * 0.005),
        "close": close_prices,
        "volume": np.random.randint(100, 1000, 50),
    })

    return df


class TestPositionSizer:
    """Test Position Sizer."""

    def test_initialization(self):
        """Test position sizer initialization."""
        sizer = PositionSizer(account_balance=10000, risk_per_trade=0.02)

        assert sizer.account_balance == 10000
        assert sizer.risk_per_trade == 0.02

    def test_calculate_atr(self, sample_ohlc_data):
        """Test ATR calculation."""
        sizer = PositionSizer()
        atr = sizer.calculate_atr(sample_ohlc_data)

        assert atr > 0
        assert isinstance(atr, (int, float))

    def test_calculate_position_size(self):
        """Test position size calculation."""
        sizer = PositionSizer(account_balance=10000, risk_per_trade=0.02)

        result = sizer.calculate_position_size(
            current_price=42000,
            atr=400,
        )

        assert "position_size" in result
        assert "position_value" in result
        assert "risk_amount" in result
        assert result["risk_amount"] == 200  # 2% of 10000

    def test_position_size_constraints(self):
        """Test that position size respects min/max constraints."""
        sizer = PositionSizer(
            account_balance=10000,
            min_position_size=0.001,
            max_position_size=1.0,
        )

        # Test max constraint
        result = sizer.calculate_position_size(
            current_price=100,
            atr=1,  # Small ATR = large position
        )

        assert result["position_size"] <= 1.0

    def test_calculate_with_dataframe(self, sample_ohlc_data):
        """Test position sizing with DataFrame input."""
        sizer = PositionSizer(account_balance=10000)

        result = sizer.calculate_with_dataframe(sample_ohlc_data)

        assert "position_size" in result
        assert "atr" in result
        assert result["position_size"] > 0

    def test_adjust_for_leverage(self):
        """Test leverage adjustment."""
        sizer = PositionSizer()

        result = sizer.adjust_for_leverage(
            position_size=0.1,
            leverage=2.0,
        )

        assert result["leveraged_position_size"] == 0.2
        assert result["leverage"] == 2.0

    def test_update_account_balance(self):
        """Test account balance update."""
        sizer = PositionSizer(account_balance=10000)

        sizer.update_account_balance(15000)
        assert sizer.account_balance == 15000

        # Test invalid balance
        with pytest.raises(ValueError):
            sizer.update_account_balance(-1000)


class TestRiskChecker:
    """Test Risk Checker."""

    def test_initialization(self):
        """Test risk checker initialization."""
        checker = RiskChecker(
            max_position_size=1.0,
            max_open_trades=5,
        )

        assert checker.max_position_size == 1.0
        assert checker.max_open_trades == 5

    def test_check_position_size_approved(self):
        """Test position size check - approved."""
        checker = RiskChecker(max_position_size=1.0)

        result = checker.check_position_size(
            position_size=0.5,
            position_value=5000,
            account_balance=10000,
        )

        assert result["approved"] is True
        assert len(result["warnings"]) == 0

    def test_check_position_size_rejected(self):
        """Test position size check - rejected."""
        checker = RiskChecker(max_position_size=1.0, max_position_value_pct=0.2)

        result = checker.check_position_size(
            position_size=1.5,  # Exceeds max
            position_value=3000,
            account_balance=10000,
        )

        assert result["approved"] is False
        assert len(result["warnings"]) > 0

    def test_check_open_trades_approved(self):
        """Test open trades check - approved."""
        checker = RiskChecker(max_open_trades=5)

        result = checker.check_open_trades(current_open_trades=3)

        assert result["approved"] is True
        assert result["remaining_slots"] == 2

    def test_check_open_trades_rejected(self):
        """Test open trades check - rejected."""
        checker = RiskChecker(max_open_trades=5)

        result = checker.check_open_trades(current_open_trades=5)

        assert result["approved"] is False
        assert result["remaining_slots"] == 0

    def test_check_daily_loss_approved(self):
        """Test daily loss check - approved."""
        checker = RiskChecker(daily_loss_limit_pct=0.05)

        result = checker.check_daily_loss(
            daily_pnl=-200,  # -2% loss
            account_balance=10000,
        )

        assert result["approved"] is True

    def test_check_daily_loss_rejected(self):
        """Test daily loss check - rejected."""
        checker = RiskChecker(daily_loss_limit_pct=0.05)

        result = checker.check_daily_loss(
            daily_pnl=-600,  # -6% loss (exceeds 5% limit)
            account_balance=10000,
        )

        assert result["approved"] is False

    def test_check_total_exposure(self):
        """Test total exposure check."""
        checker = RiskChecker(max_exposure_pct=0.5)

        result = checker.check_total_exposure(
            current_exposure=3000,
            new_position_value=1000,
            account_balance=10000,
        )

        assert result["approved"] is True
        assert result["total_exposure"] == 4000

    def test_validate_trade_all_checks(self):
        """Test complete trade validation."""
        checker = RiskChecker()

        result = checker.validate_trade(
            position_size=0.5,
            position_value=2000,
            account_balance=10000,
            current_open_trades=2,
            daily_pnl=-100,
            current_exposure=1000,
        )

        assert "approved" in result
        assert "risk_score" in result
        assert "checks" in result
        assert len(result["checks"]) == 4  # All 4 checks


class TestStopLossCalculator:
    """Test Stop-Loss Calculator."""

    def test_initialization(self):
        """Test stop-loss calculator initialization."""
        calc = StopLossCalculator(
            atr_period=14,
            default_atr_multiplier=2.0,
        )

        assert calc.atr_period == 14
        assert calc.default_atr_multiplier == 2.0

    def test_atr_based_stop_buy(self):
        """Test ATR-based stop for buy order."""
        calc = StopLossCalculator()

        result = calc.atr_based_stop(
            entry_price=42000,
            atr=400,
            action="buy",
        )

        assert result["method"] == "atr"
        assert result["stop_price"] < 42000  # Stop below entry for buy
        assert result["stop_price"] == 42000 - (400 * 2.0)

    def test_atr_based_stop_sell(self):
        """Test ATR-based stop for sell order."""
        calc = StopLossCalculator()

        result = calc.atr_based_stop(
            entry_price=42000,
            atr=400,
            action="sell",
        )

        assert result["stop_price"] > 42000  # Stop above entry for sell

    def test_fixed_percentage_stop(self):
        """Test fixed percentage stop-loss."""
        calc = StopLossCalculator(default_stop_pct=0.02)

        result = calc.fixed_percentage_stop(
            entry_price=42000,
            action="buy",
        )

        assert result["method"] == "fixed_pct"
        assert result["stop_pct"] == 2.0
        assert result["stop_price"] == 42000 * 0.98

    def test_support_resistance_stop(self):
        """Test support/resistance based stop."""
        calc = StopLossCalculator()

        result = calc.support_resistance_stop(
            entry_price=42000,
            action="buy",
            support_level=41500,
        )

        assert result["method"] == "support_resistance"
        assert result["stop_price"] < 41500  # Below support with buffer

    def test_calculate_take_profit_single_target(self):
        """Test single take-profit calculation."""
        calc = StopLossCalculator(default_risk_reward=2.0)

        result = calc.calculate_take_profit(
            entry_price=42000,
            stop_price=41200,  # 800 risk
            action="buy",
            num_targets=1,
        )

        assert result["num_targets"] == 1
        assert result["risk"] == 800
        assert result["total_reward"] == 1600  # 2:1 RR
        assert result["targets"][0]["price"] == 43600  # 42000 + 1600

    def test_calculate_take_profit_multiple_targets(self):
        """Test multiple take-profit targets."""
        calc = StopLossCalculator()

        result = calc.calculate_take_profit(
            entry_price=42000,
            stop_price=41200,
            action="buy",
            num_targets=2,
        )

        assert result["num_targets"] == 2
        assert len(result["targets"]) == 2
        assert result["targets"][0]["allocation"] == 60  # First target 60%
        assert result["targets"][1]["allocation"] == 40  # Second target 40%

    def test_calculate_complete_levels(self, sample_ohlc_data):
        """Test complete levels calculation."""
        calc = StopLossCalculator()

        result = calc.calculate_complete_levels(
            df=sample_ohlc_data,
            entry_price=42000,
            action="buy",
            method="atr",
        )

        assert "entry_price" in result
        assert "stop_loss" in result
        assert "take_profit" in result
        assert result["stop_loss"]["stop_price"] < result["entry_price"]


class TestKellyCriterion:
    """Test Kelly Criterion."""

    def test_initialization(self):
        """Test Kelly Criterion initialization."""
        kelly = KellyCriterion(
            default_win_rate=0.5,
            default_win_loss_ratio=2.0,
        )

        assert kelly.default_win_rate == 0.5
        assert kelly.default_win_loss_ratio == 2.0

    def test_calculate_kelly_positive(self):
        """Test Kelly calculation with positive expected value."""
        kelly = KellyCriterion()

        result = kelly.calculate_kelly(
            win_rate=0.6,
            win_loss_ratio=2.0,
        )

        assert result["full_kelly"] > 0
        assert result["win_rate"] == 0.6
        assert result["recommendation"] in ["fractional_kelly", "max_kelly"]

    def test_calculate_kelly_negative(self):
        """Test Kelly calculation with negative expected value."""
        kelly = KellyCriterion()

        result = kelly.calculate_kelly(
            win_rate=0.3,  # Low win rate
            win_loss_ratio=1.5,
        )

        # Should recommend not trading
        if result["full_kelly"] <= 0:
            assert result["recommendation"] == "no_trade"

    def test_calculate_position_size(self):
        """Test position size calculation with Kelly."""
        kelly = KellyCriterion()

        result = kelly.calculate_position_size(
            account_balance=10000,
            win_rate=0.55,
            win_loss_ratio=2.0,
        )

        assert "position_value" in result
        assert "position_pct" in result
        assert result["account_balance"] == 10000

    def test_adjust_for_confidence(self):
        """Test Kelly adjustment based on confidence."""
        kelly = KellyCriterion()

        result = kelly.adjust_for_confidence(
            kelly_fraction=0.2,
            confidence_level=0.75,
        )

        assert result["adjusted_kelly"] == 0.2 * 0.75
        assert result["confidence_level"] == 0.75

    def test_estimate_from_history(self):
        """Test Kelly estimation from trading history."""
        kelly = KellyCriterion()

        history = [
            {"pnl": 100},
            {"pnl": -50},
            {"pnl": 150},
            {"pnl": -75},
            {"pnl": 200},
        ]

        result = kelly.estimate_from_history(history)

        assert result["estimated_from_trades"] == 5
        assert result["num_wins"] == 3
        assert result["num_losses"] == 2
        assert "full_kelly" in result
