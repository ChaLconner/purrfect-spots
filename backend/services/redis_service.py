import json
from datetime import datetime
from typing import Any

import redis.asyncio as aioredis

from config import Config
from logger import logger


class JSONSerializer(json.JSONEncoder):
    """Custom JSON encoder to handle datetime, UUID, and Pydantic models."""

    def default(self, o: Any) -> Any:
        if hasattr(o, "model_dump"):
            return o.model_dump()
        if hasattr(o, "dict"):  # Fallback for older Pydantic
            return o.dict()
        if isinstance(o, datetime):
            return o.isoformat()
        from uuid import UUID

        if isinstance(o, UUID):
            return str(o)
        if isinstance(o, set):
            return list(o)
        return super().default(o)


class RedisService:
    def __init__(self):
        self.url = Config.REDIS_URL
        self.client: aioredis.Redis | None = None
        if self.url:
            try:
                # FIX: Use async Redis client to avoid blocking FastAPI's event loop.
                # Previous implementation used synchronous redis.Redis which blocked
                # the event loop on every cache read/write operation.
                self.client = aioredis.from_url(self.url, decode_responses=True)
                logger.info(
                    "Redis (async) configured at %s",
                    self.url.split("@")[-1] if "@" in self.url else self.url,
                )
            except Exception as e:
                logger.error("Failed to configure async Redis client: %s. Falling back to no-cache.", e)
                self.client = None

    async def ping(self) -> bool:
        """Test connection to Redis. Replaces the synchronous ping() on init."""
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error("Redis ping failed: %s", e)
            return False

    async def get(self, key: str) -> Any | None:
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.error("Redis get error for %s: %s", key, e)
            return None

    async def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """expire in seconds, default 5 mins"""
        if not self.client:
            return False
        try:
            serialized_value = json.dumps(value, cls=JSONSerializer)
            await self.client.set(key, serialized_value, ex=expire)
            return True
        except Exception as e:
            logger.error("Redis set error for %s: %s", key, e)
            return False

    async def delete(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error("Redis delete error for %s: %s", key, e)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern. Returns count of deleted keys."""
        if not self.client:
            return 0
        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error("Redis delete_pattern error for %s: %s", pattern, e)
            return 0


redis_service = RedisService()
