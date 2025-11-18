"""RiskAgent - Risk management and position sizing."""

from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

from app.agents.base import BaseAgent
from app.agents.risk.position_sizer import PositionSizer
from app.agents.risk.risk_checker import RiskChecker
from app.agents.risk.stop_loss_calculator import StopLossCalculator
from app.agents.risk.kelly_criterion import KellyCriterion


class RiskAgent(BaseAgent):
    """
    Risk management agent for position sizing and trade validation.

    Responsibilities:
    - Calculate optimal position size based on ATR
    - Validate trades against risk limits
    - Calculate stop-loss and take-profit levels
    - Optional Kelly Criterion optimization
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize RiskAgent.

        Args:
            config: Configuration dictionary
                - account_balance: Starting account balance (default: 10000)
                - risk_per_trade: Risk percentage per trade (default: 0.02)
                - max_position_size: Maximum position size (default: 1.0)
                - max_open_trades: Maximum concurrent trades (default: 5)
                - daily_loss_limit_pct: Daily loss limit (default: 0.05)
                - use_kelly: Enable Kelly Criterion (default: False)
                - stop_loss_method: Method for stop-loss (default: "atr")
                - risk_reward_ratio: Risk-reward ratio (default: 2.0)
        """
        super().__init__(config)

        # Get configuration
        account_balance = self.get_config_value("account_balance", 10000.0)
        risk_per_trade = self.get_config_value("risk_per_trade", 0.02)
        max_position_size = self.get_config_value("max_position_size", 1.0)
        max_open_trades = self.get_config_value("max_open_trades", 5)
        daily_loss_limit_pct = self.get_config_value("daily_loss_limit_pct", 0.05)

        # Initialize components
        self.position_sizer = PositionSizer(
            account_balance=account_balance,
            risk_per_trade=risk_per_trade,
            max_position_size=max_position_size,
        )

        self.risk_checker = RiskChecker(
            max_position_size=max_position_size,
            max_open_trades=max_open_trades,
            daily_loss_limit_pct=daily_loss_limit_pct,
        )

        self.stop_calculator = StopLossCalculator()

        # Kelly Criterion (optional)
        self.use_kelly = self.get_config_value("use_kelly", False)
        if self.use_kelly:
            self.kelly = KellyCriterion()
        else:
            self.kelly = None

        # Stop-loss configuration
        self.stop_loss_method = self.get_config_value("stop_loss_method", "atr")
        self.risk_reward_ratio = self.get_config_value("risk_reward_ratio", 2.0)

    def process(self, signal_data: Dict[str, Any], candle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process signal and generate risk management decision.

        Args:
            signal_data: Signal from SignalAgent
            candle_data: Market data with OHLC info

        Returns:
            Risk decision with position size, stop-loss, take-profit
        """
        # Validate input
        if not signal_data or not candle_data:
            return self._create_rejection("Invalid input data")

        # Check if signal recommends trading
        action = signal_data.get("action", "hold")
        if action == "hold":
            return self._create_rejection("Signal action is hold")

        # Validate required fields
        if "pair" not in candle_data:
            return self._create_rejection("Missing pair in candle data")

        try:
            # Prepare DataFrame
            df = self._prepare_dataframe(candle_data)
            current_price = df["close"].iloc[-1]

            # Calculate position size
            position_result = self.position_sizer.calculate_with_dataframe(df)

            # Apply Kelly Criterion if enabled
            if self.use_kelly and "confidence" in signal_data:
                kelly_adjustment = self._apply_kelly(
                    position_result["position_size"],
                    signal_data["confidence"],
                )
                position_result.update(kelly_adjustment)

            # Calculate stop-loss and take-profit
            levels = self._calculate_levels(
                df,
                current_price,
                action,
                signal_data,
            )

            # Get account state (would come from database in production)
            account_state = self._get_account_state(candle_data)

            # Validate trade against risk checks
            validation = self.risk_checker.validate_trade(
                position_size=position_result["position_size"],
                position_value=position_result["position_value"],
                account_balance=self.position_sizer.account_balance,
                current_open_trades=account_state["open_trades"],
                daily_pnl=account_state["daily_pnl"],
                current_exposure=account_state["current_exposure"],
            )

            # Build final decision
            approved = validation["approved"]

            decision = {
                "approved": approved,
                "action": action if approved else "hold",
                "pair": candle_data.get("pair"),
                "entry_price": round(current_price, 2),
                "position_size": position_result["position_size"],
                "position_value": position_result["position_value"],
                "position_pct": position_result["position_pct"],
                "stop_loss": levels["stop_loss"]["stop_price"],
                "take_profit": levels["take_profit"]["targets"][0]["price"]
                if levels["take_profit"]["targets"]
                else None,
                "take_profit_levels": levels["take_profit"]["targets"],
                "risk_amount": position_result["risk_amount"],
                "risk_pct": position_result["risk_pct"],
                "risk_reward_ratio": levels["take_profit"]["risk_reward_ratio"],
                "risk_score": validation["risk_score"],
                "validation": validation,
                "warnings": validation["warnings"],
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Add Kelly info if used
            if self.use_kelly and "kelly_adjustment" in position_result:
                decision["kelly_info"] = position_result["kelly_adjustment"]

            # Add metadata
            decision["metadata"] = {
                "stop_loss_method": self.stop_loss_method,
                "position_sizing": position_result,
                "levels": levels,
                "account_state": account_state,
            }

            return decision

        except Exception as e:
            return self._create_rejection(f"Error processing risk: {str(e)}", error=str(e))

    def _prepare_dataframe(self, candle_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare DataFrame from candle data."""
        if "candles" in candle_data:
            df = pd.DataFrame(candle_data["candles"])
        else:
            df = pd.DataFrame([{
                "timestamp": candle_data.get("timestamp"),
                "open": candle_data.get("open"),
                "high": candle_data.get("high"),
                "low": candle_data.get("low"),
                "close": candle_data.get("close"),
                "volume": candle_data.get("volume", 0),
            }])

        required_columns = ["open", "high", "low", "close"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame missing required columns: {required_columns}")

        return df

    def _calculate_levels(
        self,
        df: pd.DataFrame,
        entry_price: float,
        action: str,
        signal_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate stop-loss and take-profit levels."""
        # Extract S/R levels from signal if available
        support = None
        resistance = None

        if "indicators" in signal_data:
            sr_signal = signal_data["indicators"].get("support_resistance", {})
            metadata = sr_signal.get("metadata", {})

            if "nearest_support" in metadata and metadata["nearest_support"]:
                support = metadata["nearest_support"]["price"]

            if "nearest_resistance" in metadata and metadata["nearest_resistance"]:
                resistance = metadata["nearest_resistance"]["price"]

        # Calculate levels
        levels = self.stop_calculator.calculate_complete_levels(
            df=df,
            entry_price=entry_price,
            action=action,
            method=self.stop_loss_method,
            support_level=support,
            resistance_level=resistance,
            risk_reward_ratio=self.risk_reward_ratio,
        )

        return levels

    def _apply_kelly(
        self,
        base_position_size: float,
        confidence: float,
    ) -> Dict[str, Any]:
        """Apply Kelly Criterion adjustment."""
        # Adjust Kelly based on confidence
        kelly_result = self.kelly.calculate_kelly()

        if "error" in kelly_result:
            return {"kelly_adjustment": kelly_result}

        # Adjust by confidence
        adjusted_kelly = self.kelly.adjust_for_confidence(
            kelly_result["safe_kelly"],
            confidence,
        )

        # Calculate adjusted position size
        adjusted_size = base_position_size * adjusted_kelly["adjusted_kelly"] / 0.5

        return {
            "kelly_adjustment": adjusted_kelly,
            "adjusted_position_size": round(adjusted_size, 6),
            "kelly_used": True,
        }

    def _get_account_state(self, candle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current account state.

        In production, this would query from database.
        For now, returns defaults from candle_data or zeros.
        """
        return {
            "open_trades": candle_data.get("current_open_trades", 0),
            "daily_pnl": candle_data.get("daily_pnl", 0.0),
            "current_exposure": candle_data.get("current_exposure", 0.0),
        }

    def _create_rejection(
        self,
        reason: str,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a rejection decision."""
        decision = {
            "approved": False,
            "action": "hold",
            "position_size": 0.0,
            "stop_loss": None,
            "take_profit": None,
            "risk_score": 1.0,  # Maximum risk (rejected)
            "warnings": [reason],
            "timestamp": datetime.utcnow().isoformat(),
        }

        if error:
            decision["error"] = error

        return decision

    def update_account_balance(self, new_balance: float):
        """Update account balance."""
        self.position_sizer.update_account_balance(new_balance)
