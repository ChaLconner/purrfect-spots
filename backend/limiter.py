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

from config import config
from logger import logger


def get_redis_url() -> str | None:
    """
    Get Redis URL from environment with validation.

    Returns:
        Redis URL if available and valid, None otherwise
    """
    redis_url = config.REDIS_URL

    if not redis_url:
        if config.is_production():
            logger.warning(
                "REDIS_URL not configured - using in-memory rate limiting. "
                "This is not suitable for production with multiple server instances."
            )
        else:
            logger.info("REDIS_URL not configured - using in-memory rate limiting (dev mode).")
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

            # Use secure verification - require valid secret
            # We catch errors gracefully to fall back to IP limiting for bad tokens
            if not config.JWT_SECRET:
                # No secret configured - fall back to IP-based rate limiting
                # rather than decoding without verification
                pass
            else:
                payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
                user_id = payload.get("sub") or payload.get("user_id")
                if user_id:
                    # nosemgrep: python.flask.security.audit.directly-returned-format-string.directly-returned-format-string
                    return f"user:{user_id}"
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            # Token is invalid or expired
            # Treat as unauthenticated user (fall back to IP)
            pass
        except Exception as e:
            logger.warning(f"Failed to decode token for rate limiting user extraction: {e}")

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
    default_limits=[config.RATE_LIMIT_API_DEFAULT],
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
    default_limits=[config.UPLOAD_RATE_LIMIT],
    storage_uri=_storage_uri,
    strategy="fixed-window",
)

# Auth rate limiter - very strict for login/register attempts (brute force protection)
auth_limiter = Limiter(
    key_func=get_remote_address,  # Use IP for auth to prevent credential stuffing
    default_limits=[config.RATE_LIMIT_AUTH],
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
        "storage_type": "redis" if _storage_uri and _storage_uri != "memory://" else "memory",
        "redis_configured": bool(config.REDIS_URL),
        "limits": {
            "default": config.RATE_LIMIT_API_DEFAULT,
            "strict": "5/minute",
            "upload": config.UPLOAD_RATE_LIMIT,
            "auth": config.RATE_LIMIT_AUTH,
        },
    }
