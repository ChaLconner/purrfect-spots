import asyncio
import functools
import hashlib
import json
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")

import redis.asyncio as redis

from app.config import config
from app.logger import logger
from app.services.redis_service import redis_service

# Reuse RedisService connection pool. Separate clients created here and in token
# handling caused unnecessary pools and made shutdown harder to manage.
redis_client: redis.Redis | None = redis_service.client

# Export is_dev for compatibility with tests
is_dev = config.ENVIRONMENT.lower() in ["development", "testing"]

# Memory cache fallback for dev/test — with size limit to prevent leaks
_MEMORY_CACHE_MAX_SIZE = 500


@dataclass
class MemoryCacheEntry:
    value: Any
    expires_at: float


memory_cache: dict[str, MemoryCacheEntry] = {}
_inflight_locks: dict[str, asyncio.Lock] = {}


class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, "model_dump"):
            return o.model_dump()
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if isinstance(o, set):
            return list(o)
        if isinstance(o, bytes):
            return o.decode("utf-8", errors="replace")
        from uuid import UUID

        if isinstance(o, UUID):
            return str(o)
        return super().default(o)


def _purge_expired_memory_entries(now: float | None = None) -> None:
    current_time = time.monotonic() if now is None else now
    expired_keys = [key for key, entry in memory_cache.items() if entry.expires_at <= current_time]
    for key in expired_keys:
        del memory_cache[key]


