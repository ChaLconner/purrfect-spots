"""
Authentication utility functions for common tasks across multiple auth routes.
"""

from fastapi import Request, Response

from config import config


def get_client_info(request: Request) -> tuple[str, str]:
    """
    Get client IP and User-Agent safely from request.
    Handles proxy headers (X-Forwarded-For) if present.

    Returns:
        tuple[str, str]: (ip_address, user_agent)
    """
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # Check X-Forwarded-For if behind proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()

    return ip, user_agent


def set_refresh_cookie(response: Response, refresh_token: str):
    """
    Helper to set secure refresh token cookie.
    Sets HttpOnly, Secure (prod), SameSite=Lax.
    """
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=config.is_production(),
        samesite="lax",
        max_age=config.JWT_REFRESH_EXPIRATION_DAYS * 24 * 60 * 60,
    )
