"""Tests for Redis cache utilities."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.utils.cache import RedisCache


@pytest.mark.asyncio
class TestRedisCache:
    """Test RedisCache functionality."""

    @pytest.fixture
    async def cache(self):
        """Create cache instance with mocked redis."""
        cache = RedisCache()
        mock_redis = AsyncMock()
        cache._redis = mock_redis
        return cache

    async def test_connect_success(self):
        """Test successful Redis connection."""
        cache = RedisCache()

        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            mock_from_url.return_value = mock_redis

            await cache.connect()

            assert cache._redis is not None
            mock_redis.ping.assert_called_once()

    async def test_connect_failure(self):
        """Test Redis connection failure."""
        cache = RedisCache()

        with patch('redis.asyncio.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping.side_effect = Exception("Connection failed")
            mock_from_url.return_value = mock_redis

            with pytest.raises(Exception) as exc_info:
                await cache.connect()

            assert "Connection failed" in str(exc_info.value)

    async def test_disconnect(self, cache):
        """Test Redis disconnection."""
        await cache.disconnect()
        cache._redis.close.assert_called_once()

    async def test_get_hit(self, cache):
        """Test cache get with hit."""
        test_data = {"key": "value", "number": 42}
        cache._redis.get.return_value = json.dumps(test_data)

        result = await cache.get("test_key")

        assert result == test_data
        cache._redis.get.assert_called_once_with("test_key")

    async def test_get_miss(self, cache):
        """Test cache get with miss."""
        cache._redis.get.return_value = None

        result = await cache.get("nonexistent_key")

        assert result is None
        cache._redis.get.assert_called_once_with("nonexistent_key")

    async def test_get_error(self, cache):
        """Test cache get with error."""
        cache._redis.get.side_effect = Exception("Redis error")

        result = await cache.get("error_key")

        assert result is None

    async def test_set_success(self, cache):
        """Test cache set success."""
        test_data = {"key": "value"}

        await cache.set("test_key", test_data, ttl=300)

        cache._redis.setex.assert_called_once_with(
            "test_key", 300, json.dumps(test_data)
        )

    async def test_set_with_default_ttl(self, cache):
        """Test cache set with default TTL."""
        test_data = {"key": "value"}

        with patch('app.utils.cache.settings') as mock_settings:
            mock_settings.redis_ttl = 600
            await cache.set("test_key", test_data)

        cache._redis.setex.assert_called_once()

    async def test_set_error(self, cache):
        """Test cache set with error."""
        cache._redis.setex.side_effect = Exception("Redis error")

        # Should not raise, just log
        await cache.set("error_key", {"data": "value"})

    async def test_delete_success(self, cache):
        """Test cache delete."""
        await cache.delete("test_key")

        cache._redis.delete.assert_called_once_with("test_key")

    async def test_delete_error(self, cache):
        """Test cache delete with error."""
        cache._redis.delete.side_effect = Exception("Redis error")

        # Should not raise, just log
        await cache.delete("error_key")

    async def test_exists_true(self, cache):
        """Test cache exists returns True."""
        cache._redis.exists.return_value = 1

        result = await cache.exists("existing_key")

        assert result is True
        cache._redis.exists.assert_called_once_with("existing_key")

    async def test_exists_false(self, cache):
        """Test cache exists returns False."""
        cache._redis.exists.return_value = 0

        result = await cache.exists("nonexistent_key")

        assert result is False

    async def test_exists_error(self, cache):
        """Test cache exists with error."""
        cache._redis.exists.side_effect = Exception("Redis error")

        result = await cache.exists("error_key")

        assert result is False

    async def test_complex_data_serialization(self, cache):
        """Test caching complex nested data."""
        complex_data = {
            "candles": [
                {"timestamp": 1700000000, "open": 50000.0, "close": 50500.0},
                {"timestamp": 1700000900, "open": 50500.0, "close": 51000.0},
            ],
            "metadata": {
                "pair": "BTC/USDT",
                "timeframe": "15m",
                "count": 2,
            },
        }

        cache._redis.get.return_value = json.dumps(complex_data)

        result = await cache.get("complex_key")

        assert result == complex_data
        assert result["candles"][0]["timestamp"] == 1700000000
        assert result["metadata"]["pair"] == "BTC/USDT"
