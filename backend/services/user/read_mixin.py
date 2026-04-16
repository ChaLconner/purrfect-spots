from typing import Any

from sqlalchemy import column, select, table

import structlog
from schemas.user import User
from services.user.base_mixin import UserBaseMixin

logger = structlog.get_logger(__name__)


class UserReadMixin(UserBaseMixin):
    """Mixin for user-related read operations."""

    @staticmethod
    def _users_table() -> Any:
        return table(
            "users",
            column("id"),
            column("email"),
            column("name"),
            column("username"),
            column("picture"),
            column("bio"),
            column("google_id"),
            column("treat_balance"),
            column("total_treats_received"),
            column("is_pro"),
            column("role_id"),
            column("created_at"),
            column("updated_at"),
            column("banned_at"),
        )

    @staticmethod
    def _roles_table() -> Any:
        return table("roles", column("id"), column("name"))

    @staticmethod
    def _permissions_table() -> Any:
        return table("permissions", column("id"), column("code"))

    @staticmethod
    def _role_permissions_table() -> Any:
        return table("role_permissions", column("role_id"), column("permission_id"))

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID from database with Role and Permissions (Async)"""
        try:
            if self.db:
                try:
                    users = self._users_table()
                    roles = self._roles_table()
                    user_query = (
                        select(*users.c, roles.c.name.label("role_name"))
                        .select_from(users.outerjoin(roles, users.c.role_id == roles.c.id))
                        .where(users.c.id == user_id)
                        .limit(1)
                    )
                    db_res = await self.db.execute(user_query)
                    row = db_res.fetchone()
                    if row:
                        permissions = await self._get_permissions_for_user_id(user_id)
                        data = dict(row._mapping)
                        user_data = data.copy()
                        user_data["role"] = data.get("role_name")
                        return User(**user_data, permissions=permissions)
                except Exception as e:
                    logger.warning("SQL get_user_by_id failed, falling back to Supabase: %s", e)

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
            if self.db:
                try:
                    users = self._users_table()
                    query = select(*users.c).where(users.c.email == email).limit(1)
                    db_res = await self.db.execute(query)
                    row = db_res.fetchone()
                    if row:
                        return dict(row._mapping)
                except Exception as e:
                    logger.warning("SQL get_user_by_email failed, falling back to Supabase: %s", e)

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
            if self.db:
                try:
                    users = self._users_table()
                    roles = self._roles_table()
                    lowered_username = username.lower()
                    query = (
                        select(*users.c, roles.c.name.label("role_name"))
                        .select_from(users.outerjoin(roles, users.c.role_id == roles.c.id))
                        .where(users.c.username.ilike(lowered_username))
                        .limit(1)
                    )
                    result = await self.db.execute(query)
                    row = result.fetchone()
                    if row:
                        permissions = await self._get_permissions_for_username(username)
                        data = dict(row._mapping)
                        user_data = data.copy()
                        user_data["role"] = data.get("role_name")
                        return User(**user_data, permissions=permissions)
                except Exception as e:
                    logger.warning("SQL get_user_by_username failed, falling back to Supabase: %s", e)

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

    async def _get_permissions_for_user_id(self, user_id: str) -> list[str]:
        if not self.db:
            return []
        permissions = self._permissions_table()
        role_permissions = self._role_permissions_table()
        users = self._users_table()
        perm_query = (
            select(permissions.c.code)
            .select_from(
                permissions.join(role_permissions, permissions.c.id == role_permissions.c.permission_id).join(
                    users, role_permissions.c.role_id == users.c.role_id
                )
            )
            .where(users.c.id == user_id)
        )
        perm_db_res = await self.db.execute(perm_query)
        return [str(row[0]) for row in perm_db_res]

    async def _get_permissions_for_username(self, username: str) -> list[str]:
        if not self.db:
            return []
        permissions = self._permissions_table()
        role_permissions = self._role_permissions_table()
        users = self._users_table()
        perm_query = (
            select(permissions.c.code)
            .select_from(
                permissions.join(role_permissions, permissions.c.id == role_permissions.c.permission_id).join(
                    users, role_permissions.c.role_id == users.c.role_id
                )
            )
            .where(users.c.username.ilike(username.lower()))
        )
        perm_res = await self.db.execute(perm_query)
        return [str(row[0]) for row in perm_res]
