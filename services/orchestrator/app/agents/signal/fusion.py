"""Decision fusion logic for combining multiple signals."""

from typing import Dict, Any, List
from enum import Enum


class FusionMethod(str, Enum):
    """Fusion methods for combining signals."""

    WEIGHTED_AVERAGE = "weighted_average"
    MAJORITY_VOTE = "majority_vote"
    CONSERVATIVE = "conservative"  # Only act if all agree
    AGGRESSIVE = "aggressive"  # Act on strongest signal


class SignalFusion:
    """
    Combines multiple indicator signals into a single decision.

    Supports different fusion methods and configurable weights.
    """

    def __init__(
        self,
        method: FusionMethod = FusionMethod.WEIGHTED_AVERAGE,
        weights: Dict[str, float] = None,
        min_agreement: float = 0.6,  # For majority vote
    ):
        """
        Initialize signal fusion.

        Args:
            method: Fusion method to use
            weights: Indicator weights (default: equal weights)
            min_agreement: Minimum agreement threshold for majority vote (default: 0.6)
        """
        self.method = method
        self.weights = weights or {}
        self.min_agreement = min_agreement

        # Default weights if not provided
        if not self.weights:
            self.weights = {
                "ema": 0.25,
                "rsi": 0.25,
                "macd": 0.25,
                "support_resistance": 0.25,
            }

    def normalize_weights(self) -> Dict[str, float]:
        """
        Normalize weights to sum to 1.0.

        Returns:
            Normalized weights dictionary
        """
        total = sum(self.weights.values())
        if total == 0:
            return self.weights

        return {k: v / total for k, v in self.weights.items()}

    def action_to_score(self, action: str) -> float:
        """
        Convert action string to numerical score.

        Args:
            action: Action string (buy/sell/hold)

        Returns:
            Numerical score: +1 (buy), -1 (sell), 0 (hold)
        """
        action_map = {"buy": 1.0, "sell": -1.0, "hold": 0.0}
        return action_map.get(action.lower(), 0.0)

    def score_to_action(self, score: float, threshold: float = 0.1) -> str:
        """
        Convert numerical score to action string.

        Args:
            score: Numerical score
            threshold: Threshold for buy/sell decision (default: 0.1)

        Returns:
            Action string
        """
        if score > threshold:
            return "buy"
        elif score < -threshold:
            return "sell"
        else:
            return "hold"

    def weighted_average_fusion(self, signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fuse signals using weighted average.

        Args:
            signals: Dictionary of indicator signals

        Returns:
            Fused decision
        """
        weights = self.normalize_weights()

        # Calculate weighted score
        total_score = 0.0
        total_strength = 0.0
        reasons = []

        for indicator_name, signal in signals.items():
            weight = weights.get(indicator_name, 0.0)
            action_score = self.action_to_score(signal["action"])
            strength = signal["strength"]

            # Weighted contribution
            total_score += action_score * strength * weight
            total_strength += strength * weight

            # Collect reasons from significant signals
            if strength > 0.3:  # Only include meaningful signals
                reasons.append(f"{indicator_name}: {signal['reason']}")

        # Normalize strength
        avg_strength = total_strength / len(signals) if signals else 0.0

        # Determine final action
        final_action = self.score_to_action(total_score)

        return {
            "action": final_action,
            "confidence": round(avg_strength, 3),
            "score": round(total_score, 3),
            "reasoning": " | ".join(reasons) if reasons else "No clear signals",
            "method": "weighted_average",
        }

    def majority_vote_fusion(self, signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fuse signals using majority voting.

        Args:
            signals: Dictionary of indicator signals

        Returns:
            Fused decision
        """
        if not signals:
            return {
                "action": "hold",
                "confidence": 0.0,
                "reasoning": "No signals available",
                "method": "majority_vote",
            }

        # Count votes
        votes = {"buy": 0, "sell": 0, "hold": 0}
        weighted_votes = {"buy": 0.0, "sell": 0.0, "hold": 0.0}
        reasons = []

        for indicator_name, signal in signals.items():
            action = signal["action"]
            strength = signal["strength"]

            votes[action] += 1
            weighted_votes[action] += strength

            if strength > 0.3:
                reasons.append(f"{indicator_name}: {signal['reason']}")

        # Determine winner
        total_votes = sum(votes.values())
        max_votes = max(votes.values())
        winner = max(votes, key=votes.get)

        # Check if minimum agreement is met
        agreement = max_votes / total_votes if total_votes > 0 else 0.0

        if agreement < self.min_agreement:
            winner = "hold"
            reasons = [f"No consensus (agreement: {agreement:.1%})"]

        # Calculate confidence based on weighted votes
        confidence = weighted_votes[winner] / len(signals) if signals else 0.0

        return {
            "action": winner,
            "confidence": round(confidence, 3),
            "agreement": round(agreement, 3),
            "votes": votes,
            "reasoning": " | ".join(reasons) if reasons else "Insufficient agreement",
            "method": "majority_vote",
        }

    def conservative_fusion(self, signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Conservative fusion - only act if all indicators agree.

        Args:
            signals: Dictionary of indicator signals

        Returns:
            Fused decision
        """
        if not signals:
            return {
                "action": "hold",
                "confidence": 0.0,
                "reasoning": "No signals available",
                "method": "conservative",
            }

        # Get all actions
        actions = [signal["action"] for signal in signals.values()]
        strengths = [signal["strength"] for signal in signals.values()]

        # Check if all agree
        if len(set(actions)) == 1 and actions[0] != "hold":
            # All indicators agree on buy or sell
            avg_strength = sum(strengths) / len(strengths)
            reasons = [f"{name}: {signal['reason']}" for name, signal in signals.items()]

            return {
                "action": actions[0],
                "confidence": round(avg_strength, 3),
                "reasoning": " | ".join(reasons),
                "method": "conservative",
                "full_agreement": True,
            }
        else:
            # No full agreement - stay in hold
            return {
                "action": "hold",
                "confidence": 0.0,
                "reasoning": "No full agreement among indicators",
                "method": "conservative",
                "full_agreement": False,
            }

    def aggressive_fusion(self, signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggressive fusion - act on strongest signal.

        Args:
            signals: Dictionary of indicator signals

        Returns:
            Fused decision
        """
        if not signals:
            return {
                "action": "hold",
                "confidence": 0.0,
                "reasoning": "No signals available",
                "method": "aggressive",
            }

        # Find strongest signal
        strongest = max(signals.items(), key=lambda x: x[1]["strength"])
        indicator_name, signal = strongest

        return {
            "action": signal["action"],
            "confidence": round(signal["strength"], 3),
            "reasoning": f"Strongest signal from {indicator_name}: {signal['reason']}",
            "method": "aggressive",
            "source": indicator_name,
        }

    def fuse(self, signals: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fuse multiple signals into single decision.

        Args:
            signals: Dictionary of indicator signals
                    Format: {indicator_name: {action, strength, reason, metadata}}

        Returns:
            Fused decision with action, confidence, reasoning
        """
        if not signals:
            return {
                "action": "hold",
                "confidence": 0.0,
                "reasoning": "No signals available",
                "indicators": {},
            }

        # Apply fusion method
        if self.method == FusionMethod.WEIGHTED_AVERAGE:
            result = self.weighted_average_fusion(signals)
        elif self.method == FusionMethod.MAJORITY_VOTE:
            result = self.majority_vote_fusion(signals)
        elif self.method == FusionMethod.CONSERVATIVE:
            result = self.conservative_fusion(signals)
        elif self.method == FusionMethod.AGGRESSIVE:
            result = self.aggressive_fusion(signals)
        else:
            result = self.weighted_average_fusion(signals)  # Default

        # Add indicator details
        result["indicators"] = {
            name: {
                "action": signal["action"],
                "strength": signal["strength"],
                "reason": signal["reason"],
            }
            for name, signal in signals.items()
        }

        return result
