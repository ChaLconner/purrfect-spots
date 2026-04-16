from typing import Any, cast

from sqlalchemy import bindparam, column, func, table, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

import structlog  # type: ignore[import-untyped, unused-ignore]
from schemas.user import User
from services.user.base_mixin import UserBaseMixin
from utils.datetime_utils import utc_now_iso
from utils.exceptions import ExternalServiceError, PurrfectSpotsException

logger = structlog.get_logger(__name__)


class UserProfileMixin(UserBaseMixin):
    """Mixin for user profile management and synchronization."""

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

    async def create_or_get_user(self, user_data: dict[str, Any]) -> User:
        """Create new user or get existing user from database for OAuth (Async)"""
        try:
            user_id = user_data.get("id") or user_data.get("sub")
            if not user_id:
                raise ValueError("Missing user_id (sub) in user_data")

            user_record = self._prepare_user_record(user_data, user_id)

            if self.db:
                try:
                    await self._upsert_user_sql(user_id, user_record)
                except Exception as e:
                    await self.db.rollback()
                    logger.warning(f"SQL _upsert_user failed, falling back to Supabase: {e}")
                    await self._upsert_user_supabase(user_id, user_record)
            else:
                await self._upsert_user_supabase(user_id, user_record)

            # Need to use the main class's get_user_by_id (inherited via mixins)
            user = cast(User, await self.get_user_by_id(user_id))
            if not user:
                raise ExternalServiceError("Failed to retrieve user after creation", service="Supabase Database")
            return user
        except Exception as e:
            if self.db:
                await self.db.rollback()
            raise ExternalServiceError(f"Database error: {e!s}", service="Supabase Database")

    def _prepare_user_record(self, user_data: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Prepare user record for upsert."""
        return {
            "id": user_id,
            "email": user_data.get("email", ""),
            "name": user_data.get("name", ""),
            "picture": user_data.get("picture", ""),
            "google_id": user_data.get("google_id"),
            "bio": None,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }

    async def _upsert_user_sql(self, user_id: str, user_record: dict[str, Any]) -> None:
        """Upsert user using SQLAlchemy."""
        if not self.db:
            return

        # Check for existing role
        check_query = text("SELECT role_id FROM users WHERE id = :u_id LIMIT 1")
        check_res = await self.db.execute(check_query, {"u_id": user_id})
        check_row = check_res.fetchone()

        if not check_row or not check_row[0]:
            user_record["role_id"] = await self._get_user_role_id()

        allowed_columns = {"id", "email", "name", "picture", "google_id", "bio", "created_at", "updated_at", "role_id"}
        columns_list = [c for c in user_record if c in allowed_columns]
        update_cols = ["email", "name", "picture", "google_id", "updated_at"]
        users = self._users_table()
        insert_values = {key: user_record[key] for key in columns_list}
        insert_stmt = pg_insert(users).values(insert_values)
        upsert_query = insert_stmt.on_conflict_do_update(
            index_elements=[users.c.id],
            set_={column_name: getattr(insert_stmt.excluded, column_name) for column_name in update_cols},
        )

        await self.db.execute(upsert_query)
        await self.db.commit()

    async def _upsert_user_supabase(self, user_id: str, user_record: dict[str, Any]) -> None:
        """Upsert user using Supabase."""
        admin = await self._get_admin_client()
        existing_check = await admin.table("users").select("role_id").eq("id", user_id).execute()
        existing_data = cast(list[dict[str, Any]], existing_check.data)
        if not existing_data or not existing_data[0].get("role_id"):
            user_record["role_id"] = await self._get_user_role_id()

        await admin.table("users").upsert(user_record, on_conflict="id").execute()

    async def update_user_profile(
        self, user_id: str, update_data: dict[str, Any], jwt_token: str | None = None
    ) -> dict[str, Any]:
        """Update user profile (Async)"""
        try:
            if self.db:
                try:
                    safe_cols = [k for k in update_data if k in {"name", "username", "bio", "picture"}]
                    if not safe_cols:
                        raise ValueError("No valid profile fields provided")
                    users = self._users_table()
                    update_values: dict[str, Any] = {key: bindparam(key) for key in safe_cols}
                    update_values["updated_at"] = func.now()
                    query = (
                        update(users)
                        .where(users.c.id == bindparam("u_id"))
                        .values(update_values)
                        .returning(
                            users.c.id,
                            users.c.email,
                            users.c.name,
                            users.c.username,
                            users.c.picture,
                            users.c.bio,
                            users.c.google_id,
                            users.c.treat_balance,
                            users.c.total_treats_received,
                            users.c.is_pro,
                            users.c.role_id,
                            users.c.created_at,
                            users.c.updated_at,
                            users.c.banned_at,
                        )
                    )
                    params = {**{k: v for k, v in update_data.items() if k in safe_cols}, "u_id": user_id}
                    db_res = await self.db.execute(query, params)
                    row = db_res.fetchone()
                    if row:
                        await self.db.commit()
                        return dict(row._mapping)
                except Exception as e:
                    await self.db.rollback()
                    logger.warning(f"SQL update_user_profile failed, falling back to Supabase: {e}")

            admin = await self._get_admin_client()
            supa_res = await admin.table("users").update(update_data).eq("id", user_id).execute()
            if not supa_res or not supa_res.data:
                raise ValueError("User not found or update failed")
            data_list = cast(list[dict[str, Any]], supa_res.data)
            return data_list[0]
        except Exception as e:
            if self.db:
                await self.db.rollback()
            raise PurrfectSpotsException(f"Failed to update profile: {e!s}")
