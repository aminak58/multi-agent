"""Celery application configuration."""

from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "orchestrator",
    broker=settings.broker_url,
    backend=settings.result_backend_url,
    include=[
        "app.tasks.signal_tasks",
        "app.tasks.risk_tasks",
        "app.tasks.position_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={"master_name": "mymaster"},

    # Retry policy
    task_default_retry_delay=settings.retry_backoff,
    task_max_retries=settings.max_retries,

    # Routing
    task_routes={
        "app.tasks.signal_tasks.*": {"queue": settings.signal_queue},
        "app.tasks.risk_tasks.*": {"queue": settings.risk_queue},
        "app.tasks.position_tasks.*": {"queue": settings.position_queue},
    },

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task queues configuration
celery_app.conf.task_queues = {
    settings.signal_queue: {
        "exchange": settings.signal_queue,
        "routing_key": "signal",
    },
    settings.risk_queue: {
        "exchange": settings.risk_queue,
        "routing_key": "risk",
    },
    settings.position_queue: {
        "exchange": settings.position_queue,
        "routing_key": "position",
    },
}

if __name__ == "__main__":
    celery_app.start()
