import ipaddress
import logging
from functools import lru_cache
from typing import Any

import jwt

from config import config

# Set up logging
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _trusted_proxy_networks() -> tuple[ipaddress._BaseNetwork, ...]:
    """Parse configured trusted proxy hosts/CIDRs into network objects."""
    networks: list[ipaddress._BaseNetwork] = []
    for host in config.get_trusted_proxy_hosts():
        try:
            if "/" in host:
                networks.append(ipaddress.ip_network(host, strict=False))
            else:
                address = ipaddress.ip_address(host)
                prefix = 32 if address.version == 4 else 128
                networks.append(ipaddress.ip_network(f"{address}/{prefix}", strict=False))
        except ValueError:
            logger.warning("Ignoring invalid trusted proxy host: %s", host)
    return tuple(networks)


def _is_trusted_proxy_client(request: Any) -> bool:
    """Return True when the immediate client is a configured trusted proxy."""
    client = getattr(request, "client", None)
    client_host = getattr(client, "host", None)
    if not client_host:
        return False

    try:
        client_ip = ipaddress.ip_address(client_host)
    except ValueError:
        logger.warning("Ignoring invalid client host for proxy trust evaluation: %s", client_host)
        return False

    return any(client_ip in network for network in _trusted_proxy_networks())


def decode_token(token: str) -> dict[str, Any]:
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
    """
    Extract client IP and User-Agent from request.
    Checks X-Forwarded-For, X-Real-IP, and falls back to client.host.
    """
    ip = ""
    if _is_trusted_proxy_client(request):
        # Only trust forwarded headers when the immediate client is a known proxy.
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()

        if not ip:
            ip = request.headers.get("X-Real-IP", "")

    # Final fallback to request.client.host
    if not ip and request.client and getattr(request.client, "host", None):
        ip = request.client.host

    if not ip:
        ip = "unknown"

    user_agent = request.headers.get("user-agent", "")
    return ip, user_agent


def set_refresh_cookie(response: Any, refresh_token: str) -> None:
    """Set HttpOnly Secure cookie for refresh token"""
    is_prod = config.is_production()
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        # IMPORTANT: SameSite=None is required for cross-origin requests
        # (frontend on purrfect-spots.vercel.app, backend on purrfect-spots-backend.vercel.app)
        # SameSite=Lax blocks cookies on cross-origin POST requests, breaking token refresh.
        # SameSite=None requires Secure=True (enforced above in production).
        samesite="none" if is_prod else "lax",
        max_age=config.JWT_REFRESH_EXPIRATION_DAYS * 86400,
        path="/",
    )
