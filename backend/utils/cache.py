"""
Caching utilities for improved performance

Provides TTL-based caching for frequent data access.
Automatically uses Redis if configured (REDIS_URL), otherwise falls back to in-memory.

Features:
- Redis support for distributed caching
- In-memory fallback (cachetools) for development
- JSON serialization for complex objects
"""

import hashlib
import json
import os
import threading
from collections.abc import Callable
from functools import wraps
from typing import Any

import redis
from cachetools import TTLCache

from logger import logger
from utils.env import is_dev

# ========== Cache Configuration ==========

# Redis Client
redis_client: redis.Redis | None = None
redis_url = os.getenv("REDIS_URL")

if redis_url:
    try:
        # Check if it is a valid redis url syntax
        if redis_url.startswith(("redis://", "rediss://")):
            _client = redis.from_url(redis_url, socket_connect_timeout=5, decode_responses=True)
            # Test connection
            _client.ping()
            redis_client = _client
            logger.info("Redis cache initialized successfully")
        else:
            logger.warning("Invalid REDIS_URL format. Using in-memory cache.")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory cache.")

# Fallback In-Memory Caches (used if Redis is unavailable)
_gallery_cache: TTLCache = TTLCache(maxsize=50, ttl=300)
_tags_cache: TTLCache = TTLCache(maxsize=10, ttl=600)
_user_photos_cache: TTLCache = TTLCache(maxsize=100, ttl=120)
_cache_lock = threading.Lock()

# ========== Helpers ==========


