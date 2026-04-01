import json
from datetime import datetime
from typing import Any

import redis

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
        self.client = None
        if self.url:
            try:
                # Use standard redis client
                self.client = redis.from_url(self.url, decode_responses=True)
                # Test connection
                self.client.ping()
                logger.info("Connected to Redis at %s", self.url.split("@")[-1] if "@" in self.url else self.url)
            except Exception as e:
                logger.error("Failed to connect to Redis: %s. Falling back to no-cache.", e)
                self.client = None

    def get(self, key: str) -> Any | None:
        if not self.client:
            return None
        try:
            val = self.client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.error("Redis get error for %s: %s", key, e)
            return None

    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """expire in seconds, default 5 mins"""
        if not self.client:
            return False
        try:
            serialized_value = json.dumps(value, cls=JSONSerializer)
            self.client.set(key, serialized_value, ex=expire)
            return True
        except Exception as e:
            logger.error("Redis set error for %s: %s", key, e)
            return False

    def delete(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error("Redis delete error for %s: %s", key, e)
            return False


redis_service = RedisService()
