import asyncio
import json
import os
import secrets
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, cast

import redis.asyncio as aioredis

from app.config import Config
from app.logger import logger


class RedisLockError(RuntimeError):
    """Base error for distributed lock failures."""


class RedisLockUnavailable(RedisLockError):
    """Raised when a production lock cannot reach Redis."""


class RedisLockTimeout(RedisLockError):
    """Raised when a lock cannot be acquired before its deadline."""


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
    _local_locks: dict[str, asyncio.Lock] = {}

    def __init__(self) -> None:
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

    async def close(self) -> None:
        """Close shared Redis pool during application shutdown."""
        if self.client:
            try:
                # redis-py exposes aclose at runtime; its installed typing
                # surface still exposes only close on some supported versions.
                await cast(Any, self.client).aclose()
            except Exception:
                logger.warning("Failed to close Redis pool", exc_info=True)

    async def get(self, key: str) -> Any | None:
        if not self.client:
            return None
        try:
            val = await self.client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.error("Redis get error for %s: %s", str(key).replace("\n", " "), str(e).replace("\n", " "))
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
            logger.error("Redis set error for %s: %s", str(key).replace("\n", " "), str(e).replace("\n", " "))
            return False

    async def delete(self, key: str) -> bool:
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error("Redis delete error for %s: %s", str(key).replace("\n", " "), str(e).replace("\n", " "))
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern. Returns count of deleted keys."""
        if not self.client:
            return 0
        try:
            deleted = 0
            batch: list[str] = []
            async for key in self.client.scan_iter(match=pattern, count=500):
                batch.append(str(key))
                if len(batch) >= 500:
                    deleted += int(await self.client.delete(*batch))
                    batch.clear()
            if batch:
                deleted += int(await self.client.delete(*batch))
            return deleted
        except Exception as e:
            logger.error("Redis delete_pattern error for %s: %s", pattern, e)
            return 0

    @staticmethod
    def _use_local_lock() -> bool:
        """Keep unit tests deterministic without touching configured Redis."""
        return Config.ENVIRONMENT.lower() in {"test", "testing"} or bool(os.getenv("PYTEST_CURRENT_TEST"))

    @classmethod
    async def _acquire_local_lock(cls, key: str, wait_timeout: float) -> asyncio.Lock:
        local_lock = cls._local_locks.setdefault(key, asyncio.Lock())
        if wait_timeout <= 0:
            if local_lock.locked():
                raise RedisLockTimeout(f"Timed out acquiring local lock {key}")
            await local_lock.acquire()
            return local_lock
        try:
            await asyncio.wait_for(local_lock.acquire(), timeout=wait_timeout)
        except TimeoutError as exc:
            raise RedisLockTimeout(f"Timed out acquiring local lock {key}") from exc
        return local_lock

    @asynccontextmanager
    async def lock(self, key: str, *, ttl: int = 60, wait_timeout: float = 15.0) -> AsyncIterator[None]:
        """Acquire a cross-instance lock with token-safe release.

        Production fails closed when Redis is unavailable. Development and tests
        use an in-process lock so local execution remains usable without Redis.
        """
        if not key:
            raise ValueError("Redis lock key cannot be empty")
        ttl = max(1, int(ttl))
        wait_timeout = max(0.0, float(wait_timeout))

        if self._use_local_lock():
            try:
                local_lock = await self._acquire_local_lock(key, wait_timeout)
            except RedisLockTimeout:
                raise
            try:
                yield
            finally:
                if local_lock.locked():
                    local_lock.release()
            return

        if not self.client:
            if Config.is_production():
                raise RedisLockUnavailable("Redis is required for distributed subscription locking")
            # Development without Redis still gets a safe single-process guard.
            try:
                local_lock = await self._acquire_local_lock(key, wait_timeout)
            except RedisLockTimeout:
                raise
            try:
                yield
            finally:
                if local_lock.locked():
                    local_lock.release()
            return

        token = secrets.token_urlsafe(24)
        deadline = time.monotonic() + wait_timeout
        acquired = False
        try:
            while time.monotonic() <= deadline:
                try:
                    acquired = bool(await self.client.set(key, token, nx=True, ex=ttl))
                except Exception as exc:
                    raise RedisLockUnavailable("Redis lock operation failed") from exc
                if acquired:
                    break
                await asyncio.sleep(0.05)

            if not acquired:
                raise RedisLockTimeout(f"Timed out acquiring Redis lock {key}")

            yield
        finally:
            if acquired:
                # Delete only our own lease. A plain DEL could remove a lock
                # acquired by another request after this lease expired.
                release_script = (
                    "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"
                )
                try:
                    await self.client.eval(release_script, 1, key, token)
                except Exception:
                    logger.warning("Failed to release Redis lock %s", key, exc_info=True)


redis_service = RedisService()
