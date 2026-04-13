from typing import Any, cast

import structlog  # type: ignore[import-untyped, unused-ignore]

from schemas.user import User
from services.password_service import password_service
from services.user.base_mixin import UserBaseMixin
from utils.exceptions import ConflictError, ExternalServiceError, PurrfectSpotsException

logger = structlog.get_logger(__name__)


class UserAuthMixin(UserBaseMixin):
    """Mixin for user-related authentication and creation operations."""

    async def create_unverified_user(self, email: str, password: str, name: str) -> dict[str, Any]:
        """Create a new user without sending a confirmation email (Async)"""
        try:
            is_valid, error = await password_service.validate_new_password(password)
            if not is_valid:
                raise ValueError(error or "Password does not meet security requirements")

            admin = await self._get_admin_client()
            res = await admin.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": False,
                    "user_metadata": {"name": name, "full_name": name},
                }
            )

            if not res or not res.user:
                raise ExternalServiceError("Failed to create user", service=self.SERVICE_SUPABASE_AUTH)

            user = res.user
            return {
                "id": user.id,
                "email": user.email,
                "name": name,
                "created_at": user.created_at,
                "picture": "",
                "bio": None,
                "verification_required": True,
            }
        except Exception as e:
            msg = str(e)
            if "password" in msg.lower():
                raise ValueError(msg)
            if any(term in msg.lower() for term in ["already registered", "unique constraint"]):
                raise ConflictError("Email already registered")
            logger.error("Failed to create unverified account: %s", msg)
            raise PurrfectSpotsException("Failed to create user")

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any] | None:
        """Authenticate user using Supabase Auth (Async)"""
        try:
            res = await self.supabase.auth.sign_in_with_password({"email": email, "password": password})
            if not res:
                logger.error("Supabase returned None result for login", email=email)
                return None
            if res.user and res.session:
                # Need to use the main class's get_user_by_id (inherited via mixins)
                get_user = getattr(self, "get_user_by_id", None)
                if get_user is None:
                    logger.error("get_user_by_id is missing from UserService")
                    return None
                user = cast(User, await get_user(res.user.id))
                if user:
                    user_dict = user.model_dump()
                    user_dict.update(
                        {
                            "access_token": res.session.access_token,
                            "refresh_token": res.session.refresh_token,
                        }
                    )
                    return user_dict

                return {
                    "id": res.user.id,
                    "email": res.user.email,
                    "name": res.user.user_metadata.get("name", ""),
                    "picture": res.user.user_metadata.get("avatar_url", ""),
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                    "created_at": res.user.created_at,
                    "permissions": [],
                    "role": "user",
                }
            return None
        except Exception as e:
            logger.error("Authentication failure", error=str(e), email=email)
            return None
