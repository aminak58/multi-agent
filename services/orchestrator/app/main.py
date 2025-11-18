"""Orchestrator - Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.routes import webhooks, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for application startup and shutdown."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.version}")

    yield

    # Shutdown
    print("Shutting down Orchestrator")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Event-driven coordinator for Multi-Agent Trading System",
    docs_url="/docs" if settings.debug else None,
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router)
app.include_router(webhooks.router)

# Prometheus metrics
if settings.enable_metrics:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
