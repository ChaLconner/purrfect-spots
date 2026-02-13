"""
Helper utility for creating login responses.
Separated to avoid circular imports between AuthService and Utils.
"""
from typing import TYPE_CHECKING, Any, Dict, Union

from fastapi import Request, Response

from schemas.auth import LoginResponse
from user_models.user import UserResponse
from utils.auth_utils import get_client_info, set_refresh_cookie

if TYPE_CHECKING:
    from services.auth_service import AuthService  # noqa: F401


def create_login_response(
    auth_service: "AuthService",
    user: Union[Dict[str, Any], Any],
    request: Request,
    response: Response,
    include_refresh_cookie: bool = True,
) -> LoginResponse:
    """
    Helper to create standardized login response with tokens.
    Handles user object or dictionary.
    """
    ip, ua = get_client_info(request)

    # normalizing user ID access (attrs vs dict)
    if isinstance(user, dict):
        user_id = str(user.get("id"))
        role = user.get("role", "user")
    else:
        user_id = str(user.id)
        role = getattr(user, "role", "user")

    # Generate tokens
    # Note: user data is optional if not updating claims
    access_token = auth_service.create_access_token(user_id, role=role)
    refresh_token = auth_service.create_refresh_token(user_id, ip, ua)

    if include_refresh_cookie:
        set_refresh_cookie(response, refresh_token)

    # Standardize User object for response
    if isinstance(user, dict):
        user_response = UserResponse(
            id=user["id"],
            email=user.get("email", ""),
            name=user.get("name", ""),
            picture=user.get("picture", ""),
            bio=user.get("bio"),
            created_at=user.get("created_at"),
            google_id=user.get("google_id"),
        )
    else:
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            bio=user.bio,
            created_at=user.created_at,
            google_id=user.google_id,
        )

    return LoginResponse(
        access_token=access_token, token_type="bearer", user=user_response, refresh_token=refresh_token  # nosec B106
    )
