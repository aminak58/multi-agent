"""MCP Gateway - Main FastAPI application."""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.utils.logger import setup_logger, log_response
from app.utils.cache import cache
from app.clients.freqtrade import freqtrade_client
from app.middleware.rate_limit import setup_rate_limiting, limiter
from app.models.schemas import ErrorResponse

# Import routers
from app.routes import health, candles, positions, orders

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for application startup and shutdown.

    Handles initialization of Redis, Freqtrade client, and other resources.
    """
    # Startup
    logger.info(
        f"Starting {settings.app_name} v{settings.version}",
        extra={"environment": settings.environment},
    )

    try:
        # Connect to Redis
        await cache.connect()

        # Connect to Freqtrade
        await freqtrade_client.connect()

        logger.info("All services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", extra={"error": str(e)})
        raise

    yield

    # Shutdown
    logger.info("Shutting down application")

    try:
        await cache.disconnect()
        await freqtrade_client.disconnect()
        logger.info("All services shut down gracefully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", extra={"error": str(e)})


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Market Data & Order Execution Gateway for Multi-Agent Trading Bot",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Setup rate limiting
setup_rate_limiting(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests and responses with timing.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response
    """
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    log_response(
        logger,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.

    Args:
        request: Request that caused the exception
        exc: Exception instance

    Returns:
        JSON error response
    """
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
        },
        exc_info=True,
    )

    error_response = ErrorResponse(
        error="Internal server error",
        detail=str(exc) if settings.debug else "An unexpected error occurred",
        timestamp=datetime.utcnow(),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict(),
    )


# Include routers
app.include_router(health.router)
app.include_router(candles.router)
app.include_router(positions.router)
app.include_router(orders.router)


# Prometheus metrics
if settings.enable_metrics:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
    logger.info("Prometheus metrics enabled at /metrics")


@app.get("/")
@limiter.exempt
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
    }


if __name__ == "__main__":
    import uvicorn
    from datetime import datetime

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
