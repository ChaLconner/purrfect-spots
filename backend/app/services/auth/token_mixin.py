import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import jwt

from app.compat import structlog
from app.config import config
from app.services.auth.base_mixin import AuthBaseMixin
from app.services.token_service import get_token_service
from app.utils.datetime_utils import utc_now

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
            token_service = await get_token_service(self.db)
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

    async def consume_refresh_token(self, payload: dict[str, Any]) -> bool:
        """Atomically consume a refresh token before issuing its replacement."""
        token_service = await get_token_service(self.db)
        return await token_service.consume_refresh_token(
            payload["jti"], payload["sub"], datetime.fromtimestamp(payload["exp"], UTC)
        )

    def create_access_token(
        self,
        user_id: str,
        user_data: dict[str, Any] | None = None,
        role: str = "user",
        permissions: list[str] | None = None,
        tier: str = "free",
    ) -> str:
        """Create JWT access token."""
        expire = utc_now() + timedelta(hours=self.jwt_expiration_hours)
        jti = str(uuid.uuid4())
        normalized_tier = "pro" if tier.lower() == "pro" else "free"
        to_encode: dict[str, Any] = {
            "user_id": user_id,
            "sub": user_id,
            "role": role,
            "permissions": permissions or [],
            "tier": normalized_tier,
            "jti": jti,
            "exp": int(expire.timestamp()),
            "iat": int(utc_now().timestamp()),
            "type": "access",
            "iss": "purrfect-spots",
            "aud": "purrfect-spots-api",
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
                    "app_metadata": {
                        "provider": "google" if user_data.get("google_id") else "email",
                        "tier": normalized_tier,
                    },
                }
            )
        return jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_access_token(self, token: str) -> str | None:
        """Verify access token and return user_id."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                audience="purrfect-spots-api",
                issuer="purrfect-spots",
                options={"require": ["exp", "iat", "sub", "jti", "type"]},
            )
            if payload.get("type") != "access":
                return None
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
            "iss": "purrfect-spots",
            "aud": "purrfect-spots-refresh",
        }
        if ip or user_agent:
            to_encode["fingerprint"] = self._generate_fingerprint(ip or "", user_agent or "")
        return jwt.encode(to_encode, cast(str, config.JWT_REFRESH_SECRET), algorithm=self.jwt_algorithm)

    async def verify_refresh_token(
        self, token: str, ip: str | None = None, user_agent: str | None = None
    ) -> dict[str, Any] | None:
        """Verify refresh token (Async)."""
        try:
            payload = jwt.decode(
                token,
                cast(str, config.JWT_REFRESH_SECRET),
                algorithms=[self.jwt_algorithm],
                audience="purrfect-spots-refresh",
                issuer="purrfect-spots",
                options={"require": ["exp", "iat", "sub", "user_id", "jti", "type"]},
            )
            if payload.get("type") != "refresh":
                return None
            if not payload["jti"] or not payload["sub"] or payload["sub"] != payload["user_id"]:
                return None

            jti = payload.get("jti")
            if jti and await self.is_token_revoked(jti):
                return None

            token_service = await get_token_service(self.db)
            if await token_service.is_user_invalidated(payload["sub"], datetime.fromtimestamp(payload["iat"], UTC)):
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
