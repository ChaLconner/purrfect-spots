from typing import Any

import structlog
from schemas.user import User
from services.user.base_mixin import UserBaseMixin

logger = structlog.get_logger(__name__)


class UserReadMixin(UserBaseMixin):
    """Mixin for user-related read operations."""

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID from database with Role and Permissions (Async)"""
        try:
            from typing import cast

            query_str = f"{self.USER_COLUMNS}, roles(name, role_permissions(permissions(code)))"
            admin = await self._get_admin_client()
            supa_res = await admin.table("users").select(query_str).eq("id", user_id).execute()
            if supa_res.data:
                data_list = cast(list[dict[str, Any]], supa_res.data)
                return self._map_db_user_to_model(data_list[0])
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by ID: %s", e)
            return None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email from database (Async)"""
        try:
            from typing import cast

            admin = await self._get_admin_client()
            supa_res = await admin.table("users").select(self.USER_COLUMNS).eq("email", email).maybe_single().execute()
            return cast(dict[str, Any] | None, supa_res.data) if supa_res and supa_res.data else None
        except Exception as e:
            logger.debug("Failed to retrieve profile by email: %s", e)
            return None

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username from database (Async)"""
        try:
            from typing import cast

            admin = await self._get_admin_client()
            query_str = f"{self.USER_COLUMNS}, roles(name, role_permissions(permissions(code)))"
            supa_res = await admin.table("users").select(query_str).ilike("username", username).maybe_single().execute()
            if supa_res and supa_res.data:
                return self._map_db_user_to_model(cast(dict[str, Any], supa_res.data))
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by username: %s", e)
            return None
