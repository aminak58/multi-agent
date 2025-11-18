"""JWT authentication."""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )

    logger.debug("JWT token created", extra={"expires_at": expire.isoformat()})

    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        logger.debug("JWT token verified")
        return payload
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """
    Dependency to get current authenticated user.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User payload from JWT

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
        )

    return payload


# Optional user authentication - commented out due to FastAPI version compatibility
# async def get_optional_user(
#     credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
# ) -> Optional[dict]:
#     """
#     Optional authentication dependency.
#
#     Args:
#         credentials: HTTP Bearer credentials (optional)
#
#     Returns:
#         User payload or None
#     """
#     if credentials is None:
#         return None
#
#     try:
#         return await get_current_user(credentials)
#     except HTTPException:
#         return None
