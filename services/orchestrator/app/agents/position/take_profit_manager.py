"""Partial take-profit management for multi-target exits."""

from typing import Dict, Any, List, Optional
from datetime import datetime


class TakeProfitManager:
    """
    Manages partial take-profit exits based on multiple target levels.
    """

    def __init__(self):
        """Initialize TakeProfitManager."""
        self.active_targets: Dict[str, List[Dict[str, Any]]] = {}

    def setup_take_profit_levels(
        self,
        pair: str,
        position_size: float,
        take_profit_levels: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Setup take-profit levels for a position.

        Args:
            pair: Trading pair
            position_size: Total position size
            take_profit_levels: List of TP levels from RiskAgent
                Example: [
                    {"price": 43000, "allocation": 60},
                    {"price": 44000, "allocation": 40},
                ]

        Returns:
            Take-profit setup configuration
        """
        if not take_profit_levels:
            return {
                "pair": pair,
                "enabled": False,
                "reason": "No take-profit levels provided",
            }

        # Calculate actual amounts for each level
        tp_targets = []
        for level in take_profit_levels:
            amount = position_size * (level["allocation"] / 100.0)
            tp_targets.append({
                "price": level["price"],
                "allocation_pct": level["allocation"],
                "amount": round(amount, 6),
                "hit": False,
                "executed_at": None,
            })

        # Store active targets
        self.active_targets[pair] = tp_targets

        return {
            "pair": pair,
            "enabled": True,
            "total_targets": len(tp_targets),
            "targets": tp_targets,
            "remaining_position": position_size,
        }

    def check_take_profit_hits(
        self,
        pair: str,
        current_price: float,
        action: str,
    ) -> List[Dict[str, Any]]:
        """
        Check if any take-profit levels have been hit.

        Args:
            pair: Trading pair
            current_price: Current market price
            action: Original position action ("buy" or "sell")

        Returns:
            List of hit TP levels that need execution
        """
        if pair not in self.active_targets:
            return []

        hit_targets = []

        for target in self.active_targets[pair]:
            if target["hit"]:
                continue  # Already executed

            # Check if price has reached target
            if action == "buy":
                # For long positions, TP is above entry
                if current_price >= target["price"]:
                    target["hit"] = True
                    target["hit_at"] = datetime.utcnow().isoformat()
                    hit_targets.append(target)

            elif action == "sell":
                # For short positions, TP is below entry
                if current_price <= target["price"]:
                    target["hit"] = True
                    target["hit_at"] = datetime.utcnow().isoformat()
                    hit_targets.append(target)

        return hit_targets

    def mark_target_executed(
        self,
        pair: str,
        price: float,
        order_id: str,
    ) -> bool:
        """
        Mark a take-profit target as executed.

        Args:
            pair: Trading pair
            price: Target price
            order_id: Executed order ID

        Returns:
            True if target was found and marked
        """
        if pair not in self.active_targets:
            return False

        for target in self.active_targets[pair]:
            if target["price"] == price and target["hit"]:
                target["executed_at"] = datetime.utcnow().isoformat()
                target["order_id"] = order_id
                return True

        return False

    def get_remaining_position(self, pair: str) -> Dict[str, Any]:
        """
        Get remaining position size after partial exits.

        Args:
            pair: Trading pair

        Returns:
            Remaining position information
        """
        if pair not in self.active_targets:
            return {
                "pair": pair,
                "remaining_pct": 100.0,
                "closed_pct": 0.0,
                "targets_hit": 0,
                "total_targets": 0,
            }

        targets = self.active_targets[pair]
        executed_targets = [t for t in targets if t.get("executed_at")]
        closed_pct = sum(t["allocation_pct"] for t in executed_targets)

        return {
            "pair": pair,
            "remaining_pct": 100.0 - closed_pct,
            "closed_pct": closed_pct,
            "targets_hit": len(executed_targets),
            "total_targets": len(targets),
            "all_targets_hit": len(executed_targets) == len(targets),
        }

    def get_next_target(self, pair: str) -> Optional[Dict[str, Any]]:
        """
        Get the next unhit take-profit target.

        Args:
            pair: Trading pair

        Returns:
            Next TP target or None
        """
        if pair not in self.active_targets:
            return None

        for target in self.active_targets[pair]:
            if not target["hit"]:
                return target

        return None

    def clear_targets(self, pair: str):
        """
        Clear all take-profit targets for a pair.

        Args:
            pair: Trading pair
        """
        if pair in self.active_targets:
            del self.active_targets[pair]

    def get_status(self, pair: str) -> Dict[str, Any]:
        """
        Get current take-profit status for a pair.

        Args:
            pair: Trading pair

        Returns:
            Complete status of all TP targets
        """
        if pair not in self.active_targets:
            return {
                "pair": pair,
                "enabled": False,
                "targets": [],
            }

        targets = self.active_targets[pair]
        remaining_info = self.get_remaining_position(pair)

        return {
            "pair": pair,
            "enabled": True,
            "targets": targets,
            "total_targets": len(targets),
            "hit_targets": sum(1 for t in targets if t["hit"]),
            "executed_targets": sum(1 for t in targets if t.get("executed_at")),
            "remaining_pct": remaining_info["remaining_pct"],
            "all_complete": remaining_info["all_targets_hit"],
        }
