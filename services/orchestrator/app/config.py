"""Configuration settings for Orchestrator."""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Orchestrator"
    version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8001

    # MCP Gateway
    mcp_gateway_url: str = "http://mcp-gateway:8000/api/v1"
    mcp_jwt_secret: str  # Same as MCP Gateway

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str
    redis_db: int = 1  # Different from MCP Gateway

    # RabbitMQ
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "bot_user"
    rabbitmq_password: str
    rabbitmq_vhost: str = "/trading"

    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    celery_task_default_queue: str = "orchestrator_queue"

    # Task Queues
    signal_queue: str = "signal_queue"
    risk_queue: str = "risk_queue"
    position_queue: str = "position_queue"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Monitoring
    enable_metrics: bool = True

    # Retry Configuration
    max_retries: int = 3
    retry_backoff: int = 2  # seconds

    # Circuit Breaker
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60  # seconds

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def broker_url(self) -> str:
        """Get RabbitMQ broker URL for Celery."""
        if self.celery_broker_url:
            return self.celery_broker_url
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
        )

    @property
    def result_backend_url(self) -> str:
        """Get result backend URL for Celery."""
        if self.celery_result_backend:
            return self.celery_result_backend
        return self.redis_url

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
