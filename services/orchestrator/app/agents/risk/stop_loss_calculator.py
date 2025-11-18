"""Stop-loss and take-profit calculator."""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np


class StopLossCalculator:
    """
    Calculate optimal stop-loss and take-profit levels.

    Supports multiple methods:
    - ATR-based (volatility-adjusted)
    - Fixed percentage
    - Support/resistance based
    - Risk-reward ratio based
    """

    def __init__(
        self,
        atr_period: int = 14,
        default_atr_multiplier: float = 2.0,
        default_stop_pct: float = 0.02,  # 2%
        default_risk_reward: float = 2.0,  # 1:2 risk-reward
        min_risk_reward: float = 1.5,
    ):
        """
        Initialize stop-loss calculator.

        Args:
            atr_period: ATR calculation period
            default_atr_multiplier: Default ATR multiplier for stop-loss
            default_stop_pct: Default fixed percentage for stop-loss
            default_risk_reward: Default risk-reward ratio
            min_risk_reward: Minimum acceptable risk-reward ratio
        """
        self.atr_period = atr_period
        self.default_atr_multiplier = default_atr_multiplier
        self.default_stop_pct = default_stop_pct
        self.default_risk_reward = default_risk_reward
        self.min_risk_reward = min_risk_reward

    def calculate_atr(self, df: pd.DataFrame) -> float:
        """
        Calculate Average True Range.

        Args:
            df: DataFrame with OHLC data

        Returns:
            ATR value
        """
        if len(df) < self.atr_period:
            return (df["high"].max() - df["low"].min()) / len(df)

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean().iloc[-1]

        return atr if not pd.isna(atr) else tr.mean()

    def atr_based_stop(
        self,
        entry_price: float,
        atr: float,
        action: str,
        atr_multiplier: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate ATR-based stop-loss.

        Args:
            entry_price: Entry price
            atr: Average True Range
            action: Trade direction ('buy' or 'sell')
            atr_multiplier: ATR multiplier (uses default if None)

        Returns:
            Stop-loss details
        """
        multiplier = atr_multiplier if atr_multiplier is not None else self.default_atr_multiplier

        # Calculate stop distance
        stop_distance = atr * multiplier

        # Calculate stop price
        if action.lower() == "buy":
            stop_price = entry_price - stop_distance
        else:  # sell
            stop_price = entry_price + stop_distance

        # Calculate stop percentage
        stop_pct = (stop_distance / entry_price) * 100

        return {
            "method": "atr",
            "stop_price": round(stop_price, 2),
            "stop_distance": round(stop_distance, 2),
            "stop_pct": round(stop_pct, 2),
            "atr": round(atr, 2),
            "atr_multiplier": multiplier,
        }

    def fixed_percentage_stop(
        self,
        entry_price: float,
        action: str,
        stop_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate fixed percentage stop-loss.

        Args:
            entry_price: Entry price
            action: Trade direction ('buy' or 'sell')
            stop_pct: Stop percentage (uses default if None)

        Returns:
            Stop-loss details
        """
        pct = stop_pct if stop_pct is not None else self.default_stop_pct

        # Calculate stop distance
        stop_distance = entry_price * pct

        # Calculate stop price
        if action.lower() == "buy":
            stop_price = entry_price - stop_distance
        else:  # sell
            stop_price = entry_price + stop_distance

        return {
            "method": "fixed_pct",
            "stop_price": round(stop_price, 2),
            "stop_distance": round(stop_distance, 2),
            "stop_pct": round(pct * 100, 2),
        }

    def support_resistance_stop(
        self,
        entry_price: float,
        action: str,
        support_level: Optional[float] = None,
        resistance_level: Optional[float] = None,
        buffer_pct: float = 0.005,  # 0.5% buffer
    ) -> Dict[str, Any]:
        """
        Calculate stop-loss based on support/resistance levels.

        Args:
            entry_price: Entry price
            action: Trade direction ('buy' or 'sell')
            support_level: Support price level
            resistance_level: Resistance price level
            buffer_pct: Buffer percentage beyond S/R level

        Returns:
            Stop-loss details
        """
        if action.lower() == "buy":
            if support_level is None:
                return {"method": "support_resistance", "error": "Support level required for buy"}

            # Place stop below support
            buffer = support_level * buffer_pct
            stop_price = support_level - buffer

        else:  # sell
            if resistance_level is None:
                return {
                    "method": "support_resistance",
                    "error": "Resistance level required for sell",
                }

            # Place stop above resistance
            buffer = resistance_level * buffer_pct
            stop_price = resistance_level + buffer

        stop_distance = abs(entry_price - stop_price)
        stop_pct = (stop_distance / entry_price) * 100

        return {
            "method": "support_resistance",
            "stop_price": round(stop_price, 2),
            "stop_distance": round(stop_distance, 2),
            "stop_pct": round(stop_pct, 2),
            "reference_level": support_level if action.lower() == "buy" else resistance_level,
            "buffer_pct": round(buffer_pct * 100, 2),
        }

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_price: float,
        action: str,
        risk_reward_ratio: Optional[float] = None,
        num_targets: int = 1,
    ) -> Dict[str, Any]:
        """
        Calculate take-profit levels based on risk-reward ratio.

        Args:
            entry_price: Entry price
            stop_price: Stop-loss price
            action: Trade direction ('buy' or 'sell')
            risk_reward_ratio: Risk-reward ratio (uses default if None)
            num_targets: Number of take-profit targets (1-3)

        Returns:
            Take-profit details
        """
        rr_ratio = (
            risk_reward_ratio if risk_reward_ratio is not None else self.default_risk_reward
        )

        # Ensure minimum risk-reward
        rr_ratio = max(rr_ratio, self.min_risk_reward)

        # Calculate risk (distance to stop)
        risk = abs(entry_price - stop_price)

        # Calculate reward (distance to target)
        reward = risk * rr_ratio

        # Calculate take-profit prices
        targets = []

        if num_targets == 1:
            # Single target
            if action.lower() == "buy":
                tp_price = entry_price + reward
            else:
                tp_price = entry_price - reward

            targets.append({
                "level": 1,
                "price": round(tp_price, 2),
                "distance": round(reward, 2),
                "distance_pct": round((reward / entry_price) * 100, 2),
                "allocation": 100,
            })

        else:
            # Multiple targets with proportional allocation
            # TP1: 1R, TP2: 2R, TP3: 3R
            allocations = [50, 30, 20] if num_targets == 3 else [60, 40]

            for i in range(min(num_targets, 3)):
                partial_reward = risk * (i + 1) * rr_ratio / num_targets * (i + 1)

                if action.lower() == "buy":
                    tp_price = entry_price + partial_reward
                else:
                    tp_price = entry_price - partial_reward

                targets.append({
                    "level": i + 1,
                    "price": round(tp_price, 2),
                    "distance": round(partial_reward, 2),
                    "distance_pct": round((partial_reward / entry_price) * 100, 2),
                    "allocation": allocations[i] if i < len(allocations) else 0,
                })

        return {
            "risk_reward_ratio": rr_ratio,
            "risk": round(risk, 2),
            "total_reward": round(reward, 2),
            "num_targets": len(targets),
            "targets": targets,
        }

    def calculate_complete_levels(
        self,
        df: pd.DataFrame,
        entry_price: float,
        action: str,
        method: str = "atr",
        support_level: Optional[float] = None,
        resistance_level: Optional[float] = None,
        custom_stop_pct: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
        num_tp_targets: int = 2,
    ) -> Dict[str, Any]:
        """
        Calculate complete stop-loss and take-profit levels.

        Args:
            df: DataFrame with OHLC data
            entry_price: Entry price
            action: Trade direction ('buy' or 'sell')
            method: Stop-loss method ('atr', 'fixed_pct', 'support_resistance')
            support_level: Support level (for S/R method)
            resistance_level: Resistance level (for S/R method)
            custom_stop_pct: Custom stop percentage (for fixed_pct method)
            risk_reward_ratio: Risk-reward ratio
            num_tp_targets: Number of take-profit targets

        Returns:
            Complete levels with stop-loss and take-profit
        """
        # Calculate stop-loss based on method
        if method == "atr":
            atr = self.calculate_atr(df)
            stop_result = self.atr_based_stop(entry_price, atr, action)

        elif method == "fixed_pct":
            stop_result = self.fixed_percentage_stop(entry_price, action, custom_stop_pct)

        elif method == "support_resistance":
            stop_result = self.support_resistance_stop(
                entry_price, action, support_level, resistance_level
            )

        else:
            # Default to ATR
            atr = self.calculate_atr(df)
            stop_result = self.atr_based_stop(entry_price, atr, action)

        # Check for errors
        if "error" in stop_result:
            return stop_result

        # Calculate take-profit
        tp_result = self.calculate_take_profit(
            entry_price,
            stop_result["stop_price"],
            action,
            risk_reward_ratio,
            num_tp_targets,
        )

        return {
            "entry_price": round(entry_price, 2),
            "action": action,
            "stop_loss": stop_result,
            "take_profit": tp_result,
            "risk_pct": stop_result["stop_pct"],
            "reward_pct": tp_result["total_reward"] / entry_price * 100,
        }
