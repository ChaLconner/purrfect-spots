from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.user import User
from supabase import AClient
from utils.supabase_client import get_async_supabase_admin_client

logger = structlog.get_logger(__name__)


class UserBaseMixin:
    """Base mixin for user service containing shared state and helpers."""

    _cached_user_role_id: str | None = None
    SERVICE_SUPABASE_AUTH = "Supabase Auth"
    # Centralized user column selection to avoid over-fetching
    USER_COLUMNS = "id, email, name, username, picture, bio, google_id, treat_balance, total_treats_received, is_pro, role_id, created_at, updated_at, banned_at"

    def _prefixed_user_columns(self, prefix: str) -> str:
        """Helper to prefix user columns for JOIN queries."""
        return ", ".join([f"{prefix}.{c}" for c in self.USER_COLUMNS.split(", ")])

    @property
    def supabase(self) -> AClient:
        raise NotImplementedError

    @property
    def supabase_admin(self) -> AClient | None:
        raise NotImplementedError

    @property
    def db(self) -> AsyncSession | None:
        raise NotImplementedError

    async def _get_admin_client(self) -> AClient:
        if self.supabase_admin:
            return self.supabase_admin
        return await get_async_supabase_admin_client()

    async def _get_user_role_id(self) -> str | None:
        """Get the ID of the 'user' role from the roles table (Async)"""
        if UserBaseMixin._cached_user_role_id:
            return UserBaseMixin._cached_user_role_id

        try:
            if self.db:
                query = text("SELECT id FROM roles WHERE name = 'user' LIMIT 1")
                result = await self.db.execute(query)
                row = result.fetchone()
                if row:
                    UserBaseMixin._cached_user_role_id = str(row[0])
                    return UserBaseMixin._cached_user_role_id
            else:
                from typing import cast

                admin = await self._get_admin_client()
                res = await admin.table("roles").select("id").eq("name", "user").execute()
                if res.data:
                    data = cast(list[dict[str, Any]], res.data)
                    UserBaseMixin._cached_user_role_id = cast(str, data[0]["id"])
                    return UserBaseMixin._cached_user_role_id
        except Exception as e:
            logger.warning("Failed to fetch default user role ID: %s", e)
        return None

    def _map_db_user_to_model(self, data: dict[str, Any]) -> User:
        """Map DB result with nested role/permissions to User model"""
        from typing import cast

        permissions: list[str] = []

        role_data = data.get("roles")
        if role_data and isinstance(role_data, dict):
            role_dict = cast(dict[str, Any], role_data)
            rps = cast(list[dict[str, Any]], role_dict.get("role_permissions", []))
            for rp in rps:
                perm = cast(dict[str, Any] | None, rp.get("permissions"))
                if perm and isinstance(perm, dict) and "code" in perm:
                    permissions.append(cast(str, perm["code"]))

        user_fields = data.copy()
        if isinstance(role_data, dict) and "name" in role_data:
            user_fields["role"] = role_data["name"]

        user_fields.pop("roles", None)

        return User(**user_fields, permissions=permissions)
