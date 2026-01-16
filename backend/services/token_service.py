"""
Token Service for Purrfect Spots

Centralized token management providing:
- Token blacklisting with TTL (for logout, security events)
- Session invalidation (for password changes)
- Redis-backed with in-memory fallback
"""

import hashlib
import os
from datetime import datetime, timedelta

from logger import logger


class TokenService:
    """
    Manages JWT token lifecycle with blacklisting support.

    Uses Redis if available for distributed deployments,
    falls back to in-memory storage for single-instance deployments.

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
    ) -> bool:
        """
        Add token to blacklist.

        Args:
            token: JWT token to blacklist
            reason: Reason for blacklisting (logout, security, revoked)
            ttl_seconds: Time to keep in blacklist (defaults to 7 days)

        Returns:
            True if successfully blacklisted
        """
        token_hash = self._hash_token(token)
        ttl = ttl_seconds or self.default_ttl

        if self.redis:
            try:
                key = f"blacklist:{token_hash}"
                await self.redis.setex(key, ttl, reason)
                logger.info(
                    f"Token blacklisted: hash={token_hash[:8]}..., reason={reason}"
                )
                return True
            except Exception as e:
                logger.warning(f"Redis blacklist failed: {e}, using memory fallback")

        # Fallback to memory
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        self._memory_blacklist[token_hash] = expiry
        self._cleanup_memory_blacklist()
        logger.info(
            f"Token blacklisted (memory): hash={token_hash[:8]}..., reason={reason}"
        )
        return True

    async def is_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted.

        Args:
            token: JWT token to check

        Returns:
            True if token is blacklisted
        """
        token_hash = self._hash_token(token)

        if self.redis:
            try:
                result = await self.redis.exists(f"blacklist:{token_hash}")
                return bool(result)
            except Exception as e:
                logger.warning(f"Redis check failed: {e}, checking memory")

        # Fallback: check memory
        if token_hash in self._memory_blacklist:
            if self._memory_blacklist[token_hash] > datetime.utcnow():
                return True
            # Expired - clean up
            del self._memory_blacklist[token_hash]

        return False

    async def blacklist_all_user_tokens(self, user_id: str, reason: str = "security") -> int:
        """
        Invalidate all tokens for a user.

        Used when:
        - User changes password
        - Security breach detected
        - Admin forces logout

        Args:
            user_id: User ID to invalidate
            reason: Reason for invalidation

        Returns:
            Number of operations performed (1 if successful)
        """
        if self.redis:
            try:
                # Store user invalidation timestamp
                # All tokens issued before this time are invalid
                key = f"user_invalidated:{user_id}"
                await self.redis.set(key, datetime.utcnow().isoformat())
                await self.redis.expire(key, self.default_ttl)
                logger.info(
                    f"All tokens invalidated for user: {user_id[:8]}..., reason={reason}"
                )
                return 1
            except Exception as e:
                logger.warning(f"Redis user invalidation failed: {e}")
        return 0

    async def is_user_invalidated(self, user_id: str, token_issued_at: datetime) -> bool:
        """
        Check if user's tokens have been globally invalidated.

        Args:
            user_id: User ID to check
            token_issued_at: When the token was issued

        Returns:
            True if token was issued before invalidation
        """
        if self.redis:
            try:
                key = f"user_invalidated:{user_id}"
                invalidated_at_str = await self.redis.get(key)
                if invalidated_at_str:
                    invalidated_at = datetime.fromisoformat(
                        invalidated_at_str.decode()
                    )
                    return token_issued_at < invalidated_at
            except Exception as e:
                logger.warning(f"Redis user check failed: {e}")

        return False

    def _cleanup_memory_blacklist(self):
        """Remove expired entries from memory blacklist"""
        now = datetime.utcnow()
        expired = [k for k, expiry in self._memory_blacklist.items() if expiry <= now]
        for k in expired:
            del self._memory_blacklist[k]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired blacklist entries")


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

                redis_client = aioredis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=False,
                )
                # Test connection
                await redis_client.ping()
                logger.info("Token service initialized with Redis")
            except Exception as e:
                logger.warning(f"Could not connect to Redis for token service: {e}")
                redis_client = None

        _token_service = TokenService(redis_client)

        if not redis_client:
            logger.info("Token service initialized with in-memory storage")

    return _token_service


def get_token_service_sync() -> TokenService:
    """
    Get token service synchronously (without connection test).

    Use this in non-async contexts where Redis connection
    can be established lazily on first use.
    """
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
                )
            except Exception as e:
                logger.warning(f"Could not create Redis client: {e}")

        _token_service = TokenService(redis_client)

    return _token_service
