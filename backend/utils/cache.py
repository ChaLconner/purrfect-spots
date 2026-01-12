"""
Caching utilities for improved performance

Provides TTL-based caching for frequently accessed data like:
- Gallery images
- Popular tags
- User photos

Uses cachetools for thread-safe in-memory caching.
"""
from functools import wraps
from typing import Any, Callable, Optional
from cachetools import TTLCache
import threading
import hashlib
import json
from logger import logger
from utils.env import is_dev

# ========== Cache Configuration ==========

# Gallery cache: 5 minutes TTL, max 50 entries
_gallery_cache = TTLCache(maxsize=50, ttl=300)

# Popular tags cache: 10 minutes TTL (tags don't change often)
_tags_cache = TTLCache(maxsize=10, ttl=600)

# User photos cache: 2 minutes TTL
_user_photos_cache = TTLCache(maxsize=100, ttl=120)

# Lock for thread-safe cache operations
_cache_lock = threading.Lock()

# ========== Cache Key Generation ==========

def generate_cache_key(*args, **kwargs) -> str:
    """Generate a unique cache key from arguments."""
    key_data = json.dumps({
        'args': [str(a) for a in args],
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
    }, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()

# ========== Cache Decorators ==========

def cached_gallery(func: Callable) -> Callable:
    """
    Cache decorator for gallery endpoints.
    TTL: 5 minutes
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = f"gallery_{generate_cache_key(*args, **kwargs)}"
        
        with _cache_lock:
            if cache_key in _gallery_cache:
                if is_dev():
                    logger.debug(f"Cache HIT: {func.__name__}")
                return _gallery_cache[cache_key]
        
        result = func(*args, **kwargs)
        
        with _cache_lock:
            _gallery_cache[cache_key] = result
        
        if is_dev():
            logger.debug(f"Cache MISS: {func.__name__}")
        
        return result
    
    return wrapper


def cached_tags(func: Callable) -> Callable:
    """
    Cache decorator for popular tags.
    TTL: 10 minutes
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache_key = f"tags_{generate_cache_key(*args, **kwargs)}"
        
        with _cache_lock:
            if cache_key in _tags_cache:
                if is_dev():
                    logger.debug(f"Tags Cache HIT")
                return _tags_cache[cache_key]
        
        result = func(*args, **kwargs)
        
        with _cache_lock:
            _tags_cache[cache_key] = result
        
        if is_dev():
            logger.debug(f"Tags Cache MISS")
        
        return result
    
    return wrapper


def cached_user_photos(func: Callable) -> Callable:
    """
    Cache decorator for user photos.
    TTL: 2 minutes
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract user_id for cache key
        user_id = kwargs.get('user_id') or (args[0] if args else 'unknown')
        cache_key = f"user_{user_id}_{generate_cache_key(*args[1:], **kwargs)}"
        
        with _cache_lock:
            if cache_key in _user_photos_cache:
                if is_dev():
                    logger.debug(f"User photos Cache HIT: {user_id}")
                return _user_photos_cache[cache_key]
        
        result = func(*args, **kwargs)
        
        with _cache_lock:
            _user_photos_cache[cache_key] = result
        
        if is_dev():
            logger.debug(f"User photos Cache MISS: {user_id}")
        
        return result
    
    return wrapper

# ========== Cache Invalidation ==========

def invalidate_gallery_cache():
    """Clear all gallery cache entries."""
    with _cache_lock:
        _gallery_cache.clear()
    logger.info("Gallery cache invalidated")


def invalidate_tags_cache():
    """Clear all tags cache entries."""
    with _cache_lock:
        _tags_cache.clear()
    logger.info("Tags cache invalidated")


def invalidate_user_cache(user_id: Optional[str] = None):
    """
    Clear user photos cache.
    If user_id is provided, only clear that user's cache.
    """
    with _cache_lock:
        if user_id:
            keys_to_remove = [k for k in _user_photos_cache.keys() if k.startswith(f"user_{user_id}")]
            for key in keys_to_remove:
                del _user_photos_cache[key]
            logger.info(f"User cache invalidated for: {user_id}")
        else:
            _user_photos_cache.clear()
            logger.info("All user caches invalidated")


def invalidate_all_caches():
    """Clear all caches. Use after data mutations."""
    invalidate_gallery_cache()
    invalidate_tags_cache()
    invalidate_user_cache()
    logger.info("All caches invalidated")

# ========== Cache Statistics ==========

def get_cache_stats() -> dict:
    """Get current cache statistics."""
    with _cache_lock:
        return {
            'gallery': {
                'size': len(_gallery_cache),
                'maxsize': _gallery_cache.maxsize,
                'ttl': _gallery_cache.ttl
            },
            'tags': {
                'size': len(_tags_cache),
                'maxsize': _tags_cache.maxsize,
                'ttl': _tags_cache.ttl
            },
            'user_photos': {
                'size': len(_user_photos_cache),
                'maxsize': _user_photos_cache.maxsize,
                'ttl': _user_photos_cache.ttl
            }
        }
