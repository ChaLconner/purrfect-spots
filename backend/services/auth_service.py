from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from config import config
from services.auth.oauth_mixin import AuthOAuthMixin
from services.auth.password_mixin import AuthPasswordMixin
from services.auth.token_mixin import AuthTokenMixin
from services.user_service import UserService

if TYPE_CHECKING:
    from schemas.user import User

logger = structlog.get_logger(__name__)


class AuthService(AuthTokenMixin, AuthOAuthMixin, AuthPasswordMixin):
    """
    Authentication service using Async Supabase Client.
    Refactored to several mixins for better maintainability.
    """

    def __init__(
        self,
        supabase_client: AClient,
        supabase_admin: AClient | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        self._supabase = supabase_client
        self._supabase_admin = supabase_admin
        self._db = db
        self.user_service = UserService(supabase_client, supabase_admin, db=db)
        self.jwt_secret = config.JWT_SECRET
        self.jwt_algorithm = config.JWT_ALGORITHM
        self.jwt_expiration_hours = config.JWT_ACCESS_EXPIRATION_HOURS

        if not self.jwt_secret:
            raise ValueError("JWT_SECRET is not configured")

    @property
    def supabase_client(self) -> AClient:
        return self._supabase

    @property
    def supabase_admin(self) -> AClient | None:
        return self._supabase_admin

    @property
    def db(self) -> AsyncSession | None:
        return self._db

    # Delegation methods to UserService
    async def create_or_get_user(self, user_data: dict[str, Any]) -> "User":
        return await self.user_service.create_or_get_user(user_data)

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any] | None:
        return await self.user_service.authenticate_user(email, password)

    async def create_user_with_password(self, email: str, password: str, name: str) -> dict[str, Any]:
        return await self.user_service.create_unverified_user(email, password, name)

    async def get_user_by_email_unverified(self, email: str) -> dict[str, Any] | None:
        return await self.user_service.get_user_by_email(email)

    async def get_user_by_id(self, user_id: str) -> "User | None":
        return await self.user_service.get_user_by_id(user_id)

    async def update_user_profile(
        self, user_id: str, update_data: dict[str, Any], jwt_token: str | None = None
    ) -> dict[str, Any]:
        return await self.user_service.update_user_profile(user_id, update_data, jwt_token)

    async def confirm_user_email(self, email: str) -> bool:
        """Confirm user email via Admin Client (Async)"""
        try:
            admin = await self._get_admin_client()
            if self.db:
                from sqlalchemy import text

                query = text("SELECT id FROM users WHERE email = :email")
                result = await self.db.execute(query, {"email": email})
                row = result.fetchone()
                if not row:
                    return False
                user_id = row[0]
            else:
                res = await admin.table("users").select("id").eq("email", email).execute()
                if not res.data:
                    return False
                user_id = res.data[0]["id"]

            await admin.auth.admin.update_user_by_id(user_id, {"email_confirm": True})
            return True
        except Exception as e:
            logger.error("Failed to confirm user email: %s", e)
            return False
