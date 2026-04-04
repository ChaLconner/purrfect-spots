"""
Rate limiter configuration using slowapi with per-user support and Redis backend.

Features:
- Per-user rate limiting (not just IP-based)
- Redis storage for production (distributed rate limiting)
- Graceful fallback to in-memory storage for development
- Different rate limits for different endpoint types
"""

from typing import Any, cast

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

        if redis_url.startswith("rediss://"):
            client = redis.from_url(
                redis_url,
                socket_connect_timeout=10,
                socket_timeout=10,
                ssl_cert_reqs=None,  # Mitigate WinError 10054 with Upstash
            )
        else:
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


def get_user_tier(request: Request) -> str:
    """
    Extract user tier from JWT. Defaults to 'free'.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            if config.JWT_SECRET:
                payload = jwt.decode(
                    token,
                    config.JWT_SECRET,
                    algorithms=[config.JWT_ALGORITHM],
                    options={"verify_signature": True, "verify_exp": True},
                )
                # Check for tier in app_metadata or user_metadata (Supabase standard)
                # Supabase often puts it in app_metadata
                app_metadata = payload.get("app_metadata", {})
                return str(app_metadata.get("tier", "free")).lower()
        except Exception as e:
            logger.debug(f"Failed to extract user tier from JWT: {e}")
            pass
    return "free"


def get_user_id_from_request(request: Request) -> str:
    """
    Extract user identifier for rate limiting.
    Uses authenticated user ID if available, falls back to IP address.
    Includes user tier in the identifier to support dynamic rate limits.
    """
    tier = get_user_tier(request)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            if config.JWT_SECRET:
                payload = jwt.decode(
                    token,
                    config.JWT_SECRET,
                    algorithms=[config.JWT_ALGORITHM],
                    options={"verify_signature": True, "verify_exp": True},
                )
                user_id = payload.get("sub") or payload.get("user_id")
                if user_id:
                    clean_user_id = "".join(c for c in str(user_id) if c.isalnum() or c in "-_@.")
                    # Return user identifier WITH tier for dynamic limit resolution
                    return f"user:{clean_user_id[0:128]}:{tier}"
        except Exception as e:
            logger.debug(f"Failed to extract user ID from JWT: {e}")
            pass

    # Fallback to IP address with tier
    return f"{get_remote_address(request)}:{tier}"


# Dynamic Limit Resolvers
# These MUST accept a 'key' parameter to be correctly handled by slowapi's dynamic limits
def get_strict_limit(key: str) -> str:
    """Resolve tiered strict limit based on identifier key"""
    tier = key.split(":")[-1] if ":" in key else "free"
    return config.RATE_LIMIT_STRICT_PRO if tier == "pro" else config.RATE_LIMIT_STRICT_FREE


def get_upload_limit(key: str) -> str:
    """Resolve tiered upload limit based on identifier key"""
    tier = key.split(":")[-1] if ":" in key else "free"
    return config.RATE_LIMIT_UPLOAD_PRO if tier == "pro" else config.RATE_LIMIT_UPLOAD_FREE


def get_api_limit(key: str) -> str:
    """Resolve tiered API limit based on identifier key"""
    tier = key.split(":")[-1] if ":" in key else "free"
    return config.RATE_LIMIT_API_PRO if tier == "pro" else config.RATE_LIMIT_API_FREE


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
# Wrapped in try/except to prevent import-time crashes if Redis is unreachable
try:
    _storage_uri = get_storage_uri()
except Exception as e:
    logger.warning(f"Failed to initialize rate limit storage: {e} — falling back to in-memory")
    _storage_uri = "memory://"

# ========== Rate Limiters ==========

# Prepare storage options for Redis to handle timeouts and connection drops gracefully
# This is especially important for Upstash which may close idle connections
_storage_options = {}
if _storage_uri and _storage_uri.startswith("rediss://"):
    _storage_options = {
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "health_check_interval": 30,  # Check connection health every 30s to detect closed contentions
        "ssl_cert_reqs": None,  # Mitigate WinError 10054 with Upstash
    }
elif _storage_uri and _storage_uri.startswith("redis://"):
    _storage_options = {
        "socket_connect_timeout": 5,
        "socket_timeout": 5,
        "health_check_interval": 30,
    }

# Standard rate limiter for general API endpoints
limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=[get_api_limit],
    storage_uri=_storage_uri,
    storage_options=cast(Any, _storage_options),
    strategy="fixed-window",
    swallow_errors=True,
    in_memory_fallback_enabled=True,
)

# Strict rate limiter for resource-intensive endpoints (cat detection, uploads)
strict_limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=[get_strict_limit],
    storage_uri=_storage_uri,
    storage_options=cast(Any, _storage_options),
    strategy="fixed-window",
    swallow_errors=True,
    in_memory_fallback_enabled=True,
)

# Upload rate limiter - moderate limits for file uploads
upload_limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=[get_upload_limit],
    storage_uri=_storage_uri,
    storage_options=cast(Any, _storage_options),
    strategy="fixed-window",
    swallow_errors=True,
    in_memory_fallback_enabled=True,
)

# Auth rate limiter - very strict for login/register attempts (brute force protection)
auth_limiter = Limiter(
    key_func=get_remote_address,  # Use IP for auth to prevent credential stuffing
    default_limits=[config.RATE_LIMIT_AUTH],
    storage_uri=_storage_uri,
    storage_options=cast(Any, _storage_options),
    strategy="fixed-window",
    swallow_errors=True,
    in_memory_fallback_enabled=True,
)

# Forgot password rate limiter - even stricter to prevent mail bombing
forgot_password_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[config.RATE_LIMIT_FORGOT_PASSWORD],
    storage_uri=_storage_uri,
    storage_options=cast(Any, _storage_options),
    strategy="fixed-window",
    swallow_errors=True,
    in_memory_fallback_enabled=True,
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
            "strict_free": config.RATE_LIMIT_STRICT_FREE,
            "strict_pro": config.RATE_LIMIT_STRICT_PRO,
            "upload_free": config.RATE_LIMIT_UPLOAD_FREE,
            "upload_pro": config.RATE_LIMIT_UPLOAD_PRO,
            "api_free": config.RATE_LIMIT_API_FREE,
            "api_pro": config.RATE_LIMIT_API_PRO,
            "auth": config.RATE_LIMIT_AUTH,
            "forgot_password": config.RATE_LIMIT_FORGOT_PASSWORD,
        },
    }
