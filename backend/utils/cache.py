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
_gallery_cache = TTLCache(maxsize=50, ttl=300)
_tags_cache = TTLCache(maxsize=10, ttl=600)
_user_photos_cache = TTLCache(maxsize=100, ttl=120)
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


def cached_gallery(func: Callable) -> Callable:
    """
    Cache decorator for gallery endpoints.
    TTL: 5 minutes (300s)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = f"gallery_{generate_cache_key(*args, **kwargs)}"

        # 1. Try Redis
        if redis_client:
            cached = _redis_get(cache_key)
            if cached is not None:
                if is_dev():
                    logger.debug(f"Redis Cache HIT: {func.__name__}")
                else:
                    logger.info(f"Redis Cache HIT: {func.__name__} (key: {cache_key[:20]}...)")
                return cached

        # 2. Try Memory (Fallback)
        elif cache_key in _gallery_cache:
            with _cache_lock:
                if is_dev():
                    logger.debug(f"Memory Cache HIT: {func.__name__}")
                else:
                    logger.info(f"Memory Cache HIT: {func.__name__} (key: {cache_key[:20]}...)")
                return _gallery_cache[cache_key]

        # 3. Execute Function
        if is_dev():
            logger.debug(f"Cache MISS: {func.__name__}")
        else:
            logger.info(f"Cache MISS: {func.__name__} - Executing function (key: {cache_key[:20]}...)")
        result = func(*args, **kwargs)

        # 4. Save to Cache
        if redis_client:
            _redis_set(cache_key, result, 300)
            logger.info(f"Saved to Redis cache: {func.__name__} (TTL: 300s)")
        else:
            with _cache_lock:
                _gallery_cache[cache_key] = result
            logger.info(f"Saved to Memory cache: {func.__name__} (TTL: 300s)")

        return result

    return wrapper


def cached_tags(func: Callable) -> Callable:
    """
    Cache decorator for popular tags.
    TTL: 10 minutes (600s)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = f"tags_{generate_cache_key(*args, **kwargs)}"

        if redis_client:
            cached = _redis_get(cache_key)
            if cached is not None:
                if is_dev():
                    logger.debug("Redis Tags Cache HIT")
                return cached
        elif cache_key in _tags_cache:
            with _cache_lock:
                if is_dev():
                    logger.debug("Memory Tags Cache HIT")
                return _tags_cache[cache_key]

        result = func(*args, **kwargs)

        if redis_client:
            _redis_set(cache_key, result, 600)
        else:
            with _cache_lock:
                _tags_cache[cache_key] = result

        return result

    return wrapper


def cached_user_photos(func: Callable) -> Callable:
    """
    Cache decorator for user photos.
    TTL: 2 minutes (120s)
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = kwargs.get("user_id") or (args[0] if args else "unknown")
        cache_key = f"user_{user_id}_{generate_cache_key(*args[1:], **kwargs)}"

        if redis_client:
            cached = _redis_get(cache_key)
            if cached is not None:
                if is_dev():
                    logger.debug(f"Redis User Cache HIT: {user_id}")
                return cached
        elif cache_key in _user_photos_cache:
            with _cache_lock:
                if is_dev():
                    logger.debug(f"Memory User Cache HIT: {user_id}")
                return _user_photos_cache[cache_key]

        result = func(*args, **kwargs)

        if redis_client:
            _redis_set(cache_key, result, 120)
        else:
            with _cache_lock:
                _user_photos_cache[cache_key] = result

        return result

    return wrapper


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