def generate_cache_key(*args: Any, **kwargs: Any) -> str:
    """Helper to generate a consistent cache key for given args/kwargs"""
    arg_str = json.dumps(
        {"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}, default=str, sort_keys=True
    )
    return hashlib.md5(arg_str.encode(), usedforsecurity=False).hexdigest()  # nosec B303


async def _read_cached_value(cache_key: str) -> Any | None:
    """Read cache backends in priority order."""
    if redis_client:
        try:
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                try:
                    return json.loads(cached_data)
                except json.JSONDecodeError:
                    logger.warning("Invalid cached JSON for key: %s", cache_key)
        except Exception as e:
            if "Event loop is closed" not in str(e):
                logger.warning("Redis read error: %s", e)

    memory_entry = memory_cache.get(cache_key)
    if memory_entry is None:
        return None
    if memory_entry.expires_at <= time.monotonic():
        memory_cache.pop(cache_key, None)
        return None
    return memory_entry.value


async def _write_cached_value(cache_key: str, result: Any, expire: int) -> None:
    """Write Redis when available; retain memory only as fallback."""
    if redis_client:
        try:
            serialized = json.dumps(result, cls=JSONEncoder)
            await redis_client.setex(cache_key, expire, serialized)
            return
        except Exception as e:
            if "Event loop is closed" not in str(e):
                logger.warning("Redis write error: %s", e)

    _purge_expired_memory_entries()
    if len(memory_cache) >= _MEMORY_CACHE_MAX_SIZE and cache_key not in memory_cache:
        evict_count = _MEMORY_CACHE_MAX_SIZE // 5
        for old_key in list(memory_cache.keys())[:evict_count]:
            del memory_cache[old_key]
    memory_cache[cache_key] = MemoryCacheEntry(
        value=result,
        expires_at=time.monotonic() + max(expire, 0),
    )


def cache(
    expire: int = 60, key_prefix: str = "", skip_args: int = 0
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], Callable[..., Coroutine[Any, Any, Any]]]:
    """
    Cache decorator for async functions using Redis (with memory fallback).
    """

    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Coroutine[Any, Any, Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 1. Generate Cache Key
            try:
                _purge_expired_memory_entries()

                # Skip first N args for key generation (e.g. self, cls, client)
                key_args = args[skip_args:]
                arg_hash = generate_cache_key(*key_args, **kwargs)
                namespace = key_prefix or func.__name__
                cache_key = f"cache:{namespace}:{func.__name__}:{arg_hash}"

                cached = await _read_cached_value(cache_key)
                if cached is not None:
                    if is_dev:
                        logger.debug("Cache hit: %s", cache_key)
                    return cached
                if is_dev:
                    logger.debug("Cache miss: %s", cache_key)
            except Exception as e:
                logger.warning("Cache key/read error: %s", e)

            # 2. Coalesce concurrent misses for the same key.
            lock = _inflight_locks.setdefault(cache_key, asyncio.Lock())
            try:
                async with lock:
                    cached = await _read_cached_value(cache_key)
                    if cached is not None:
                        return cached
                    result = await func(*args, **kwargs)
                    try:
                        await _write_cached_value(cache_key, result, expire)
                    except Exception as e:
                        logger.warning("Cache write skipped: %s", e)
                    return result
            except Exception as e:
                logger.warning("Cache fetch/write error: %s", e)
                raise
            finally:
                waiters = getattr(lock, "_waiters", None)
                if not lock.locked() and not waiters:
                    _inflight_locks.pop(cache_key, None)

        return wrapper

    return decorator


async def clear_cache(pattern: str = "cache:*") -> None:
    """Clear cache by pattern"""
    # 1. Clear Memory Cache
    if pattern == "cache:*":
        memory_cache.clear()
    else:
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            keys_to_del = [k for k in list(memory_cache.keys()) if k.startswith(prefix)]
            for k in keys_to_del:
                del memory_cache[k]
        else:
            if pattern in memory_cache:
                del memory_cache[pattern]

    # 2. Clear Redis Cache
    if redis_client:
        try:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return  # No running loop

            batch: list[str] = []
            async for key in redis_client.scan_iter(match=pattern, count=500):
                batch.append(str(key))
                if len(batch) >= 500:
                    await redis_client.delete(*batch)
                    batch.clear()
            if batch:
                await redis_client.delete(*batch)
        except Exception as e:
            logger.debug(f"Failed to clear Redis cache: {e}")
            # pass


async def clear_cache_patterns(patterns: tuple[str, ...]) -> None:
    """Invalidate related namespaces with one Redis scan."""
    prefixes = tuple(pattern[:-1] if pattern.endswith("*") else pattern for pattern in patterns)
    for key in list(memory_cache):
        if any(key.startswith(prefix) for prefix in prefixes):
            memory_cache.pop(key, None)

    if not redis_client:
        return
    try:
        batch: list[str] = []
        async for key in redis_client.scan_iter(match="cache:*", count=500):
            key_text = str(key)
            if any(key_text.startswith(prefix) for prefix in prefixes):
                batch.append(key_text)
            if len(batch) >= 500:
                await redis_client.delete(*batch)
                batch.clear()
        if batch:
            await redis_client.delete(*batch)
    except Exception as e:
        logger.debug("Failed to clear related Redis caches: %s", e)


async def invalidate_all_caches() -> None:
    """Invalidate all application caches"""
    await clear_cache("cache:*")


# Aliases for compatibility
cached_gallery = cache(expire=300, key_prefix="gallery", skip_args=1)
cached_tags = cache(expire=600, key_prefix="tags", skip_args=1)
cached_leaderboard = cache(expire=300, key_prefix="leaderboard", skip_args=1)
cached_user_photos = cache(expire=300, key_prefix="user_photos", skip_args=1)
cached_user_likes = cache(expire=300, key_prefix="user_likes", skip_args=1)


# Invalidation helpers
async def invalidate_gallery_cache() -> None:
    await clear_cache_patterns(("cache:gallery:*", "cache:nearby:*", "cache:viewport:*"))


async def invalidate_tags_cache() -> None:
    await clear_cache("cache:tags:*")


async def invalidate_leaderboard_cache() -> None:
    await clear_cache("cache:leaderboard:*")


async def invalidate_user_cache(user_id: str | None = None) -> None:
    # Always clear user_photos as user_id specific one is hard to match with hash
    await clear_cache_patterns(("cache:user_photos:*", "cache:user_likes:*"))


async def invalidate_after_upload(user_id: str) -> None:
    """Invalidate upload-affected namespaces with one bounded Redis scan."""
    await clear_cache_patterns(
        (
            "cache:gallery:*",
            "cache:nearby:*",
            "cache:viewport:*",
            "cache:tags:*",
            "cache:user_photos:*",
            "cache:user_likes:*",
        )
    )


def get_cache_stats() -> dict[str, Any]:
    _purge_expired_memory_entries()
    return {
        "mode": "redis" if redis_client else "memory",
        "redis_connected": redis_client is not None,
        "memory_cache_size": len(memory_cache),
        "environment": config.ENVIRONMENT,
        "gallery": {"maxsize": 50},
        "tags": {"maxsize": 50},
        "user_photos": {"maxsize": 50},
    }
