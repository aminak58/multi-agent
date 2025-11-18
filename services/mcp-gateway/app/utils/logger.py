"""Logging configuration."""

import logging
import sys
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from app.config import settings


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with JSON formatting.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    handler = logging.StreamHandler(sys.stdout)

    if settings.log_format == "json":
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def log_request(logger: logging.Logger, method: str, path: str, extra: Dict[str, Any] = None):
    """
    Log HTTP request.

    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        extra: Additional fields
    """
    log_data = {"method": method, "path": path}
    if extra:
        log_data.update(extra)

    logger.info("HTTP request", extra=log_data)


def log_response(
    logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float
):
    """
    Log HTTP response.

    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
    """
    logger.info(
        "HTTP response",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        },
    )
