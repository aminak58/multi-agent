"""Position sizing calculator using ATR (Average True Range)."""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


class PositionSizer:
    """
    Calculate position size based on ATR and risk parameters.

    ATR-based position sizing ensures consistent risk per trade
    regardless of market volatility.
    """

    def __init__(
        self,
        account_balance: float = 10000.0,
        risk_per_trade: float = 0.02,  # 2% risk per trade
        atr_period: int = 14,
        atr_multiplier: float = 2.0,  # Stop-loss = ATR * multiplier
        min_position_size: float = 0.001,
        max_position_size: float = 1.0,
    ):
        """
        Initialize position sizer.

        Args:
            account_balance: Total account balance
            risk_per_trade: Risk percentage per trade (default: 0.02 = 2%)
            atr_period: ATR calculation period (default: 14)
            atr_multiplier: Multiplier for stop-loss distance (default: 2.0)
            min_position_size: Minimum position size (default: 0.001)
            max_position_size: Maximum position size (default: 1.0)
        """
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.min_position_size = min_position_size
        self.max_position_size = max_position_size

    def calculate_atr(self, df: pd.DataFrame) -> float:
        """
        Calculate Average True Range.

        Args:
            df: DataFrame with OHLC data

        Returns:
            ATR value
        """
        if len(df) < self.atr_period:
            # Fallback to simple range if insufficient data
            return (df["high"].max() - df["low"].min()) / len(df)

        # Calculate True Range
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Calculate ATR
        atr = tr.rolling(window=self.atr_period).mean().iloc[-1]

        return atr if not pd.isna(atr) else tr.mean()

    def calculate_position_size(
        self,
        current_price: float,
        atr: float,
        custom_risk: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate position size based on ATR.

        Formula:
        Position Size = (Account Balance * Risk %) / (ATR * Multiplier)

        Args:
            current_price: Current market price
            atr: Average True Range
            custom_risk: Custom risk percentage (overrides default)

        Returns:
            Dictionary with position size and details
        """
        # Use custom risk or default
        risk_pct = custom_risk if custom_risk is not None else self.risk_per_trade

        # Calculate risk amount in currency
        risk_amount = self.account_balance * risk_pct

        # Calculate stop-loss distance
        stop_distance = atr * self.atr_multiplier

        # Calculate position size
        # Position size = Risk amount / Stop distance
        if stop_distance > 0:
            position_size = risk_amount / stop_distance
        else:
            position_size = self.min_position_size

        # Apply constraints
        position_size = max(self.min_position_size, min(position_size, self.max_position_size))

        # Calculate position value
        position_value = position_size * current_price

        # Calculate position as percentage of account
        position_pct = (position_value / self.account_balance) * 100

        return {
            "position_size": round(position_size, 6),
            "position_value": round(position_value, 2),
            "position_pct": round(position_pct, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_pct": round(risk_pct * 100, 2),
            "stop_distance": round(stop_distance, 2),
            "stop_distance_pct": round((stop_distance / current_price) * 100, 2),
            "atr": round(atr, 2),
            "atr_multiplier": self.atr_multiplier,
        }

    def calculate_with_dataframe(
        self,
        df: pd.DataFrame,
        custom_risk: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate position size with DataFrame input.

        Args:
            df: DataFrame with OHLC data
            custom_risk: Custom risk percentage

        Returns:
            Position sizing details
        """
        if len(df) == 0:
            raise ValueError("DataFrame is empty")

        # Get current price
        current_price = df["close"].iloc[-1]

        # Calculate ATR
        atr = self.calculate_atr(df)

        # Calculate position size
        return self.calculate_position_size(current_price, atr, custom_risk)

    def adjust_for_leverage(
        self,
        position_size: float,
        leverage: float = 1.0,
        max_leverage: float = 3.0,
    ) -> Dict[str, Any]:
        """
        Adjust position size for leverage trading.

        Args:
            position_size: Base position size
            leverage: Desired leverage (default: 1.0 = no leverage)
            max_leverage: Maximum allowed leverage (default: 3.0)

        Returns:
            Adjusted position details
        """
        # Constrain leverage
        effective_leverage = min(leverage, max_leverage)

        # Calculate leveraged position
        leveraged_size = position_size * effective_leverage

        # Apply max position constraint
        leveraged_size = min(leveraged_size, self.max_position_size)

        return {
            "base_position_size": round(position_size, 6),
            "leverage": effective_leverage,
            "leveraged_position_size": round(leveraged_size, 6),
            "max_leverage": max_leverage,
        }

    def update_account_balance(self, new_balance: float):
        """
        Update account balance.

        Args:
            new_balance: New account balance
        """
        if new_balance <= 0:
            raise ValueError("Account balance must be positive")

        self.account_balance = new_balance
