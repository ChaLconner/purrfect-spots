import uuid
from typing import Any, cast

import structlog
from sqlalchemy import text

from schemas.auth import LoginResponse
from schemas.user import UserResponse
from services.auth.base_mixin import AuthBaseMixin
from services.google_auth_service import google_auth_service

logger = structlog.get_logger(__name__)


class AuthOAuthMixin(AuthBaseMixin):
    """Mixin for OAuth-related operations (Google)."""

    # Will be assigned in the main class
    user_service: Any

    def create_access_token(
        self,
        user_id: str,
        user_data: dict[str, Any] | None = None,
        role: str = "user",
        permissions: list[str] | None = None,
    ) -> str:
        raise NotImplementedError

    def create_refresh_token(self, user_id: str, ip: str | None = None, user_agent: str | None = None) -> str:
        raise NotImplementedError

    async def _find_or_create_google_user(self, user_info: dict[str, Any], google_id: str) -> dict[str, Any]:
        """Find existing user by Google ID or email to handle account linking (Async)"""
        email = user_info.get("email")
        user_id = None

        try:
            if self.db:
                user_id = await self._find_user_sql(google_id, email)
            else:
                user_id = await self._find_user_supabase(google_id, email)
        except Exception as e:
            logger.debug("Identity check unsuccessful: %s", e)

        if not user_id:
            user_id = str(uuid.uuid4())

        return {
            "id": user_id,
            "sub": user_id,
            "google_id": google_id,
            "email": email,
            "name": user_info.get("name", ""),
            "picture": user_info.get("picture", ""),
        }

    async def _find_user_sql(self, google_id: str, email: str | None) -> str | None:
        """Find user by Google ID or email using SQLAlchemy."""
        if not self.db:
            return None
        db_session = self.db
        query = text("SELECT id FROM users WHERE google_id = :g_id")
        result = await db_session.execute(query, {"g_id": google_id})
        row = result.fetchone()
        if row:
            return cast(str | None, row[0])

        if email:
            query_email = text("SELECT id FROM users WHERE email = :email")
            result_email = await db_session.execute(query_email, {"email": email})
            row_email = result_email.fetchone()
            if row_email:
                user_id = cast(str, row_email[0])
                update_query = text("UPDATE users SET google_id = :g_id WHERE id = :u_id")
                await db_session.execute(update_query, {"g_id": google_id, "u_id": user_id})
                await db_session.commit()
                return user_id
        return None

    async def _find_user_supabase(self, google_id: str, email: str | None) -> str | None:
        """Find user by Google ID or email using Supabase."""
        admin = await self._get_admin_client()
        res = await admin.table("users").select("id").eq("google_id", google_id).execute()
        if res.data:
            return cast(str | None, res.data[0]["id"])

        if email:
            res_email = await admin.table("users").select("id").eq("email", email).execute()
            if res_email.data:
                user_id = cast(str, res_email.data[0]["id"])
                await admin.table("users").update({"google_id": google_id}).eq("id", user_id).execute()
                return user_id
        return None

    def verify_google_token(self, token: str) -> dict[str, Any]:
        """Verify Google OAuth token"""
        return google_auth_service.verify_google_token(token)

    async def exchange_google_code(
        self, code: str, code_verifier: str, redirect_uri: str, ip: str | None = None, user_agent: str | None = None
    ) -> LoginResponse:
        """Exchange Google authorization code for access token (Async)"""
        try:
            result = await google_auth_service.exchange_google_code(code, code_verifier, redirect_uri)
            user_info = result["user_info"]
            google_id = user_info["google_id"]

            user_data = await self._find_or_create_google_user(user_info, google_id)
            user = await self.user_service.create_or_get_user(user_data)
            if user.banned_at:
                raise PermissionError("Account suspended")

            jwt_token = self.create_access_token(user.id, user_data, role=user.role, permissions=user.permissions)
            refresh_token = self.create_refresh_token(user.id, ip, user_agent)

            return LoginResponse(
                access_token=jwt_token,
                token_type="bearer",
                user=UserResponse(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    picture=user.picture,
                    bio=user.bio,
                    created_at=user.created_at,
                    google_id=user.google_id,
                ),
                refresh_token=refresh_token,
            )
        except PermissionError:
            raise
        except Exception as e:
            logger.error("[OAuth] Exchange exception: %s", e)
            raise ValueError(f"Code exchange failed: {e}")
