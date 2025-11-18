"""Candles data endpoint."""

from typing import Optional
from fastapi import APIRouter, Query, Depends

from app.models.schemas import CandlesResponse
from app.clients.freqtrade import freqtrade_client
from app.utils.cache import cache
from app.auth.jwt import get_current_user
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["candles"])


@router.get("/candles", response_model=CandlesResponse)
async def get_candles(
    pair: str = Query(..., description="Trading pair (e.g., BTC/USDT)"),
    timeframe: str = Query(..., description="Timeframe (e.g., 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(500, ge=1, le=1000, description="Number of candles to retrieve"),
    use_cache: bool = Query(True, description="Use cached data if available"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get OHLCV candle data for a trading pair.

    This endpoint retrieves historical candle data from Freqtrade.
    Results are cached in Redis for improved performance.

    Args:
        pair: Trading pair symbol
        timeframe: Candle timeframe
        limit: Maximum number of candles to return
        use_cache: Whether to use cached data
        current_user: Authenticated user (from JWT)

    Returns:
        CandlesResponse with list of candles
    """
    logger.info(
        "Candles requested",
        extra={
            "pair": pair,
            "timeframe": timeframe,
            "limit": limit,
            "user": current_user.get("sub"),
        },
    )

    # Try cache first
    cache_key = f"candles:{pair}:{timeframe}:{limit}"
    if use_cache:
        cached_data = await cache.get(cache_key)
        if cached_data:
            logger.debug("Returning cached candles", extra={"cache_key": cache_key})
            return CandlesResponse(**cached_data)

    # Fetch from Freqtrade
    candles = await freqtrade_client.get_candles(pair, timeframe, limit)

    response = CandlesResponse(
        pair=pair, timeframe=timeframe, candles=candles, count=len(candles)
    )

    # Cache the response
    await cache.set(cache_key, response.dict(), ttl=60)  # Cache for 1 minute

    return response
