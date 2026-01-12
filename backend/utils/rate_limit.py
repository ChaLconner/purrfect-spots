"""
Rate limiting configuration for API endpoints

Uses slowapi for request rate limiting to prevent abuse.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from logger import logger

# ========== Rate Limiter Configuration ==========

def get_client_ip(request: Request) -> str:
    """
    Get client IP address, handling proxies.
    Checks X-Forwarded-For header first for reverse proxy scenarios.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return get_remote_address(request)


# Initialize the limiter
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["200 per minute"],  # Default limit for all endpoints
    enabled=True,
    strategy="fixed-window"
)


# ========== Rate Limit Configurations ==========

# Standard rate limits for different endpoint types
RATE_LIMITS = {
    # Read operations - higher limits
    "gallery_read": "120/minute",
    "gallery_all": "30/minute",  # Lower for heavy endpoint
    "search": "60/minute",
    "tags": "60/minute",
    
    # Write operations - lower limits
    "upload": "10/minute",
    "delete": "20/minute",
    
    # Auth operations - prevent brute force
    "login": "10/minute",
    "register": "5/minute",
    "password_reset": "5/minute",
    
    # Profile operations
    "profile_read": "60/minute",
    "profile_update": "30/minute",
}


# ========== Error Handler ==========

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    logger.warning(f"Rate limit exceeded for {get_client_ip(request)}: {request.url.path}")
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": f"Rate limit exceeded. Please try again later.",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "Rate limit exceeded"
        },
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": str(exc.detail) if hasattr(exc, 'detail') else "unknown"
        }
    )


# ========== Utility Functions ==========

def get_rate_limit(endpoint_type: str) -> str:
    """Get rate limit string for an endpoint type."""
    return RATE_LIMITS.get(endpoint_type, "60/minute")
