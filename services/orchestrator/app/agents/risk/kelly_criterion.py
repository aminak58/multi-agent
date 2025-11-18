"""Kelly Criterion for optimal position sizing."""

from typing import Dict, Any, Optional


class KellyCriterion:
    """
    Calculate optimal position size using Kelly Criterion.

    Kelly Formula:
    f* = (p * b - q) / b

    Where:
    - f* = fraction of capital to bet
    - p = probability of win
    - q = probability of loss (1 - p)
    - b = win/loss ratio (profit per unit risked)
    """

    def __init__(
        self,
        default_win_rate: float = 0.5,
        default_win_loss_ratio: float = 2.0,
        max_kelly_fraction: float = 0.25,  # Use max 25% of full Kelly
        fractional_kelly: float = 0.5,  # Use half Kelly by default
    ):
        """
        Initialize Kelly Criterion calculator.

        Args:
            default_win_rate: Default win rate (default: 0.5)
            default_win_loss_ratio: Default win/loss ratio (default: 2.0)
            max_kelly_fraction: Maximum Kelly fraction to use (default: 0.25)
            fractional_kelly: Fraction of full Kelly to use (default: 0.5 = half Kelly)
        """
        self.default_win_rate = default_win_rate
        self.default_win_loss_ratio = default_win_loss_ratio
        self.max_kelly_fraction = max_kelly_fraction
        self.fractional_kelly = fractional_kelly

    def calculate_kelly(
        self,
        win_rate: Optional[float] = None,
        win_loss_ratio: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate Kelly fraction.

        Args:
            win_rate: Probability of winning (0-1)
            win_loss_ratio: Ratio of average win to average loss

        Returns:
            Kelly calculation results
        """
        # Use provided values or defaults
        p = win_rate if win_rate is not None else self.default_win_rate
        b = win_loss_ratio if win_loss_ratio is not None else self.default_win_loss_ratio

        # Validate inputs
        if not 0 < p < 1:
            return {
                "error": "Win rate must be between 0 and 1",
                "win_rate": p,
            }

        if b <= 0:
            return {
                "error": "Win/loss ratio must be positive",
                "win_loss_ratio": b,
            }

        # Calculate Kelly fraction
        # f* = (p * b - q) / b
        q = 1 - p
        kelly_fraction = (p * b - q) / b

        # Kelly can be negative (indicating not to bet)
        # or greater than 1 (indicating leverage opportunity)
        # We constrain it for safety

        # Determine recommendation
        if kelly_fraction <= 0:
            recommendation = "no_trade"
            safe_fraction = 0.0
            reason = "Negative expected value - do not trade"
        elif kelly_fraction > self.max_kelly_fraction:
            recommendation = "max_kelly"
            safe_fraction = self.max_kelly_fraction
            reason = f"Full Kelly ({kelly_fraction:.2%}) exceeds maximum, using {self.max_kelly_fraction:.2%}"
        else:
            recommendation = "fractional_kelly"
            safe_fraction = kelly_fraction * self.fractional_kelly
            reason = f"Using {self.fractional_kelly:.0%} of Kelly for safety"

        return {
            "full_kelly": round(kelly_fraction, 4),
            "safe_kelly": round(safe_fraction, 4),
            "win_rate": round(p, 3),
            "loss_rate": round(q, 3),
            "win_loss_ratio": round(b, 2),
            "recommendation": recommendation,
            "reason": reason,
            "fractional_kelly_multiplier": self.fractional_kelly,
            "max_kelly_fraction": self.max_kelly_fraction,
        }

    def calculate_position_size(
        self,
        account_balance: float,
        win_rate: Optional[float] = None,
        win_loss_ratio: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate position size based on Kelly Criterion.

        Args:
            account_balance: Total account balance
            win_rate: Probability of winning
            win_loss_ratio: Ratio of average win to average loss

        Returns:
            Position size recommendation
        """
        # Calculate Kelly fraction
        kelly_result = self.calculate_kelly(win_rate, win_loss_ratio)

        # Check for errors
        if "error" in kelly_result:
            return kelly_result

        # Calculate position size
        safe_fraction = kelly_result["safe_kelly"]
        position_value = account_balance * safe_fraction

        return {
            **kelly_result,
            "account_balance": round(account_balance, 2),
            "position_value": round(position_value, 2),
            "position_pct": round(safe_fraction * 100, 2),
        }

    def estimate_from_history(
        self,
        trades_history: list,
    ) -> Dict[str, Any]:
        """
        Estimate Kelly parameters from trading history.

        Args:
            trades_history: List of past trades with 'pnl' field

        Returns:
            Estimated parameters and Kelly calculation
        """
        if not trades_history:
            return {
                "error": "No trading history provided",
                "estimated_win_rate": 0.0,
                "estimated_win_loss_ratio": 0.0,
            }

        # Separate wins and losses
        wins = [t["pnl"] for t in trades_history if t.get("pnl", 0) > 0]
        losses = [abs(t["pnl"]) for t in trades_history if t.get("pnl", 0) < 0]

        # Calculate win rate
        total_trades = len(trades_history)
        num_wins = len(wins)
        win_rate = num_wins / total_trades if total_trades > 0 else 0.0

        # Calculate average win and loss
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 1.0  # Avoid division by zero

        # Calculate win/loss ratio
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0

        # Calculate Kelly with estimated parameters
        kelly_result = self.calculate_kelly(win_rate, win_loss_ratio)

        return {
            **kelly_result,
            "estimated_from_trades": total_trades,
            "num_wins": num_wins,
            "num_losses": len(losses),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
        }

    def adjust_for_confidence(
        self,
        kelly_fraction: float,
        confidence_level: float,
    ) -> Dict[str, Any]:
        """
        Adjust Kelly fraction based on signal confidence.

        Args:
            kelly_fraction: Base Kelly fraction
            confidence_level: Signal confidence (0-1)

        Returns:
            Adjusted Kelly fraction
        """
        # Scale Kelly by confidence
        # Higher confidence = use more of Kelly
        # Lower confidence = use less of Kelly

        adjusted_fraction = kelly_fraction * confidence_level

        # Apply maximum constraint
        adjusted_fraction = min(adjusted_fraction, self.max_kelly_fraction)

        return {
            "base_kelly": round(kelly_fraction, 4),
            "confidence_level": round(confidence_level, 3),
            "adjusted_kelly": round(adjusted_fraction, 4),
            "adjustment_factor": round(confidence_level, 3),
        }
