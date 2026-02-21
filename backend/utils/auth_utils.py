import logging
from typing import Any, Dict

import jwt

from config import config

# Set up logging
logger = logging.getLogger(__name__)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.

    Tries decoding with:
    1. SUPABASE_KEY (if available) - for Supabase tokens
    2. JWT_SECRET (if available) - for custom tokens

    Args:
        token: The JWT token string

    Returns:
        dict: The decoded token claims

    Raises:
        ValueError: If token is invalid or expired
    """
    if not token:
        raise ValueError("Token is missing")

    errors: list[str] = []



    # Decode with Custom JWT Secret (Standard)
    # This secret must match the one used to sign the token (e.g. Supabase Project Secret)
    if config.JWT_SECRET:
        try:
            # We don't enforce audience here by default as Supabase tokens might vary
            # or be used in contexts where audience check is handled elsewhere.
            # However, PyJWT verifies 'aud' claim presence by default.
            return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            errors.append(f"JWT secret validation failed: {e}")

    logger.warning(f"Failed to decode token: {errors}")
    raise ValueError("Invalid token")


def get_client_info(request: Any) -> tuple[str, str]:
    """Extract client IP and User-Agent from request"""
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # Check for proxies
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        ip = x_real_ip
    else:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()

    return ip, user_agent


def set_refresh_cookie(response: Any, refresh_token: str) -> None:
    """Set HttpOnly Secure cookie for refresh token"""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=config.is_production(),
        samesite="lax",
        max_age=config.JWT_REFRESH_EXPIRATION_DAYS * 86400,
        path="/",
    )
