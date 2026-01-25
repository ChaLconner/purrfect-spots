"""
Rate limiter configuration using slowapi with per-user support and Redis backend.

Features:
- Per-user rate limiting (not just IP-based)
- Redis storage for production (distributed rate limiting)
- Graceful fallback to in-memory storage for development
- Different rate limits for different endpoint types
"""

import os

import jwt
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from logger import logger


def get_redis_url() -> str | None:
    """
    Get Redis URL from environment with validation.

    Returns:
        Redis URL if available and valid, None otherwise
    """
    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        logger.warning(
            "REDIS_URL not configured - using in-memory rate limiting. "
            "This is fine for development but not suitable for production "
            "with multiple server instances."
        )
        return None

    # Validate Redis URL format
    if not redis_url.startswith(("redis://", "rediss://")):
        logger.warning(
            "Invalid REDIS_URL format: should start with redis:// or rediss://. Falling back to in-memory storage."
        )
        return None

    return redis_url


def test_redis_connection(redis_url: str) -> bool:
    """
    Test Redis connection before using it for rate limiting.

    Args:
        redis_url: Redis connection URL

    Returns:
        True if connection successful, False otherwise
    """
    try:
        import redis

        client = redis.from_url(redis_url, socket_connect_timeout=5)
        client.ping()
        logger.info("Redis connection successful - using Redis for rate limiting")
        return True
    except ImportError:
        logger.warning("Redis package not installed - using in-memory rate limiting")
        return False
    except Exception as e:
        logger.warning(f"Redis connection failed: {e} - using in-memory rate limiting")
        return False


def get_storage_uri() -> str | None:
    """
    Get storage URI for rate limiter.

    Returns:
        None (In-memory storage) as requested for internal optimization
    """
    """
    Get storage URI for rate limiter.
    
    Returns:
        Redis URL if configured and working, else "memory://"
    """
    redis_url = get_redis_url()

    if redis_url and test_redis_connection(redis_url):
        return redis_url

    logger.info("Using in-memory storage for rate limiting")
    return "memory://"


def get_user_id_from_request(request: Request) -> str:
    """
    Extract user identifier for rate limiting.
    Uses authenticated user ID if available, falls back to IP address.
    This enables per-user rate limiting instead of per-IP.

    Args:
        request: FastAPI Request object

    Returns:
        User identifier string (either "user:{id}" or IP address)
    """
    # Try to get user ID from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            # Decode without verification just to get the user ID
            # Full verification happens in auth middleware
            payload = jwt.decode(token, options={"verify_signature": False})  # nosemgrep: python.jwt.security.unverified-jwt-decode.unverified-jwt-decode
            user_id = payload.get("sub") or payload.get("user_id")
            if user_id:
                return f"user:{user_id}"  # nosemgrep: python.flask.security.audit.directly-returned-format-string.directly-returned-format-string
        except Exception:
            pass

    # Fall back to IP address for unauthenticated requests
    return get_remote_address(request)


def get_identifier_with_endpoint(request: Request) -> str:
    """
    Get identifier that includes both user/IP and endpoint.
    This allows different rate limits per endpoint per user.

    Args:
        request: FastAPI Request object

    Returns:
        Combined identifier string
    """
    base_id = get_user_id_from_request(request)
    endpoint = request.url.path
    return f"{base_id}:{endpoint}"


# Get validated storage URI (Redis or None for in-memory)
_storage_uri = get_storage_uri()

# ========== Rate Limiters ==========

# Standard rate limiter for general API endpoints
limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=["100/minute"],
    storage_uri=_storage_uri,
    strategy="fixed-window",
)

# Strict rate limiter for resource-intensive endpoints (cat detection, uploads)
strict_limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=["5/minute"],
    storage_uri=_storage_uri,
    strategy="fixed-window",
)

# Upload rate limiter - moderate limits for file uploads
upload_limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=["10/minute"],
    storage_uri=_storage_uri,
    strategy="fixed-window",
)

# Auth rate limiter - very strict for login/register attempts (brute force protection)
auth_limiter = Limiter(
    key_func=get_remote_address,  # Use IP for auth to prevent credential stuffing
    default_limits=["10/minute", "50/hour"],
    storage_uri=_storage_uri,
    strategy="fixed-window",
)


def get_rate_limit_info() -> dict:
    """
    Get current rate limiting configuration info.
    Useful for health checks and debugging.

    Returns:
        Dictionary with rate limiting configuration
    """
    return {
        "storage_type": "memory",
        "redis_configured": False,
        "redis_connected": False,
        "limits": {
            "default": "100/minute",
            "strict": "5/minute",
            "upload": "10/minute",
            "auth": "10/minute, 50/hour",
        },
    }
