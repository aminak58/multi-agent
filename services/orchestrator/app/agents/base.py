"""Base agent class for all trading agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BaseAgent(ABC):
    """Abstract base class for all trading agents."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize base agent.

        Args:
            config: Agent configuration dictionary
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.created_at = datetime.utcnow()

    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return decision.

        Args:
            data: Input data for processing

        Returns:
            Decision dictionary
        """
        pass

    def validate_input(self, data: Dict[str, Any], required_fields: list) -> bool:
        """
        Validate input data has required fields.

        Args:
            data: Input data
            required_fields: List of required field names

        Returns:
            True if valid, False otherwise
        """
        return all(field in data for field in required_fields)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)
