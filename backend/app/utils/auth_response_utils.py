"""
Helper utility for creating login responses.
Separated to avoid circular imports between AuthService and Utils.
"""

from typing import TYPE_CHECKING, Any

from fastapi import Request, Response

from app.schemas.auth import LoginResponse
from app.schemas.user import UserResponse
from app.utils.auth_utils import get_client_info, set_refresh_cookie

if TYPE_CHECKING:
    from app.services.auth_service import AuthService  # noqa: F401


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def create_login_response(
    auth_service: "AuthService",
    user: dict[str, Any] | Any,
    request: Request,
    response: Response,
    include_refresh_cookie: bool = True,
) -> LoginResponse:
    """
    Helper to create standardized login response with tokens.
    Handles user object or dictionary.
    """
    ip, ua = get_client_info(request)

    user_id = str(_get(user, "id"))
    role = _get(user, "role", "user")
    permissions = _get(user, "permissions", [])
    tier = "pro" if _get(user, "is_pro", False) else "free"

    # Generate tokens
    access_token = auth_service.create_access_token(user_id, role=role, permissions=permissions, tier=tier)
    refresh_token = auth_service.create_refresh_token(user_id, ip, ua)

    if include_refresh_cookie:
        set_refresh_cookie(response, refresh_token)

    user_response = UserResponse(
        id=_get(user, "id"),
        email=_get(user, "email", ""),
        name=_get(user, "name", ""),
        picture=_get(user, "picture", ""),
        bio=_get(user, "bio"),
        created_at=_get(user, "created_at"),
        google_id=_get(user, "google_id"),
        role=role,
        permissions=permissions,
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",  # nosec S106
        user=user_response,
    )
