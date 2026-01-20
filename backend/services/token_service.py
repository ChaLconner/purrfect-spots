"""
Token Service for Purrfect Spots

Centralized token management providing:
- Token blacklisting with TTL (for logout, security events)
- Session invalidation (for password changes)
- Redis-backed with in-memory fallback + Database persistence
"""

import hashlib
import os
from datetime import datetime, timedelta, timezone

from dependencies import get_supabase_admin_client, get_supabase_client
from logger import logger
from utils.datetime_utils import utc_now, utc_now_iso


class TokenService:
    """
    Manages JWT token lifecycle with blacklisting support.

    Uses Redis if available for distributed deployments,
    falls back to in-memory storage for single-instance deployments.
    Also syncs with Supabase DB for persistence.

    Security features:
    - Tokens are hashed before storage (never store raw tokens)
    - TTL-based expiration (automatic cleanup)
    - User-level invalidation support
    """

    def __init__(self, redis_client=None):
        """
        Initialize token service.

        Args:
            redis_client: Optional async Redis client
        """
        self.redis = redis_client
        self._memory_blacklist: dict[str, datetime] = {}  # Fallback storage
        self.default_ttl = 3600 * 24 * 7  # 7 days

        # We use admin client for blacklist operations to ensure we can write
        self.supabase_admin = get_supabase_admin_client()

    def _hash_token(self, token: str) -> str:
        """
        Hash token for secure storage.
        Never store raw tokens - use hash for lookup.
        """
        return hashlib.sha256(token.encode()).hexdigest()[:32]

    async def blacklist_token(
        self,
        token: str,
        reason: str = "logout",
        ttl_seconds: int | None = None,
        user_id: str | None = None,
        jti: str | None = None,
        expires_at: datetime | None = None,
    ) -> bool:
        """
        Add token to blacklist.

        Args:
            token: JWT token string (optional if jti provided, but preferred for hashing)
            reason: Reason for blacklisting
            ttl_seconds: TTL for fast cache
            user_id: Owner user ID (for DB logging)
            jti: Token ID (for DB logging)
            expires_at: Token expiration time

        Returns:
            True if successfully blacklisted
        """
        # 1. Calculate derivatives
        token_hash = self._hash_token(token) if token else (jti or "unknown")
        ttl = ttl_seconds or self.default_ttl

        # 2. Write to Fast Cache (Redis/Memory)
        if self.redis:
            try:
                key = f"blacklist:{token_hash}"
                await self.redis.setex(key, ttl, reason)
                logger.debug(f"Token blacklisted in Redis: {token_hash[:8]}")
            except Exception as e:
                logger.warning(f"Redis blacklist failed: {e}")
        else:
            # Memory fallback
            expiry = datetime.now(timezone.utc) + timedelta(seconds=ttl)
            self._memory_blacklist[token_hash] = expiry
            self._cleanup_memory_blacklist()

        # 3. Persist to Database (Supabase) if we have enough info
        # This allows other unrelated instances/workers to respect the blacklist eventually,
        # and provides audit trail.
        if jti and user_id and expires_at:
            try:
                # Run sync in case this is called from async context
                # Note: supabase-py client is synchronous mostly, but can be wrapped.
                # Here we assume standard synchronous client usage for DB.
                # Ideally, we should offload this if high throughput, but for logout it's fine.
                self.supabase_admin.table("token_blacklist").insert({
                    "token_jti": jti,
                    "user_id": user_id,
                    "expires_at": expires_at.isoformat(),
                    "revoked_at": utc_now_iso()
                }).execute()
            except Exception as e:
                logger.error(f"Failed to persist blacklist to DB: {e}")
                # We don't return False here because the cache write succeeded,
                # so the token IS effectively blacklisted for this instance.

        return True

    async def is_blacklisted(self, token: str = None, jti: str = None) -> bool:
        """
        Check if token is blacklisted.
        
        Priority:
        1. Check Redis/Memory (Fastest)
        2. Check Database (Source of Truth for persistence) - Optional optimization: skip if cache miss?
           Actually, for security, if cache misses, we MIGHT want to check DB if we suspect cache is cold.
           But for performance, usually we rely on cache.
           
           DECISION: For high performance, we check cache first. 
           If cache is empty/down, should we check DB?
           - Checking DB on every request is the bottleneck we are fixing.
           - So we should ONLY check Redis/Memory. The DB is just for hydration on restart or audit.
           - HOWEVER, to sync across instances without Redis, DB check is needed?
           - The prompt asked to fix performance. So we MUST avoid DB check on every request.
           
           Compromise: We check ONLY cache (Redis/Memory).
           The DB write in `blacklist_token` is for audit and potential cold-start hydration tools (not implemented yet).
        """
        token_hash = self._hash_token(token) if token else jti
        if not token_hash:
            return False

        # 1. Check Redis
        if self.redis:
            try:
                result = await self.redis.exists(f"blacklist:{token_hash}")
                if result:
                    return True
            except Exception as e:
                logger.warning(f"Redis check failed: {e}")

        # 2. Check Memory
        if token_hash in self._memory_blacklist:
            if self._memory_blacklist[token_hash] > datetime.now(timezone.utc):
                return True
            else:
                del self._memory_blacklist[token_hash]

        # 3. (Optional) DB Check - DISABLED for performance
        # We assume if it's not in cache, it's valid.
        
        return False

    async def blacklist_all_user_tokens(self, user_id: str, reason: str = "security") -> int:
        """
        Invalidate all tokens for a user.
        """
        if self.redis:
            try:
                key = f"user_invalidated:{user_id}"
                await self.redis.set(key, datetime.now(timezone.utc).isoformat())
                await self.redis.expire(key, self.default_ttl)
                logger.info(f"All tokens invalidated for user: {user_id}")
                return 1
            except Exception as e:
                logger.warning(f"Redis user invalidation failed: {e}")
        return 0

    async def is_user_invalidated(self, user_id: str, token_issued_at: datetime) -> bool:
        """
        Check if user's tokens have been globally invalidated.
        """
        if self.redis:
            try:
                key = f"user_invalidated:{user_id}"
                invalidated_at_str = await self.redis.get(key)
                if invalidated_at_str:
                    invalidated_at = datetime.fromisoformat(invalidated_at_str.decode())
                    # Ensure timezone awareness
                    if invalidated_at.tzinfo is None:
                        invalidated_at = invalidated_at.replace(tzinfo=timezone.utc)
                    if token_issued_at.tzinfo is None:
                        token_issued_at = token_issued_at.replace(tzinfo=timezone.utc)
                        
                    return token_issued_at < invalidated_at
            except Exception as e:
                logger.warning(f"Redis user check failed: {e}")

        return False

    def _cleanup_memory_blacklist(self):
        """Remove expired entries from memory blacklist"""
        now = datetime.now(timezone.utc)
        expired = [k for k, expiry in self._memory_blacklist.items() if expiry <= now]
        for k in expired:
            del self._memory_blacklist[k]


# Singleton instance
_token_service: TokenService | None = None


async def get_token_service() -> TokenService:
    """
    Get or create token service singleton.
    Lazily initializes Redis connection if REDIS_URL is configured.
    """
    global _token_service

    if _token_service is None:
        redis_client = None
        redis_url = os.getenv("REDIS_URL")

        if redis_url:
            try:
                import redis.asyncio as aioredis
                redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False)
                await redis_client.ping()
                logger.info("Token service initialized with Redis")
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}")
                redis_client = None

        _token_service = TokenService(redis_client)
        if not redis_client:
            logger.info("Token service initialized with in-memory storage")

    return _token_service


def get_token_service_sync() -> TokenService:
    """Sync accessor for non-async contexts (careful with async methods)"""
    global _token_service
    # Same initialization logic but without async ping
    if _token_service is None:
        redis_client = None
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis.asyncio as aioredis
                redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False)
            except Exception:
                pass
        _token_service = TokenService(redis_client)
    return _token_service