def generate_cache_key(*args, **kwargs) -> str:
    """Generate a unique cache key from arguments."""
    key_data = json.dumps(
        {
            "args": [str(a) for a in args],
            "kwargs": {k: str(v) for k, v in sorted(kwargs.items())},
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(key_data.encode()).hexdigest()


def _redis_get(key: str) -> Any | None:
    """Helper to safely get and deserialize from Redis."""
    if not redis_client:
        return None
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.error("Cache retrieval failed for identifier: %s (Error: %s)", key, e)
    return None


def _redis_set(key: str, value: Any, ttl: int) -> None:
    """Helper to safely serialize and set to Redis."""
    if not redis_client:
        return
    try:
        serialized = json.dumps(value, default=str)
        redis_client.setex(key, ttl, serialized)
    except Exception as e:
        logger.error("Cache storage failed for identifier: %s (Error: %s)", key, e)


# ========== Cache Decorators ==========


def _create_cache_wrapper(
    func: Callable,
    prefix: str,
    ttl: int,
    memory_cache: TTLCache,
    user_id_arg_index: int | None = None,
    user_id_kwarg: str | None = None,
) -> Callable:
    """Generic cache wrapper for redis/memory hybrid caching"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = _get_wrapper_cache_key(prefix, user_id_arg_index, user_id_kwarg, args, kwargs)

        # 1. Try Cache Hierarchy (Redis -> Memory)
        cached_result = _get_from_any_cache(cache_key, memory_cache, prefix)
        if cached_result is not None:
            return cached_result

        # 2. Cache Miss - Execute
        if is_dev():
            logger.debug(f"Cache MISS: {prefix}")
        result = func(*args, **kwargs)

        # 3. Save to Hierarchy
        _save_to_any_cache(cache_key, result, ttl, memory_cache)

        return result

    return wrapper


def _get_from_any_cache(key: str, memory_cache: TTLCache, prefix: str) -> Any | None:
    """Try to get result from Redis first, then Memory."""
    if redis_client:
        cached = _redis_get(key)
        if cached is not None:
            if is_dev():
                logger.debug(f"Redis Cache HIT: {prefix}")
            return cached
    elif key in memory_cache:
        with _cache_lock:
            if is_dev():
                logger.debug(f"Memory Cache HIT: {prefix}")
            return memory_cache[key]
    return None


def _save_to_any_cache(key: str, result: Any, ttl: int, memory_cache: TTLCache) -> None:
    """Save result to Redis if available, otherwise Memory."""
    if redis_client:
        _redis_set(key, result, ttl)
    else:
        with _cache_lock:
            memory_cache[key] = result


def _get_wrapper_cache_key(prefix, user_id_idx, user_id_kw, args, kwargs) -> str:
    """Helper to determine cache key for wrapper"""
    if user_id_idx is None and user_id_kw is None:
        return f"{prefix}_{generate_cache_key(*args, **kwargs)}"

    user_id = _extract_user_id(user_id_idx, user_id_kw, args, kwargs)

    # Filter args to exclude user_id if it was the first argument
    key_args = args[1:] if user_id_idx == 0 else args
    return f"{prefix}_{user_id}_{generate_cache_key(*key_args, **kwargs)}"


def _extract_user_id(idx, kw, args, kwargs) -> str:
    """Extract user_id from args or kwargs"""
    if kw and kw in kwargs:
        return str(kwargs[kw])
    if idx is not None and args and idx < len(args):
        return str(args[idx])
    return "unknown"


def cached_gallery(func: Callable) -> Callable:
    """Cache decorator for gallery endpoints. TTL: 5 minutes"""
    return _create_cache_wrapper(func, "gallery", 300, _gallery_cache)


def cached_tags(func: Callable) -> Callable:
    """Cache decorator for popular tags. TTL: 10 minutes"""
    return _create_cache_wrapper(func, "tags", 600, _tags_cache)


def cached_user_photos(func: Callable) -> Callable:
    """Cache decorator for user photos. TTL: 2 minutes"""
    return _create_cache_wrapper(func, "user", 120, _user_photos_cache, user_id_arg_index=0, user_id_kwarg="user_id")


# ========== Cache Invalidation ==========


def _redis_delete_pattern(pattern: str):
    """Helper to delete keys matching a pattern in Redis."""
    if not redis_client:
        return
    try:
        # Note: KEYS is dangerous in production used heavily, but SCAN is safer.
        # For this scale, SCAN is preferred.
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=pattern, count=100)
            if keys:
                redis_client.delete(*keys)
            if cursor == 0:
                break
    except Exception as e:
        logger.error(f"Redis delete pattern error: {e}")


def invalidate_gallery_cache():
    """Clear gallery cache entries."""
    if redis_client:
        _redis_delete_pattern("gallery_*")
    with _cache_lock:
        _gallery_cache.clear()
    logger.info("Gallery cache invalidated")


def invalidate_tags_cache():
    """Clear tags cache entries."""
    if redis_client:
        _redis_delete_pattern("tags_*")
    with _cache_lock:
        _tags_cache.clear()
    logger.info("Tags cache invalidated")


def invalidate_user_cache(user_id: str | None = None):
    """Clear user photos cache."""
    if redis_client:
        if user_id:
            _redis_delete_pattern(f"user_{user_id}_*")
        else:
            _redis_delete_pattern("user_*")

    with _cache_lock:
        if user_id:
            keys_to_remove = [k for k in _user_photos_cache.keys() if k.startswith(f"user_{user_id}")]
            for key in keys_to_remove:
                del _user_photos_cache[key]
        else:
            _user_photos_cache.clear()
    logger.info(f"User cache invalidated (Target: {user_id if user_id else 'All'})")


def invalidate_all_caches():
    """Clear all caches."""
    invalidate_gallery_cache()
    invalidate_tags_cache()
    invalidate_user_cache()
    logger.info("All caches invalidated")


# ========== Statistics ==========


def get_cache_stats() -> dict[str, Any]:
    """Get current cache statistics."""
    stats: dict[str, Any] = {
        "mode": "redis" if redis_client else "memory",
        "redis_connected": redis_client is not None,
    }

    if not redis_client:
        # Return memory stats
        with _cache_lock:
            stats["gallery"] = {
                "size": len(_gallery_cache),
                "maxsize": _gallery_cache.maxsize,
            }
            stats["tags"] = {"size": len(_tags_cache), "maxsize": _tags_cache.maxsize}
            stats["user_photos"] = {
                "size": len(_user_photos_cache),
                "maxsize": _user_photos_cache.maxsize,
            }

    return stats
