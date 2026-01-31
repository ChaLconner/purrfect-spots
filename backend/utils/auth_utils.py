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
    )


from schemas.auth import LoginResponse
from services.auth_service import AuthService
from user_models.user import UserResponse


async def create_login_response(
    auth_service: AuthService, user, request: Request, response: Response, include_refresh_cookie: bool = True
) -> LoginResponse:
    """
    Unified helper to create tokens, set cookies, and return LoginResponse.

    Args:
        auth_service: AuthService instance
        user: User object (must have id, email, name, picture, bio, created_at)
        request: FastAPI Request
        response: FastAPI Response
        include_refresh_cookie: Whether to set the refresh token cookie

    Returns:
        LoginResponse model
    """
    ip, ua = get_client_info(request)

    # Create tokens
    # Note: user might be a dict or object depending on source, but AuthService expects ID for tokens
    user_id = getattr(user, "id", user.get("id") if isinstance(user, dict) else str(user))

    # Prepare token extra claims if needed (usually just standard claims)
    access_token = auth_service.create_access_token(user_id)
    refresh_token = auth_service.create_refresh_token(user_id, ip, ua)

    if include_refresh_cookie:
        set_refresh_cookie(response, refresh_token)

    # Standardize user object for response
    # Handle both dict and object (Pydantic model)
    def get_attr(obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",  # nosec B106
        user=UserResponse(
            id=user_id,
            email=get_attr(user, "email"),
            name=get_attr(user, "name"),
            picture=get_attr(user, "picture"),
            bio=get_attr(user, "bio"),
            created_at=get_attr(user, "created_at"),
        ),
        refresh_token=refresh_token,
    )
