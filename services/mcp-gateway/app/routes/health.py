"""Health check endpoint."""

from datetime import datetime
from fastapi import APIRouter, Depends

from app.models.schemas import HealthResponse
from app.config import settings
from app.utils.cache import cache
from app.clients.freqtrade import freqtrade_client
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns comprehensive health status of the gateway and its dependencies.
    """
    logger.debug("Health check requested")

    services = {}

    # Check Redis
    try:
        await cache._redis.ping()
        services["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services["redis"] = f"unhealthy: {str(e)}"

    # Check Freqtrade
    freqtrade_health = await freqtrade_client.get_health()
    services["freqtrade"] = freqtrade_health["status"]

    # Overall status
    overall_status = (
        "healthy"
        if all(s == "healthy" for s in services.values())
        else "degraded"
    )

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.version,
        services=services,
    )
