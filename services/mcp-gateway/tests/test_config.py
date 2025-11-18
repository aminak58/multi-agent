"""Tests for configuration module."""

import pytest
from unittest.mock import patch
import os

from app.config import Settings


class TestSettings:
    """Test Settings configuration."""

    def test_default_settings(self):
        """Test default settings values."""
        with patch.dict(os.environ, {
            "JWT_SECRET": "test-secret",
            "HMAC_SECRET": "test-hmac",
            "REDIS_PASSWORD": "test-redis",
            "POSTGRES_PASSWORD": "test-postgres",
        }):
            settings = Settings()

            assert settings.app_name == "MCP Gateway"
            assert settings.version == "0.1.0"
            assert settings.environment == "development"
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000
            assert settings.jwt_algorithm == "HS256"
            assert settings.rate_limit_per_minute == 60

    def test_database_url_generation(self):
        """Test database URL is generated correctly."""
        with patch.dict(os.environ, {
            "JWT_SECRET": "test-secret",
            "HMAC_SECRET": "test-hmac",
            "REDIS_PASSWORD": "test-redis",
            "POSTGRES_USER": "testuser",
            "POSTGRES_PASSWORD": "testpass",
            "POSTGRES_HOST": "testhost",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "testdb",
        }):
            settings = Settings()

            expected_url = "postgresql+asyncpg://testuser:testpass@testhost:5433/testdb"
            assert settings.database_url == expected_url

    def test_redis_url_generation(self):
        """Test Redis URL is generated correctly."""
        with patch.dict(os.environ, {
            "JWT_SECRET": "test-secret",
            "HMAC_SECRET": "test-hmac",
            "REDIS_HOST": "testredis",
            "REDIS_PORT": "6380",
            "REDIS_PASSWORD": "testredispass",
            "REDIS_DB": "2",
            "POSTGRES_PASSWORD": "test",
        }):
            settings = Settings()

            expected_url = "redis://:testredispass@testredis:6380/2"
            assert settings.redis_url == expected_url

    def test_redis_url_without_password(self):
        """Test Redis URL generation without password."""
        with patch.dict(os.environ, {
            "JWT_SECRET": "test-secret",
            "HMAC_SECRET": "test-hmac",
            "REDIS_HOST": "testredis",
            "REDIS_PORT": "6380",
            "REDIS_PASSWORD": "",
            "REDIS_DB": "2",
            "POSTGRES_PASSWORD": "test",
        }):
            settings = Settings()

            expected_url = "redis://testredis:6380/2"
            assert settings.redis_url == expected_url

    def test_custom_environment_settings(self):
        """Test custom environment settings."""
        with patch.dict(os.environ, {
            "JWT_SECRET": "prod-secret",
            "HMAC_SECRET": "prod-hmac",
            "REDIS_PASSWORD": "prod-redis",
            "POSTGRES_PASSWORD": "prod-postgres",
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "WARNING",
            "RATE_LIMIT_PER_MINUTE": "120",
        }):
            settings = Settings()

            assert settings.environment == "production"
            assert settings.debug is False
            assert settings.log_level == "WARNING"
            assert settings.rate_limit_per_minute == 120
