"""Basic trailing stop implementation."""

from typing import Dict, Any, Optional
from datetime import datetime


class TrailingStopManager:
    """
    Manages trailing stop-loss orders that adjust with price movement.
    """

    def __init__(
        self,
        trailing_distance_pct: float = 0.02,  # 2% default
        activation_profit_pct: float = 0.01,  # Activate after 1% profit
    ):
        """
        Initialize TrailingStopManager.

        Args:
            trailing_distance_pct: Trailing distance as percentage (0.02 = 2%)
            activation_profit_pct: Minimum profit before trailing activates
        """
        self.trailing_distance_pct = trailing_distance_pct
        self.activation_profit_pct = activation_profit_pct
        self.active_stops: Dict[str, Dict[str, Any]] = {}

    def setup_trailing_stop(
        self,
        pair: str,
        entry_price: float,
        action: str,
        initial_stop_loss: float,
        trailing_distance_pct: Optional[float] = None,
        activation_profit_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Setup trailing stop for a position.

        Args:
            pair: Trading pair
            entry_price: Position entry price
            action: Position action ("buy" or "sell")
            initial_stop_loss: Initial stop-loss price
            trailing_distance_pct: Custom trailing distance (overrides default)
            activation_profit_pct: Custom activation threshold (overrides default)

        Returns:
            Trailing stop configuration
        """
        trailing_dist = trailing_distance_pct or self.trailing_distance_pct
        activation_profit = activation_profit_pct or self.activation_profit_pct

        # Calculate activation price
        if action == "buy":
            activation_price = entry_price * (1 + activation_profit)
        else:  # sell
            activation_price = entry_price * (1 - activation_profit)

        self.active_stops[pair] = {
            "pair": pair,
            "entry_price": entry_price,
            "action": action,
            "current_stop": initial_stop_loss,
            "highest_price": entry_price if action == "buy" else None,
            "lowest_price": entry_price if action == "sell" else None,
            "trailing_distance_pct": trailing_dist,
            "activation_price": activation_price,
            "activated": False,
            "updates": 0,
            "created_at": datetime.utcnow().isoformat(),
            "last_update": datetime.utcnow().isoformat(),
        }

        return {
            "enabled": True,
            "pair": pair,
            "initial_stop": initial_stop_loss,
            "trailing_distance": trailing_dist * 100,  # Convert to percentage
            "activation_price": round(activation_price, 2),
            "activation_profit": activation_profit * 100,
        }

    def update_trailing_stop(
        self,
        pair: str,
        current_price: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Update trailing stop based on current price.

        Args:
            pair: Trading pair
            current_price: Current market price

        Returns:
            Update result if stop was adjusted, None otherwise
        """
        if pair not in self.active_stops:
            return None

        stop_config = self.active_stops[pair]
        action = stop_config["action"]

        # Check if trailing should be activated
        if not stop_config["activated"]:
            activation_price = stop_config["activation_price"]

            if action == "buy" and current_price >= activation_price:
                stop_config["activated"] = True
            elif action == "sell" and current_price <= activation_price:
                stop_config["activated"] = True

            if not stop_config["activated"]:
                # Not activated yet
                return None

        # Update highest/lowest price
        if action == "buy":
            if stop_config["highest_price"] is None or current_price > stop_config["highest_price"]:
                stop_config["highest_price"] = current_price

                # Calculate new trailing stop
                new_stop = current_price * (1 - stop_config["trailing_distance_pct"])

                # Only update if new stop is higher (tighter)
                if new_stop > stop_config["current_stop"]:
                    old_stop = stop_config["current_stop"]
                    stop_config["current_stop"] = new_stop
                    stop_config["updates"] += 1
                    stop_config["last_update"] = datetime.utcnow().isoformat()

                    return {
                        "updated": True,
                        "pair": pair,
                        "old_stop": round(old_stop, 2),
                        "new_stop": round(new_stop, 2),
                        "current_price": round(current_price, 2),
                        "highest_price": round(stop_config["highest_price"], 2),
                        "updates": stop_config["updates"],
                    }

        else:  # sell (short position)
            if stop_config["lowest_price"] is None or current_price < stop_config["lowest_price"]:
                stop_config["lowest_price"] = current_price

                # Calculate new trailing stop
                new_stop = current_price * (1 + stop_config["trailing_distance_pct"])

                # Only update if new stop is lower (tighter)
                if new_stop < stop_config["current_stop"]:
                    old_stop = stop_config["current_stop"]
                    stop_config["current_stop"] = new_stop
                    stop_config["updates"] += 1
                    stop_config["last_update"] = datetime.utcnow().isoformat()

                    return {
                        "updated": True,
                        "pair": pair,
                        "old_stop": round(old_stop, 2),
                        "new_stop": round(new_stop, 2),
                        "current_price": round(current_price, 2),
                        "lowest_price": round(stop_config["lowest_price"], 2),
                        "updates": stop_config["updates"],
                    }

        return None

    def check_stop_hit(
        self,
        pair: str,
        current_price: float,
    ) -> bool:
        """
        Check if trailing stop has been hit.

        Args:
            pair: Trading pair
            current_price: Current market price

        Returns:
            True if stop-loss has been hit
        """
        if pair not in self.active_stops:
            return False

        stop_config = self.active_stops[pair]
        action = stop_config["action"]
        current_stop = stop_config["current_stop"]

        if action == "buy":
            # Stop hit if price falls below stop
            return current_price <= current_stop
        else:  # sell
            # Stop hit if price rises above stop
            return current_price >= current_stop

    def get_current_stop(self, pair: str) -> Optional[float]:
        """
        Get current stop-loss price for a pair.

        Args:
            pair: Trading pair

        Returns:
            Current stop-loss price or None
        """
        if pair not in self.active_stops:
            return None

        return self.active_stops[pair]["current_stop"]

    def get_status(self, pair: str) -> Optional[Dict[str, Any]]:
        """
        Get trailing stop status.

        Args:
            pair: Trading pair

        Returns:
            Complete status or None if not found
        """
        if pair not in self.active_stops:
            return None

        config = self.active_stops[pair]

        return {
            "pair": pair,
            "enabled": True,
            "activated": config["activated"],
            "current_stop": round(config["current_stop"], 2),
            "entry_price": round(config["entry_price"], 2),
            "activation_price": round(config["activation_price"], 2),
            "highest_price": round(config["highest_price"], 2) if config["highest_price"] else None,
            "lowest_price": round(config["lowest_price"], 2) if config["lowest_price"] else None,
            "trailing_distance_pct": config["trailing_distance_pct"] * 100,
            "updates": config["updates"],
            "last_update": config["last_update"],
        }

    def clear_stop(self, pair: str):
        """
        Clear trailing stop for a pair.

        Args:
            pair: Trading pair
        """
        if pair in self.active_stops:
            del self.active_stops[pair]

    def is_enabled(self, pair: str) -> bool:
        """
        Check if trailing stop is enabled for pair.

        Args:
            pair: Trading pair

        Returns:
            True if trailing stop is active
        """
        return pair in self.active_stops
