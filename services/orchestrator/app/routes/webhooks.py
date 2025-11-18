"""Webhook endpoints for receiving candle updates."""

from fastapi import APIRouter, BackgroundTasks
from app.models.schemas import CandleUpdate, WebhookResponse
from app.tasks.orchestration import process_candle_update

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/candle", response_model=WebhookResponse)
async def receive_candle_update(
    candle: CandleUpdate,
    background_tasks: BackgroundTasks,
):
    """
    Receive candle update webhook.

    This triggers the multi-agent decision flow:
    1. Signal Agent → generates trading signal
    2. Risk Agent → validates and sizes position
    3. Position Manager → executes order

    Args:
        candle: Candle update data
        background_tasks: FastAPI background tasks

    Returns:
        Webhook acknowledgment
    """
    # Trigger async processing
    task = process_candle_update.delay(candle.dict())

    return WebhookResponse(
        status="accepted",
        message=f"Candle update for {candle.pair} queued for processing",
        task_id=str(task.id),
    )
