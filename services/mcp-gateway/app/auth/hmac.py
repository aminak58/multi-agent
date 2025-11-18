"""HMAC signature validation for webhook security."""

import hmac
import hashlib
from typing import Optional

from fastapi import HTTPException, Header

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def compute_signature(payload: bytes) -> str:
    """
    Compute HMAC-SHA256 signature.

    Args:
        payload: Request body bytes

    Returns:
        Hex-encoded signature
    """
    signature = hmac.new(
        settings.hmac_secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    return signature


def verify_signature(payload: bytes, received_signature: str) -> bool:
    """
    Verify HMAC signature.

    Args:
        payload: Request body bytes
        received_signature: Signature from request header

    Returns:
        True if signature is valid
    """
    expected_signature = compute_signature(payload)

    # Constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(expected_signature, received_signature)

    if not is_valid:
        logger.warning(
            "Invalid HMAC signature",
            extra={
                "expected": expected_signature[:10] + "...",
                "received": received_signature[:10] + "...",
            },
        )

    return is_valid


async def verify_hmac_signature(
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    body: bytes = b"",
) -> bool:
    """
    FastAPI dependency to verify HMAC signature.

    Args:
        x_signature: HMAC signature from header
        body: Request body

    Returns:
        True if signature is valid

    Raises:
        HTTPException: If signature is missing or invalid
    """
    if not x_signature:
        logger.warning("Missing HMAC signature")
        raise HTTPException(status_code=401, detail="Missing signature")

    if not verify_signature(body, x_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    logger.debug("HMAC signature verified")
    return True
