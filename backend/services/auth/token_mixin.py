import uuid
from datetime import datetime, timedelta
from typing import Any, cast

import jwt

import structlog
from config import config
from services.auth.base_mixin import AuthBaseMixin
from services.token_service import get_token_service
from utils.datetime_utils import utc_now

logger = structlog.get_logger(__name__)


class AuthTokenMixin(AuthBaseMixin):
    """Mixin for JWT access and refresh token management."""

    # Will be assigned in the main class
    jwt_expiration_hours: int

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token JTI is in blacklist (Async)."""
        if not jti:
            return False
        try:
            token_service = await get_token_service()
            return await token_service.is_blacklisted(jti=jti)
        except Exception as e:
            logger.error("Failed to check revocation status: %s", e)
            return True

    async def revoke_token(self, jti: str, user_id: str, expires_at: datetime) -> bool:
        """Add token to blacklist (Async)."""
        try:
            token_service = await get_token_service(self.db)
            return await token_service.blacklist_token(
                token=None, jti=jti, user_id=user_id, expires_at=expires_at, reason="logout"
            )
        except Exception as e:
            logger.error("Failed to revoke session: %s", e)
            return False

    def create_access_token(
        self,
        user_id: str,
        user_data: dict[str, Any] | None = None,
        role: str = "user",
        permissions: list[str] | None = None,
    ) -> str:
        """Create JWT access token."""
        expire = utc_now() + timedelta(hours=self.jwt_expiration_hours)
        jti = str(uuid.uuid4())
        to_encode: dict[str, Any] = {
            "user_id": user_id,
            "sub": user_id,
            "role": role,
            "permissions": permissions or [],
            "jti": jti,
            "exp": int(expire.timestamp()),
            "iat": int(utc_now().timestamp()),
        }
        if user_data:
            to_encode.update(
                {
                    "email": user_data.get("email", ""),
                    "user_metadata": {
                        "name": user_data.get("name", ""),
                        "avatar_url": user_data.get("picture", ""),
                        "provider_id": user_data.get("google_id"),
                    },
                    "app_metadata": {"provider": "google" if user_data.get("google_id") else "email"},
                }
            )
        return jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_access_token(self, token: str) -> str | None:
        """Verify access token and return user_id."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload.get("sub") or payload.get("user_id")
        except Exception as e:
            logger.debug(f"Token verification failed: {e}")
            return None

    def create_refresh_token(self, user_id: str, ip: str | None = None, user_agent: str | None = None) -> str:
        """Create long-lived refresh token."""
        expire = utc_now() + timedelta(days=config.JWT_REFRESH_EXPIRATION_DAYS)
        jti = str(uuid.uuid4())
        to_encode = {
            "user_id": user_id,
            "sub": user_id,
            "jti": jti,
            "exp": int(expire.timestamp()),
            "iat": int(utc_now().timestamp()),
            "type": "refresh",
        }
        if ip or user_agent:
            to_encode["fingerprint"] = self._generate_fingerprint(ip or "", user_agent or "")
        return jwt.encode(to_encode, cast(str, config.JWT_REFRESH_SECRET), algorithm=self.jwt_algorithm)

    async def verify_refresh_token(
        self, token: str, ip: str | None = None, user_agent: str | None = None
    ) -> dict[str, Any] | None:
        """Verify refresh token (Async)."""
        try:
            payload = jwt.decode(token, cast(str, config.JWT_REFRESH_SECRET), algorithms=[self.jwt_algorithm])
            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")
            if jti and await self.is_token_revoked(jti):
                return None

            token_fingerprint = payload.get("fingerprint")
            if token_fingerprint and (ip or user_agent):
                current_fingerprint = self._generate_fingerprint(ip or "", user_agent or "")
                if token_fingerprint != current_fingerprint:
                    return None
            return payload
        except Exception as e:
            logger.error("Session verification unsuccessful: %s", e)
            return None
