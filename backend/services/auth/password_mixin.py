from typing import Any, cast

import structlog
from sqlalchemy import text
from supabase import acreate_client

from config import config
from services.auth.base_mixin import AuthBaseMixin
from services.email_service import email_service
from services.password_service import password_service
from services.token_service import get_token_service
from utils.datetime_utils import utc_now

logger = structlog.get_logger(__name__)


class AuthPasswordMixin(AuthBaseMixin):
    """Mixin for password management (reset/change)."""

    async def create_password_reset_token(self, email: str) -> bool:
        """Request password reset via Supabase Auth (Async)."""
        try:
            params = {
                "type": "recovery",
                "email": email,
                "options": {"redirect_to": f"{config.FRONTEND_URL}/reset-password"},
            }
            admin = await self._get_admin_client()
            res = await admin.auth.admin.generate_link(cast(Any, params))

            if not res:
                return False

            properties = getattr(res, "properties", None)
            if not properties:
                return False

            action_link = getattr(properties, "action_link", None)
            if not action_link:
                return False

            return email_service.send_reset_email(email, action_link)
        except Exception:
            logger.error("Failed to process password reset")
        return True

    async def reset_password(self, access_token: str, new_password: str) -> bool:
        """Reset password using Supabase Auth session (Async)"""
        try:
            is_valid, error = await password_service.validate_new_password(new_password)
            if not is_valid:
                raise ValueError(error)

            temp_client = await acreate_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            temp_client.postgrest.auth(access_token)
            user_res = await temp_client.auth.get_user(access_token)
            if not user_res or not user_res.user:
                raise ValueError("Invalid user session")

            user_id = user_res.user.id
            await temp_client.auth.update_user({"password": new_password})

            if self.db:
                query = text("UPDATE users SET updated_at = :now WHERE id = :u_id")
                await self.db.execute(query, {"now": utc_now().isoformat(), "u_id": user_id})
                await self.db.commit()
            else:
                admin = await self._get_admin_client()
                await admin.table("users").update({"updated_at": utc_now().isoformat()}).eq("id", user_id).execute()

            if user_res.user.email:
                ts = await get_token_service()
                await ts.blacklist_all_user_tokens(user_id, reason="password_reset")
                email_service.send_password_changed_email(user_res.user.email)
            return True
        except Exception as e:
            logger.error(f"Reset password failed: {e}")
            return False

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change password (Async)"""
        try:
            # Need user_service
            user = await self.user_service.get_user_by_id(user_id)  # type: ignore
            if not user or user.google_id:
                return False

            is_valid, error = await password_service.validate_new_password(new_password)
            if not is_valid:
                raise ValueError(error)

            auth_test = await self.user_service.authenticate_user(user.email, current_password)  # type: ignore
            if not auth_test:
                raise ValueError("Incorrect current password")

            admin = await self._get_admin_client()
            await admin.auth.admin.update_user_by_id(user_id, {"password": new_password})

            ts = await get_token_service()
            await ts.blacklist_all_user_tokens(user_id, reason="password_change")
            email_service.send_password_changed_email(user.email)
            return True
        except Exception as e:
            logger.error(f"Change password failed: {e}")
            raise e
