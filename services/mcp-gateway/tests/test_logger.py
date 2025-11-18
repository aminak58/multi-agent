"""Tests for logging utilities."""

import pytest
import logging
from unittest.mock import patch, MagicMock

from app.utils.logger import setup_logger, log_request, log_response


class TestLogger:
    """Test logging utilities."""

    def test_setup_logger_default(self):
        """Test logger setup with default settings."""
        logger = setup_logger("test_logger")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"
        assert len(logger.handlers) > 0

    def test_setup_logger_level(self):
        """Test logger respects log level."""
        with patch('app.utils.logger.settings') as mock_settings:
            mock_settings.log_level = "DEBUG"
            logger = setup_logger("test_logger_debug")

            assert logger.level == logging.DEBUG

    def test_log_request(self):
        """Test request logging."""
        logger = MagicMock()

        log_request(logger, "GET", "/api/v1/candles", {"user": "test"})

        logger.info.assert_called_once()
        call_args = logger.info.call_args
        assert call_args[0][0] == "HTTP request"
        assert call_args[1]["extra"]["method"] == "GET"
        assert call_args[1]["extra"]["path"] == "/api/v1/candles"

    def test_log_response(self):
        """Test response logging."""
        logger = MagicMock()

        log_response(logger, "GET", "/api/v1/health", 200, 45.5)

        logger.info.assert_called_once()
        call_args = logger.info.call_args
        assert call_args[0][0] == "HTTP response"
        assert call_args[1]["extra"]["status_code"] == 200
        assert call_args[1]["extra"]["duration_ms"] == 45.5

    def test_logger_json_format(self):
        """Test JSON logging format."""
        with patch('app.utils.logger.settings') as mock_settings:
            mock_settings.log_level = "INFO"
            mock_settings.log_format = "json"

            logger = setup_logger("test_json_logger")

            # Check handler formatter
            handler = logger.handlers[0]
            # JSON formatter should be pythonjsonlogger.JsonFormatter
            assert hasattr(handler.formatter, '_fmt')

    def test_logger_text_format(self):
        """Test text logging format."""
        with patch('app.utils.logger.settings') as mock_settings:
            mock_settings.log_level = "INFO"
            mock_settings.log_format = "text"

            logger = setup_logger("test_text_logger")

            # Check handler formatter
            handler = logger.handlers[0]
            assert isinstance(handler.formatter, logging.Formatter)
