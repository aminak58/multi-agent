"""Risk validation checks for trading decisions."""

from typing import Dict, Any, List
from datetime import datetime, timedelta


class RiskChecker:
    """
    Validates trading decisions against risk management rules.

    Ensures trades comply with:
    - Maximum position size limits
    - Maximum open trades limit
    - Daily loss limits
    - Total exposure limits
    """

    def __init__(
        self,
        max_position_size: float = 1.0,
        max_position_value_pct: float = 0.2,  # 20% of account per position
        max_open_trades: int = 5,
        daily_loss_limit_pct: float = 0.05,  # 5% daily loss limit
        max_exposure_pct: float = 0.5,  # 50% total exposure
        max_correlated_exposure_pct: float = 0.3,  # 30% in correlated assets
    ):
        """
        Initialize risk checker.

        Args:
            max_position_size: Maximum position size in units
            max_position_value_pct: Maximum position value as % of account
            max_open_trades: Maximum number of concurrent open trades
            daily_loss_limit_pct: Maximum daily loss as % of account
            max_exposure_pct: Maximum total exposure as % of account
            max_correlated_exposure_pct: Maximum exposure in correlated assets
        """
        self.max_position_size = max_position_size
        self.max_position_value_pct = max_position_value_pct
        self.max_open_trades = max_open_trades
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.max_exposure_pct = max_exposure_pct
        self.max_correlated_exposure_pct = max_correlated_exposure_pct

    def check_position_size(
        self,
        position_size: float,
        position_value: float,
        account_balance: float,
    ) -> Dict[str, Any]:
        """
        Check if position size is within limits.

        Args:
            position_size: Proposed position size
            position_value: Position value in currency
            account_balance: Current account balance

        Returns:
            Validation result
        """
        warnings = []
        approved = True

        # Check absolute position size
        if position_size > self.max_position_size:
            warnings.append(
                f"Position size ({position_size:.4f}) exceeds maximum ({self.max_position_size})"
            )
            approved = False

        # Check position value as percentage of account
        position_pct = (position_value / account_balance) * 100
        max_pct = self.max_position_value_pct * 100

        if position_pct > max_pct:
            warnings.append(
                f"Position value ({position_pct:.1f}%) exceeds maximum ({max_pct:.1f}%)"
            )
            approved = False

        return {
            "check": "position_size",
            "approved": approved,
            "position_size": position_size,
            "position_value_pct": round(position_pct, 2),
            "max_position_value_pct": round(max_pct, 2),
            "warnings": warnings,
        }

    def check_open_trades(
        self,
        current_open_trades: int,
    ) -> Dict[str, Any]:
        """
        Check if we can open a new trade.

        Args:
            current_open_trades: Number of currently open trades

        Returns:
            Validation result
        """
        warnings = []
        approved = True

        if current_open_trades >= self.max_open_trades:
            warnings.append(
                f"Maximum open trades reached ({current_open_trades}/{self.max_open_trades})"
            )
            approved = False

        return {
            "check": "open_trades",
            "approved": approved,
            "current_open_trades": current_open_trades,
            "max_open_trades": self.max_open_trades,
            "remaining_slots": max(0, self.max_open_trades - current_open_trades),
            "warnings": warnings,
        }

    def check_daily_loss(
        self,
        daily_pnl: float,
        account_balance: float,
    ) -> Dict[str, Any]:
        """
        Check if daily loss limit is breached.

        Args:
            daily_pnl: Today's profit/loss
            account_balance: Current account balance

        Returns:
            Validation result
        """
        warnings = []
        approved = True

        # Calculate daily loss percentage
        daily_loss_pct = abs(daily_pnl / account_balance) if daily_pnl < 0 else 0
        max_loss_pct = self.daily_loss_limit_pct

        if daily_loss_pct >= max_loss_pct:
            warnings.append(
                f"Daily loss limit breached ({daily_loss_pct:.2%} >= {max_loss_pct:.2%})"
            )
            approved = False
        elif daily_loss_pct >= max_loss_pct * 0.8:  # Warning at 80%
            warnings.append(
                f"Approaching daily loss limit ({daily_loss_pct:.2%} / {max_loss_pct:.2%})"
            )

        return {
            "check": "daily_loss",
            "approved": approved,
            "daily_pnl": round(daily_pnl, 2),
            "daily_loss_pct": round(daily_loss_pct * 100, 2),
            "daily_loss_limit_pct": round(max_loss_pct * 100, 2),
            "remaining_loss_allowance": round(
                (max_loss_pct - daily_loss_pct) * account_balance, 2
            ),
            "warnings": warnings,
        }

    def check_total_exposure(
        self,
        current_exposure: float,
        new_position_value: float,
        account_balance: float,
    ) -> Dict[str, Any]:
        """
        Check total market exposure.

        Args:
            current_exposure: Current total exposure value
            new_position_value: Value of new position
            account_balance: Current account balance

        Returns:
            Validation result
        """
        warnings = []
        approved = True

        # Calculate total exposure with new position
        total_exposure = current_exposure + new_position_value
        exposure_pct = (total_exposure / account_balance)
        max_pct = self.max_exposure_pct

        if exposure_pct > max_pct:
            warnings.append(
                f"Total exposure ({exposure_pct:.2%}) exceeds maximum ({max_pct:.2%})"
            )
            approved = False
        elif exposure_pct > max_pct * 0.9:  # Warning at 90%
            warnings.append(
                f"Approaching exposure limit ({exposure_pct:.2%} / {max_pct:.2%})"
            )

        return {
            "check": "total_exposure",
            "approved": approved,
            "current_exposure": round(current_exposure, 2),
            "new_position_value": round(new_position_value, 2),
            "total_exposure": round(total_exposure, 2),
            "exposure_pct": round(exposure_pct * 100, 2),
            "max_exposure_pct": round(max_pct * 100, 2),
            "remaining_capacity": round((max_pct - exposure_pct) * account_balance, 2),
            "warnings": warnings,
        }

    def validate_trade(
        self,
        position_size: float,
        position_value: float,
        account_balance: float,
        current_open_trades: int = 0,
        daily_pnl: float = 0.0,
        current_exposure: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Run all risk checks for a trade.

        Args:
            position_size: Proposed position size
            position_value: Position value
            account_balance: Account balance
            current_open_trades: Number of open trades
            daily_pnl: Today's P&L
            current_exposure: Current market exposure

        Returns:
            Complete validation result
        """
        checks = []

        # Run all checks
        checks.append(self.check_position_size(position_size, position_value, account_balance))
        checks.append(self.check_open_trades(current_open_trades))
        checks.append(self.check_daily_loss(daily_pnl, account_balance))
        checks.append(self.check_total_exposure(current_exposure, position_value, account_balance))

        # Aggregate results
        all_approved = all(check["approved"] for check in checks)
        all_warnings = []
        for check in checks:
            all_warnings.extend(check.get("warnings", []))

        # Calculate risk score (0-1, higher = riskier)
        risk_factors = []

        # Position size risk
        pos_check = checks[0]
        if pos_check["position_value_pct"] > 0:
            risk_factors.append(
                pos_check["position_value_pct"] / pos_check["max_position_value_pct"]
            )

        # Open trades risk
        trades_check = checks[1]
        risk_factors.append(
            trades_check["current_open_trades"] / trades_check["max_open_trades"]
        )

        # Daily loss risk
        loss_check = checks[2]
        risk_factors.append(loss_check["daily_loss_pct"] / loss_check["daily_loss_limit_pct"])

        # Exposure risk
        exp_check = checks[3]
        risk_factors.append(exp_check["exposure_pct"] / exp_check["max_exposure_pct"])

        risk_score = sum(risk_factors) / len(risk_factors) if risk_factors else 0.0

        return {
            "approved": all_approved,
            "risk_score": round(risk_score, 3),
            "checks": checks,
            "warnings": all_warnings,
            "summary": f"{'✓ Approved' if all_approved else '✗ Rejected'} - Risk Score: {risk_score:.2f}",
        }
