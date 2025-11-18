"""Orders execution endpoints."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import (
    OrderRequest,
    OrderResponse,
    DryRunResponse,
    OrderStatus,
)
from app.clients.freqtrade import freqtrade_client
from app.auth.jwt import get_current_user
from app.auth.hmac import verify_hmac_signature
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["orders"])


@router.post("/orders/dry-run", response_model=DryRunResponse)
async def dry_run_order(
    order: OrderRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Validate order without execution (dry-run).

    This endpoint validates order parameters and checks if the order
    can be executed, without actually placing it.

    Args:
        order: Order request details
        current_user: Authenticated user (from JWT)

    Returns:
        DryRunResponse with validation result
    """
    logger.info(
        "Dry-run order requested",
        extra={
            "request_id": order.request_id,
            "agent": order.agent,
            "pair": order.pair,
            "side": order.side,
            "amount": order.amount,
            "user": current_user.get("sub"),
        },
    )

    # Validate with Freqtrade
    result = await freqtrade_client.dry_run_order(
        order.pair, order.side.value, order.amount
    )

    return DryRunResponse(**result)


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order: OrderRequest,
    current_user: dict = Depends(get_current_user),
    signature_valid: bool = Depends(verify_hmac_signature),
):
    """
    Create and execute a new order.

    This endpoint places a real order on Freqtrade. It requires both
    JWT authentication and HMAC signature verification.

    **Security**: This endpoint requires HMAC signature in X-Signature header.

    Args:
        order: Order request details
        current_user: Authenticated user (from JWT)
        signature_valid: HMAC signature verification result

    Returns:
        OrderResponse with order execution details

    Raises:
        HTTPException: If order execution fails
    """
    logger.info(
        "Order creation requested",
        extra={
            "request_id": order.request_id,
            "agent": order.agent,
            "pair": order.pair,
            "side": order.side,
            "amount": order.amount,
            "user": current_user.get("sub"),
        },
    )

    try:
        # Execute order via Freqtrade
        result = await freqtrade_client.create_order(
            pair=order.pair,
            side=order.side.value,
            amount=order.amount,
            order_type=order.order_type.value,
            price=order.price,
        )

        # Parse response
        order_response = OrderResponse(
            order_id=result.get("order_id", "unknown"),
            request_id=order.request_id,
            status=OrderStatus.SUBMITTED,
            pair=order.pair,
            side=order.side,
            amount=order.amount,
            filled_amount=0.0,  # Will be updated by Freqtrade
            price=order.price,
            average_price=None,
            timestamp=datetime.utcnow(),
            message=result.get("status", "Order submitted"),
        )

        logger.info(
            "Order created successfully",
            extra={
                "order_id": order_response.order_id,
                "request_id": order.request_id,
            },
        )

        return order_response

    except Exception as e:
        logger.error(
            f"Order creation failed: {e}",
            extra={"request_id": order.request_id, "error": str(e)},
        )
        raise HTTPException(
            status_code=500, detail=f"Order execution failed: {str(e)}"
        )
