import functools
import hashlib
import json
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

import redis.asyncio as redis

from config import config
from logger import logger

# Initialize Redis client
redis_url = config.REDIS_URL
redis_client: redis.Redis | None = None

# Export is_dev for compatibility with tests
is_dev = config.ENVIRONMENT.lower() in ["development", "testing"]

# Memory cache fallback for dev/test
memory_cache: dict[str, Any] = {}

if redis_url:
    try:
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")


class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, "model_dump"):
            return o.model_dump()
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return super().default(o)


def generate_cache_key(*args: Any, **kwargs: Any) -> str:
    """Helper to generate a consistent cache key for given args/kwargs"""
    arg_str = json.dumps(
        {"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}}, default=str, sort_keys=True
    )
    return hashlib.sha256(arg_str.encode()).hexdigest()


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
                # Skip first N args for key generation (e.g. self, cls, client)
                key_args = args[skip_args:]
                arg_hash = generate_cache_key(*key_args, **kwargs)
                cache_key = f"cache:{key_prefix or func.__name__}:{arg_hash}"

                # 2. Try to get from Cache
                if redis_client:
                    try:
                        cached_data = await redis_client.get(cache_key)
                        if cached_data:
                            if is_dev:
                                logger.debug(f"Cache hit (Redis): {cache_key}")
                            return json.loads(cached_data)
                    except Exception as e:
                        if "Event loop is closed" not in str(e):
                            logger.warning(f"Redis read error: {e}")

                if cache_key in memory_cache:
                    if is_dev:
                        logger.debug(f"Cache hit (Memory): {cache_key}")
                    return memory_cache[cache_key]

                if is_dev:
                    logger.debug(f"Cache miss: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache key/read error: {e}")

            # 3. Fetch fresh data
            result = await func(*args, **kwargs)

            # 4. Save to Cache
            try:
                if redis_client:
                    try:
                        serialized = json.dumps(result, cls=JSONEncoder)
                        await redis_client.setex(cache_key, expire, serialized)
                    except Exception as e:
                        if "Event loop is closed" not in str(e):
                            logger.warning(f"Redis write error: {e}")

                memory_cache[cache_key] = result
            except Exception as e:
                logger.warning(f"Memory cache write error: {e}")

            return result

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
            import asyncio

            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return  # No running loop

            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
        except Exception:  # nosec B110
            pass


async def invalidate_all_caches() -> None:
    """Invalidate all application caches"""
    await clear_cache("cache:*")


# Aliases for compatibility
cached_gallery = cache(expire=300, key_prefix="gallery", skip_args=1)
cached_tags = cache(expire=600, key_prefix="tags", skip_args=1)
cached_leaderboard = cache(expire=300, key_prefix="leaderboard", skip_args=1)
cached_user_photos = cache(expire=300, key_prefix="user_photos", skip_args=1)


# Invalidation helpers
async def invalidate_gallery_cache() -> None:
    await clear_cache("cache:gallery:*")


async def invalidate_tags_cache() -> None:
    await clear_cache("cache:tags:*")


async def invalidate_leaderboard_cache() -> None:
    await clear_cache("cache:leaderboard:*")


async def invalidate_user_cache(user_id: str | None = None) -> None:
    # Always clear user_photos as user_id specific one is hard to match with hash
    await clear_cache("cache:user_photos:*")


def get_cache_stats() -> dict[str, Any]:
    return {
        "mode": "redis" if redis_client else "memory",
        "redis_connected": redis_client is not None,
        "memory_cache_size": len(memory_cache),
        "environment": config.ENVIRONMENT,
        "gallery": {"maxsize": 50},
        "tags": {"maxsize": 50},
        "user_photos": {"maxsize": 50},
    }
