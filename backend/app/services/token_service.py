"""
Token Service for Purrfect Spots

Centralized token management providing:
- Token blacklisting with TTL (for logout, security events)
- Session invalidation (for password changes)
- Redis-backed with in-memory fallback + Database persistence
"""

import asyncio
import hashlib
import math
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import redis.asyncio as aioredis

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.logger import logger
from app.runtime_environment import is_production_environment
from app.services.redis_service import redis_service

UTC_OFFSET_SUFFIX = "+00:00"
from app.utils.datetime_utils import utc_now_iso
from app.utils.supabase_client import get_async_supabase_admin_client, has_supabase_service_role_key


class TokenService:
    """
    Manages JWT token lifecycle with blacklisting support. (Async)
    """

    def __init__(
        self,
        redis_client: aioredis.Redis | None = None,
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
        self.TOKEN_COLUMNS = "id, token_jti, user_id, expires_at, revoked_at"  # nosec S105

    async def _get_admin_client(self, force_refresh: bool = False) -> AClient:
        """Lazy load admin client if not provided"""
        if force_refresh or self.supabase_admin is None:
            self.supabase_admin = await get_async_supabase_admin_client(force_refresh=force_refresh)
        return self.supabase_admin

    @staticmethod
    def _is_rls_error(exc: Exception) -> bool:
        error_message = str(exc).lower()
        return "42501" in error_message or "row-level security" in error_message

    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _store_in_memory_blacklist(self, token_hash: str, ttl: int) -> None:
        """Store blacklist entry in process memory when a durable fast cache is unavailable."""
        expiry = datetime.now(UTC) + timedelta(seconds=ttl)
        self._memory_blacklist[token_hash] = expiry
        logger.debug("Memory deny-list fallback updated")
        self._cleanup_memory_blacklist()

    def _get_blacklist_ttl(self, ttl_seconds: int | None, expires_at: datetime | None) -> int:
        """Keep fast-cache revocation entries no longer than token lifetime."""
        requested_ttl = self.default_ttl if ttl_seconds is None else ttl_seconds
        requested_ttl = max(1, int(requested_ttl))
        if expires_at is None:
            return requested_ttl

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        remaining_ttl = math.ceil((expires_at - datetime.now(UTC)).total_seconds())
        return max(1, min(requested_ttl, remaining_ttl))

    async def _cache_blacklisted_token(self, token_hash: str, ttl: int, reason: str) -> None:
        if not self.redis:
            self._store_in_memory_blacklist(token_hash, ttl)
            return

        try:
            key = f"blacklist:{token_hash}"
            await self.redis.setex(key, ttl, reason)
            logger.debug("Identifier stored in fast cache (Hash: %s)", token_hash[:8])
        except Exception as exc:
            logger.warning("Redis blacklist failed: %s", exc)
            self._store_in_memory_blacklist(token_hash, ttl)

    async def _persist_blacklist_sql(self, jti: str, user_id: str, expires_at: datetime) -> bool:
        if not self.db:
            return False

        try:
            query = text(
                "INSERT INTO token_blacklist (token_jti, user_id, expires_at, revoked_at) "
                "VALUES (:jti, :user_id, :expires_at, :revoked_at) "
                "ON CONFLICT (token_jti) DO UPDATE SET "
                "user_id = EXCLUDED.user_id, "
                "expires_at = EXCLUDED.expires_at, "
                "revoked_at = EXCLUDED.revoked_at"
            )
            await self.db.execute(
                query,
                {
                    "jti": jti,
                    "user_id": user_id,
                    "expires_at": expires_at,
                    "revoked_at": datetime.now(UTC),
                },
            )
            await self.db.commit()
            return True
        except Exception as exc:
            await self.db.rollback()
            logger.warning("SQL blacklist save failed, falling back to Supabase client: %s", exc)
            return False

    async def _persist_blacklist_supabase(self, jti: str, user_id: str, expires_at: datetime) -> bool:
        payload = {
            "token_jti": jti,
            "user_id": user_id,
            "expires_at": expires_at.isoformat(),
            "revoked_at": utc_now_iso(),
        }
        try:
            admin_client = await self._get_admin_client()
            await admin_client.table("token_blacklist").upsert(payload, on_conflict="token_jti").execute()
        except Exception as exc:
            if not self._is_rls_error(exc):
                raise

            logger.warning("token_blacklist insert hit RLS; refreshing Supabase admin client and retrying once")
            admin_client = await self._get_admin_client(force_refresh=True)
            await admin_client.table("token_blacklist").upsert(payload, on_conflict="token_jti").execute()
        return True

    async def _persist_blacklist(
        self,
        jti: str | None,
        user_id: str | None,
        expires_at: datetime | None,
        token_hash: str,
    ) -> bool:
        if not (jti and user_id and expires_at):
            return True
        if await self._persist_blacklist_sql(jti, user_id, expires_at):
            return True
        if not has_supabase_service_role_key():
            logger.info("Skipping blacklist DB persistence because no service-role key is available in runtime.")
            return bool(self._memory_blacklist.get(token_hash) or self.redis)

        try:
            return await self._persist_blacklist_supabase(jti, user_id, expires_at)
        except Exception as exc:
            if self._is_rls_error(exc):
                logger.warning("Skipping blacklist DB persistence due to token_blacklist RLS policy")
            else:
                logger.error("Failed to persist blacklist to DB")
            return bool(self._memory_blacklist.get(token_hash) or self.redis)

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
        token_hash = self._hash_token(token) if token else (jti or "unknown")
        ttl = self._get_blacklist_ttl(ttl_seconds, expires_at)
        await self._cache_blacklisted_token(token_hash, ttl, reason)
        return await self._persist_blacklist(jti, user_id, expires_at, token_hash)

    async def _check_redis_blacklist(self, token_hash: str) -> bool:
        """Check Redis blacklist."""
        if not self.redis:
            return False
        try:
            result = await self.redis.exists(f"blacklist:{token_hash}")
            if result:
                return True
        except Exception as e:
            logger.warning("Redis read error")
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
        is_production = is_production_environment()
        if not is_production:
            return False

        try:
            target_jti = jti if jti else token_hash
            if self.db:
                try:
                    return await self._check_db_blacklist_sql(target_jti)
                except Exception:
                    logger.warning("SQL blacklist lookup failed, falling back to Supabase client")

            return await self._check_db_blacklist_supabase(target_jti)
        except Exception:
            logger.warning("Database blacklist check failed")
            logger.error("Database check failed - blocking token for security")
            return True

    async def _check_db_blacklist_sql(self, jti: str) -> bool:
        """Check database blacklist using SQLAlchemy."""
        if not self.db:
            return False
        db_session = self.db
        query = text("SELECT expires_at FROM token_blacklist WHERE token_jti = :jti")
        result = await db_session.execute(query, {"jti": jti})
        rows = result.fetchall()
        for row in rows:
            value = row[0]
            expires_at = (
                datetime.fromisoformat(value.replace("Z", UTC_OFFSET_SUFFIX)) if isinstance(value, str) else value
            )
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if datetime.now(UTC) < expires_at:
                return True
        return False

    async def _check_db_blacklist_supabase(self, jti: str) -> bool:
        """Check database blacklist using Supabase."""
        try:
            admin_client = await self._get_admin_client()
            supa_res = (
                await admin_client.table("token_blacklist").select(self.TOKEN_COLUMNS).eq("token_jti", jti).execute()
            )
        except Exception as exc:
            if not self._is_rls_error(exc):
                raise

            logger.warning("token_blacklist select hit RLS; refreshing Supabase admin client and retrying once")
            admin_client = await self._get_admin_client(force_refresh=True)
            supa_res = (
                await admin_client.table("token_blacklist").select(self.TOKEN_COLUMNS).eq("token_jti", jti).execute()
            )

        if supa_res.data:
            data = cast(list[dict[str, Any]], supa_res.data)
            for entry in data:
                expires_at = datetime.fromisoformat(entry["expires_at"].replace("Z", UTC_OFFSET_SUFFIX))
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
        """Invalidate all tokens for a user by setting a global revocation timestamp."""
        logger.debug("Global token revocation requested")
        now_iso = utc_now_iso()

        # 1. Update Fast Cache (Redis)
        if self.redis:
            try:
                key = f"user_invalidated:{user_id}"
                await self.redis.set(key, now_iso)
                await self.redis.expire(key, self.default_ttl)
                logger.info("Session state cleared in Redis")
            except Exception as e:
                logger.warning("Redis user invalidation failed: %s", e)

        # 2. Persist to Database (Source of Truth)
        try:
            if self.db:
                query = text("UPDATE users SET last_token_revocation_at = :now WHERE id = :u_id")
                await self.db.execute(query, {"now": now_iso, "u_id": user_id})
                await self.db.commit()
            else:
                admin_client = await self._get_admin_client()
                await (
                    admin_client.table("users")
                    .update({"last_token_revocation_at": now_iso})
                    .eq("id", user_id)
                    .execute()
                )

            logger.info("Persistent revocation set for user: %s", user_id)
            return 1
        except Exception as e:
            logger.error("Failed to persist global revocation for user %s: %s", user_id, e)
            # If we can't persist it, we have a security risk if Redis goes down later
            return 0

    @staticmethod
    def _as_utc_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    async def _get_redis_user_revocation(self, user_id: str) -> datetime | None:
        if not self.redis:
            return None

        try:
            invalidated_at_str = await self.redis.get(f"user_invalidated:{user_id}")
            if not invalidated_at_str:
                return None
            if isinstance(invalidated_at_str, bytes):
                invalidated_at_str = invalidated_at_str.decode()
            return self._as_utc_datetime(datetime.fromisoformat(str(invalidated_at_str)))
        except Exception as exc:
            logger.warning("Redis user check failed: %s", exc)
            return None

    async def _get_db_user_revocation(self, user_id: str) -> datetime | None:
        if self.db:
            query = text("SELECT last_token_revocation_at FROM users WHERE id = :u_id")
            result = await self.db.execute(query, {"u_id": user_id})
            row = result.fetchone()
            if not row or not row[0]:
                return None
            value = row[0]
            revocation = (
                datetime.fromisoformat(value.replace("Z", UTC_OFFSET_SUFFIX)) if isinstance(value, str) else value
            )
            return self._as_utc_datetime(cast(datetime, revocation))

        admin_client = await self._get_admin_client()
        response = (
            await admin_client.table("users")
            .select("last_token_revocation_at")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        if not response or not response.data:
            return None
        data = cast(dict[str, Any], response.data)
        value = data.get("last_token_revocation_at")
        if not value:
            return None
        revocation = datetime.fromisoformat(value.replace("Z", UTC_OFFSET_SUFFIX)) if isinstance(value, str) else value
        return self._as_utc_datetime(cast(datetime, revocation))

    async def is_user_invalidated(self, user_id: str, token_issued_at: datetime) -> bool:
        """Check if user's tokens have been globally invalidated (Redis with DB fallback)."""
        issued_at = self._as_utc_datetime(token_issued_at)
        try:
            redis_invalidated_at = await self._get_redis_user_revocation(user_id)
            if redis_invalidated_at is not None:
                return issued_at < redis_invalidated_at
            db_invalidated_at = await self._get_db_user_revocation(user_id)
            return db_invalidated_at is not None and issued_at < db_invalidated_at
        except Exception as exc:
            logger.error("Database user invalidation check failed: %s", exc)
            # If we can't verify if a user should be invalidated, we should fail closed in the middleware
            # or raise an error here to be caught by the middleware.
            raise

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
    # Preserve the async contract used by authentication callers and provide a
    # cancellation point before returning a shared service instance.
    await asyncio.sleep(0)
    global _token_service

    if _token_service is None:
        # Share RedisService pool with cache and distributed locks.
        redis_client = redis_service.client
        if redis_client:
            logger.info("Initializing Token Service singleton with shared Redis backend")

        # Admin client will be lazily loaded
        _token_service = TokenService(redis_client, db=None)
        if not redis_client:
            logger.info("Initializing Token Service singleton with in-memory storage")

    if db:
        return TokenService(_token_service.redis, _token_service.supabase_admin, db=db)

    return _token_service
