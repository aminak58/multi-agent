"""Health check endpoint."""

from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.version,
    )
