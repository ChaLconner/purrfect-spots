from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from schemas.user import User
from utils.supabase_client import get_async_supabase_admin_client

logger = structlog.get_logger(__name__)


class UserBaseMixin:
    """Base mixin for user service containing shared state and helpers."""

    _cached_user_role_id: str | None = None
    SERVICE_SUPABASE_AUTH = "Supabase Auth"

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
                admin = await self._get_admin_client()
                res = await admin.table("roles").select("id").eq("name", "user").execute()
                if res.data:
                    UserBaseMixin._cached_user_role_id = res.data[0]["id"]
                    return UserBaseMixin._cached_user_role_id
        except Exception as e:
            logger.warning("Failed to fetch default user role ID: %s", e)
        return None

    def _map_db_user_to_model(self, data: dict[str, Any]) -> User:
        """Map DB result with nested role/permissions to User model"""
        permissions: list[str] = []

        role_data = data.get("roles")
        if role_data and isinstance(role_data, dict):
            rps = role_data.get("role_permissions", [])
            for rp in rps:
                perm = rp.get("permissions")
                if perm and "code" in perm:
                    permissions.append(perm["code"])

        user_fields = data.copy()
        if isinstance(role_data, dict) and "name" in role_data:
            user_fields["role"] = role_data["name"]

        user_fields.pop("roles", None)

        return User(**user_fields, permissions=permissions)
