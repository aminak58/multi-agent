"""Redis caching utilities."""

import json
from typing import Any, Optional
import redis.asyncio as aioredis

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RedisCache:
    """Redis cache manager."""

    def __init__(self):
        """Initialize Redis connection."""
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        try:
            self._redis = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10,
            )
            # Test connection
            await self._redis.ping()
            logger.info("Redis connection established", extra={"redis_url": settings.redis_host})
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}", extra={"error": str(e)})
            raise

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis connection closed")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self._redis.get(key)
            if value:
                logger.debug(f"Cache hit", extra={"key": key})
                return json.loads(value)
            logger.debug(f"Cache miss", extra={"key": key})
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}", extra={"key": key, "error": str(e)})
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)
        """
        try:
            ttl = ttl or settings.redis_ttl
            serialized = json.dumps(value)
            await self._redis.setex(key, ttl, serialized)
            logger.debug(f"Cache set", extra={"key": key, "ttl": ttl})
        except Exception as e:
            logger.error(f"Cache set error: {e}", extra={"key": key, "error": str(e)})

    async def delete(self, key: str):
        """
        Delete key from cache.

        Args:
            key: Cache key
        """
        try:
            await self._redis.delete(key)
            logger.debug(f"Cache delete", extra={"key": key})
        except Exception as e:
            logger.error(f"Cache delete error: {e}", extra={"key": key, "error": str(e)})

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error: {e}", extra={"key": key, "error": str(e)})
            return False


# Global cache instance
cache = RedisCache()
