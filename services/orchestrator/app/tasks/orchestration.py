"""Main orchestration tasks."""

from typing import Dict, Any
from celery import chain
from app.celery_app import celery_app
from app.tasks.signal_tasks import generate_signal
from app.tasks.risk_tasks import validate_and_size
from app.tasks.position_tasks import execute_order


@celery_app.task(name="process_candle_update", bind=True, max_retries=3)
def process_candle_update(self, candle_data: Dict[str, Any]):
    """
    Process candle update through multi-agent pipeline.

    Flow:
    1. SignalAgent: Generate trading signal
    2. RiskAgent: Validate and size position
    3. PositionManager: Execute order

    Args:
        candle_data: Candle update data

    Returns:
        Final execution result
    """
    try:
        # Create task chain
        workflow = chain(
            generate_signal.s(candle_data),
            validate_and_size.s(candle_data),
            execute_order.s(candle_data),
        )

        # Execute workflow
        result = workflow.apply_async()

        return {
            "status": "success",
            "workflow_id": str(result.id),
            "pair": candle_data.get("pair"),
        }

    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60)
