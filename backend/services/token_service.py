"""
Token Service for Purrfect Spots

Centralized token management providing:
- Token blacklisting with TTL (for logout, security events)
- Session invalidation (for password changes)
- Redis-backed with in-memory fallback + Database persistence
"""

import hashlib
import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import redis.asyncio as aioredis

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
from supabase import AClient
from utils.datetime_utils import utc_now_iso
from utils.supabase_client import get_async_supabase_admin_client


class TokenService:
    """
    Manages JWT token lifecycle with blacklisting support. (Async)
    """

    def __init__(
        self,
        redis_client: "aioredis.Redis | None" = None,
        supabase_client: AClient | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        """
        Initialize token service.
        """
        self.redis = redis_client
        self.db = db
        self._memory_blacklist: dict[str, datetime] = {}  # Fallback storage
        self.default_ttl = 3600 * 24 * 7  # 7 days
        self.supabase_admin = supabase_client
        self.TOKEN_COLUMNS = "id, token_jti, user_id, expires_at, revoked_at"

    async def _get_admin_client(self) -> AClient:
        """Lazy load admin client if not provided"""
        if self.supabase_admin is None:
            self.supabase_admin = await get_async_supabase_admin_client()
        return self.supabase_admin

    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def blacklist_token(
        self,
        token: str | None,
        reason: str = "logout",
        ttl_seconds: int | None = None,
        user_id: str | None = None,
        jti: str | None = None,
        expires_at: datetime | None = None,
    ) -> bool:
        """
        Add token to blacklist. (Async)
        """
        # 1. Calculate derivatives
        token_hash = self._hash_token(token) if token else (jti or "unknown")
        ttl = ttl_seconds or self.default_ttl

        # 2. Write to Fast Cache (Redis/Memory)
        if self.redis:
            try:
                key = f"blacklist:{token_hash}"
                await self.redis.setex(key, ttl, reason)
                logger.debug("Identifier stored in fast cache (Hash: %s)", token_hash[:8])
            except Exception as e:
                logger.warning(f"Redis blacklist failed: {e}")
        else:
            # Memory fallback
            expiry = datetime.now(UTC) + timedelta(seconds=ttl)
            self._memory_blacklist[token_hash] = expiry
            logger.debug(f"Token blacklisted in memory. Reason: {reason}")
            self._cleanup_memory_blacklist()

        # 3. Persist to Database (Supabase) if we have enough info
        if jti and user_id and expires_at:
            try:
                if self.db:
                    db_session = self.db
                    query = text(
                        "INSERT INTO token_blacklist (token_jti, user_id, expires_at, revoked_at) "
                        "VALUES (:jti, :user_id, :expires_at, :revoked_at)"
                    )
                    await db_session.execute(
                        query,
                        {
                            "jti": jti,
                            "user_id": user_id,
                            "expires_at": expires_at.isoformat(),
                            "revoked_at": utc_now_iso(),
                        },
                    )
                    await db_session.commit()
                else:
                    admin_client = await self._get_admin_client()
                    await (
                        admin_client.table("token_blacklist")
                        .insert(
                            {
                                "token_jti": jti,
                                "user_id": user_id,
                                "expires_at": expires_at.isoformat(),
                                "revoked_at": utc_now_iso(),
                            }
                        )
                        .execute()
                    )
            except Exception as e:
                logger.error(f"Failed to persist blacklist to DB: {e}")

        return True

    async def _check_redis_blacklist(self, token_hash: str) -> bool:
        """Check Redis blacklist."""
        if not self.redis:
            return False
        try:
            result = await self.redis.exists(f"blacklist:{token_hash}")
            if result:
                return True
        except Exception as e:
            logger.warning(f"Redis read error: {e}")
            # If connection is dead, invalidate the singleton so it reconnects next time
            if _is_reconnect_error(e):
                reset_token_service()
        return False

    def _check_memory_blacklist(self, token_hash: str) -> bool:
        """Check in-memory blacklist."""
        if token_hash in self._memory_blacklist:
            if self._memory_blacklist[token_hash] > datetime.now(UTC):
                return True
            self._memory_blacklist.pop(token_hash, None)
        return False

    async def _check_db_blacklist(self, jti: str | None, token_hash: str) -> bool:
        """Check database blacklist (Async-safe)."""
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        if not is_production:
            return False

        try:
            target_jti = jti if jti else token_hash
            if self.db:
                return await self._check_db_blacklist_sql(target_jti)

            return await self._check_db_blacklist_supabase(target_jti)
        except Exception as e:
            logger.warning(f"Database check failed: {e}")
            if is_production:
                logger.error("Database check failed - blocking token for security")
                return True
        return False

    async def _check_db_blacklist_sql(self, jti: str) -> bool:
        """Check database blacklist using SQLAlchemy."""
        if not self.db:
            return False
        db_session = self.db
        query = text("SELECT expires_at FROM token_blacklist WHERE token_jti = :jti")
        result = await db_session.execute(query, {"jti": jti})
        rows = result.fetchall()
        for row in rows:
            expires_at = datetime.fromisoformat(row[0].replace("Z", "+00:00"))
            if datetime.now(UTC) < expires_at:
                return True
        return False

    async def _check_db_blacklist_supabase(self, jti: str) -> bool:
        """Check database blacklist using Supabase."""
        admin_client = await self._get_admin_client()
        supa_res = await admin_client.table("token_blacklist").select(self.TOKEN_COLUMNS).eq("token_jti", jti).execute()

        if supa_res.data:
            for entry in supa_res.data:
                expires_at = datetime.fromisoformat(entry["expires_at"].replace("Z", "+00:00"))
                if datetime.now(UTC) < expires_at:
                    return True
        return False

    async def is_blacklisted(self, token: str | None = None, jti: str | None = None) -> bool:
        """
        Check if token is blacklisted. (Async)
        """
        token_hash = self._hash_token(token) if token else jti
        if not token_hash:
            return False

        # 1. Check Redis
        if await self._check_redis_blacklist(token_hash):
            return True

        # 2. Check Memory
        if self._check_memory_blacklist(token_hash):
            return True

        # 3. SECURITY: Check Database as source of truth
        return bool(await self._check_db_blacklist(jti, token_hash))

    async def blacklist_all_user_tokens(self, user_id: str, reason: str = "security_event") -> int:
        """Invalidate all tokens for a user."""
        if self.redis:
            try:
                key = f"user_invalidated:{user_id}"
                await self.redis.set(key, datetime.now(UTC).isoformat())
                await self.redis.expire(key, self.default_ttl)
                logger.info("Session state cleared for user: %s (Reason: %s)", user_id, reason)
                return 1
            except Exception as e:
                logger.warning(f"Redis user invalidation failed: {e}")
        return 0

    async def is_user_invalidated(self, user_id: str, token_issued_at: datetime) -> bool:
        """Check if user's tokens have been globally invalidated."""
        if self.redis:
            try:
                key = f"user_invalidated:{user_id}"
                invalidated_at_str = await self.redis.get(key)
                if invalidated_at_str:
                    invalidated_at = datetime.fromisoformat(invalidated_at_str.decode())
                    if invalidated_at.tzinfo is None:
                        invalidated_at = invalidated_at.replace(tzinfo=UTC)
                    if token_issued_at.tzinfo is None:
                        token_issued_at = token_issued_at.replace(tzinfo=UTC)

                    return token_issued_at < invalidated_at
            except Exception as e:
                logger.warning(f"Redis user check failed: {e}")

        return False

    def _cleanup_memory_blacklist(self) -> None:
        """Remove expired entries from memory blacklist"""
        now = datetime.now(UTC)
        expired = [k for k, expiry in self._memory_blacklist.items() if expiry <= now]
        for k in expired:
            self._memory_blacklist.pop(k, None)


# Singleton instance
_token_service: TokenService | None = None

# Connection errors that warrant a full reconnect
_RECONNECT_ERRORS = ("forcibly closed", "connection refused", "connection reset", "broken pipe", "eof occurred")


def _is_reconnect_error(exc: Exception) -> bool:
    """Returns True if the error suggests the Redis connection is dead."""
    msg = str(exc).lower()
    return any(pattern in msg for pattern in _RECONNECT_ERRORS)


def reset_token_service() -> None:
    """Force the singleton to reconnect on next request (call after Redis errors)."""
    global _token_service
    _token_service = None


async def get_token_service(db: AsyncSession | None = None) -> TokenService:
    """Get or create token service (Async dependency)"""
    global _token_service

    if _token_service is None:
        redis_client = None
        redis_url = os.getenv("REDIS_URL")

        if redis_url:
            try:
                import redis.asyncio as aioredis

                redis_client = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                await redis_client.ping()
                logger.info("Token service initialized with Redis")
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")
                redis_client = None

        # Admin client will be lazily loaded
        _token_service = TokenService(redis_client, db=db)
        if not redis_client:
            logger.info("Token service initialized with in-memory storage")
    else:
        # If singleton exists, update DB session if provided
        if db:
            _token_service.db = db

    return _token_service
