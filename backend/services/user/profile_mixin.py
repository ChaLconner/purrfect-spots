from typing import Any, cast

import structlog
from sqlalchemy import text

from schemas.user import User
from services.user.base_mixin import UserBaseMixin
from utils.datetime_utils import utc_now_iso
from utils.exceptions import ExternalServiceError, PurrfectSpotsException

logger = structlog.get_logger(__name__)


class UserProfileMixin(UserBaseMixin):
    """Mixin for user profile management and synchronization."""

    async def create_or_get_user(self, user_data: dict[str, Any]) -> User:
        """Create new user or get existing user from database for OAuth (Async)"""
        try:
            user_id = user_data.get("id") or user_data.get("sub")
            if not user_id:
                raise ValueError("Missing user_id (sub) in user_data")

            user_record = self._prepare_user_record(user_data, user_id)

            if self.db:
                await self._upsert_user_sql(user_id, user_record)
            else:
                await self._upsert_user_supabase(user_id, user_record)

            # Need to use the main class's get_user_by_id (inherited via mixins)
            user = await self.get_user_by_id(user_id)  # type: ignore
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
        columns = ", ".join(columns_list)
        placeholders = ", ".join([f":{c}" for c in columns_list])
        update_cols = ["email", "name", "picture", "google_id", "updated_at"]
        update_stmt = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        upsert_query = text(
            f"INSERT INTO users ({columns}) VALUES ({placeholders}) "  # noqa: S608
            f"ON CONFLICT (id) DO UPDATE SET {update_stmt}"
        )

        await self.db.execute(upsert_query, {k: user_record[k] for k in columns_list})
        await self.db.commit()

    async def _upsert_user_supabase(self, user_id: str, user_record: dict[str, Any]) -> None:
        """Upsert user using Supabase."""
        admin = await self._get_admin_client()
        existing_check = await admin.table("users").select("role_id").eq("id", user_id).execute()

        if not existing_check.data or not existing_check.data[0].get("role_id"):
            user_record["role_id"] = await self._get_user_role_id()

        await admin.table("users").upsert(user_record, on_conflict="id").execute()

    async def update_user_profile(
        self, user_id: str, update_data: dict[str, Any], jwt_token: str | None = None
    ) -> dict[str, Any]:
        """Update user profile (Async)"""
        try:
            if self.db:
                safe_cols = [k for k in update_data if k in {"name", "username", "bio", "picture"}]
                cols = ", ".join([f"{k} = :{k}" for k in safe_cols])
                query = text(f"UPDATE users SET {cols}, updated_at = NOW() WHERE id = :u_id RETURNING *")  # noqa: S608
                params = {**{k: v for k, v in update_data.items() if k in safe_cols}, "u_id": user_id}
                db_res = await self.db.execute(query, params)
                row = db_res.fetchone()
                if not row:
                    raise ValueError("User not found or update failed")
                await self.db.commit()
                return dict(row._mapping)
            admin = await self._get_admin_client()
            supa_res = await admin.table("users").update(update_data).eq("id", user_id).execute()
            if not supa_res or not supa_res.data:
                raise ValueError("User not found or update failed")
            return cast(dict[str, Any], supa_res.data[0])
        except Exception as e:
            if self.db:
                await self.db.rollback()
            raise PurrfectSpotsException(f"Failed to update profile: {e!s}")
