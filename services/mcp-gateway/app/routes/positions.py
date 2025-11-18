"""Positions endpoint."""

from fastapi import APIRouter, Depends

from app.models.schemas import PositionsResponse
from app.clients.freqtrade import freqtrade_client
from app.auth.jwt import get_current_user
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["positions"])


@router.get("/positions/open", response_model=PositionsResponse)
async def get_open_positions(
    current_user: dict = Depends(get_current_user),
):
    """
    Get all currently open positions.

    Retrieves active trades from Freqtrade including entry price,
    current price, and unrealized PnL.

    Args:
        current_user: Authenticated user (from JWT)

    Returns:
        PositionsResponse with list of open positions
    """
    logger.info(
        "Open positions requested", extra={"user": current_user.get("sub")}
    )

    # Fetch from Freqtrade
    positions = await freqtrade_client.get_open_positions()

    logger.info(
        f"Retrieved {len(positions)} open positions",
        extra={"count": len(positions)},
    )

    return PositionsResponse(positions=positions, total_count=len(positions))
