"""
Tests for token service
"""

import os
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.token_service import TokenService


class TestTokenService:
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        return AsyncMock()

    @pytest.fixture
    def mock_supabase_admin(self):
        """Mock Supabase admin client"""
        mock = MagicMock()
        # Mock chainable methods
        chain_mock = MagicMock()
        chain_mock.insert.return_value = chain_mock
        chain_mock.select.return_value = chain_mock
        chain_mock.eq.return_value = chain_mock
        # execute must be async
        chain_mock.execute = AsyncMock(return_value=MagicMock(data=[], count=0))

        mock.table = MagicMock(return_value=chain_mock)
        return mock

    @pytest.fixture
    def token_service(self, mock_redis, mock_supabase_admin):
        """Create TokenService instance with mocked dependencies"""
        # Patch the async getter
        with patch(
            "services.token_service.get_async_supabase_admin_client", new=AsyncMock(return_value=mock_supabase_admin)
        ):
            service = TokenService(mock_redis)
            yield service

    @pytest.mark.asyncio
    async def test_blacklist_token_redis(self, token_service, mock_redis):
        """Test blacklisting a token with Redis enabled"""
        token = "test-token"

        # We need to spy on redis.setex
        # token_service.redis is mock_redis

        result = await token_service.blacklist_token(token=token, reason="test-logout", ttl_seconds=3600)

        assert result is True
        # Hash token
        token_hash = token_service._hash_token(token)
        mock_redis.setex.assert_called_once_with(f"blacklist:{token_hash}", 3600, "test-logout")

    @pytest.mark.asyncio
    async def test_blacklist_token_memory_fallback(self, mock_supabase_admin):
        """Test blacklisting with memory fallback when Redis is None"""
        with patch(
            "services.token_service.get_async_supabase_admin_client", new=AsyncMock(return_value=mock_supabase_admin)
        ):
            service = TokenService(None)
            token = "memory-token"
            token_hash = service._hash_token(token)

            result = await service.blacklist_token(token=token, reason="memory-logout")

            assert result is True
            assert token_hash in service._memory_blacklist

            # Check expiry is set in future
            expiry = service._memory_blacklist[token_hash]
            assert expiry.tzinfo == UTC
            assert expiry > datetime.now(UTC)

    @pytest.mark.asyncio
    async def test_blacklist_token_db_persistence(self, token_service, mock_supabase_admin):
        """Test blacklisting with DB persistence"""
        token = "db-token"
        user_id = "user-123"
        jti = "jti-123"
        expires_at = datetime.now(UTC) + timedelta(hours=1)

        result = await token_service.blacklist_token(token=token, user_id=user_id, jti=jti, expires_at=expires_at)

        assert result is True

        # Verify mocked table calls
        mock_supabase_admin.table.assert_called_with("token_blacklist")
        mock_supabase_admin.table.return_value.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_blacklisted_redis(self, token_service, mock_redis):
        """Test checking blacklist status via Redis"""
        token = "redis-check"
        token_hash = token_service._hash_token(token)
        mock_redis.exists.return_value = 1

        result = await token_service.is_blacklisted(token=token)

        assert result is True
        mock_redis.exists.assert_called_once_with(f"blacklist:{token_hash}")

    @pytest.mark.asyncio
    async def test_is_blacklisted_memory(self, mock_supabase_admin):
        """Test checking blacklist status via Memory"""
        with patch(
            "services.token_service.get_async_supabase_admin_client", new=AsyncMock(return_value=mock_supabase_admin)
        ):
            service = TokenService(None)
            token = "memory-check"
            token_hash = service._hash_token(token)
            service._memory_blacklist[token_hash] = datetime.now(UTC) + timedelta(minutes=5)

            result = await service.is_blacklisted(token=token)
            assert result is True

    @pytest.mark.asyncio
    async def test_is_blacklisted_db(self, token_service, mock_supabase_admin):
        # Setup Redis/Memory miss
        token_service.redis.exists = AsyncMock(return_value=False)

        # Setup DB hit
        mock_response = MagicMock()
        from datetime import datetime, timedelta

        future_time = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

        mock_response.data = [{"expires_at": future_time}]

        # Mock admin client returning our response
        mock_supabase_admin.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
            return_value=mock_response
        )

        # Force production environment to enable DB check
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            result = await token_service.is_blacklisted(jti="test-jti")

        assert result is True
        mock_supabase_admin.table.assert_called_with("token_blacklist")

    @pytest.mark.asyncio
    async def test_blacklist_all_user_tokens(self, token_service, mock_redis):
        """Test invalidating all user tokens"""
        user_id = "user-456"

        result = await token_service.blacklist_all_user_tokens(user_id)

        assert result == 1
        mock_redis.set.assert_called_once()
        assert f"user_invalidated:{user_id}" in mock_redis.set.call_args[0][0]

    @pytest.mark.asyncio
    async def test_is_user_invalidated(self, token_service, mock_redis):
        """Test checking if user tokens are invalidated"""
        user_id = "user-456"
        invalidated_at = datetime.now(UTC)
        mock_redis.get.return_value = invalidated_at.isoformat().encode()

        # Token issued BEFORE invalidation
        token_iat = invalidated_at - timedelta(minutes=1)
        # Using aware objects for comparison
        token_iat = token_iat.replace(tzinfo=UTC)  # already aware

        result = await token_service.is_user_invalidated(user_id, token_iat)
        assert result is True

        # Token issued AFTER invalidation
        token_iat_new = invalidated_at + timedelta(minutes=1)
        result = await token_service.is_user_invalidated(user_id, token_iat_new)
        assert result is False

    @pytest.mark.asyncio
    async def test_is_user_invalidated_naive_dates(self, token_service, mock_redis):
        """Test is_user_invalidated with naive datetime objects (should handle gracefully)"""
        user_id = "u1"
        invalidated_at = datetime.now()  # naive
        mock_redis.get.return_value = invalidated_at.isoformat().encode()

        token_iat = datetime.now() - timedelta(minutes=1)  # naive

        # TokenService handles timezone conversion if naive
        result = await token_service.is_user_invalidated(user_id, token_iat)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_db_blacklist_exception_prod(self, token_service, mock_supabase_admin):
        """Test DB check exception in production blocks for security (fail-closed)"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            mock_supabase_admin.table.return_value.execute.side_effect = Exception("DB error")

            # Since _check_db_blacklist is async and uses _get_admin_client -> mock
            # We call is_blacklisted which calls _check_db_blacklist

            result = await token_service.is_blacklisted(jti="jti")
            assert result is True  # Fail closed

    @pytest.mark.asyncio
    async def test_check_db_blacklist_not_prod(self, token_service, mock_supabase_admin):
        """Test DB check skipped in dev if no production flag"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            # mock not called
            mock_supabase_admin.table.return_value.execute.side_effect = Exception("DB error")

            # Need to avoid redis check returning true
            token_service.redis.exists.return_value = 0

            result = await token_service.is_blacklisted(jti="jti")
            assert result is False

    def test_cleanup_memory_blacklist(self, mock_supabase_admin):
        """Test clearing expired entries from memory blacklist"""
        # Patch async client (not used here but for safe init)
        with patch(
            "services.token_service.get_async_supabase_admin_client", new=AsyncMock(return_value=mock_supabase_admin)
        ):
            service = TokenService(None)
            service._memory_blacklist = {
                "old": datetime.now(UTC) - timedelta(minutes=1),
                "new": datetime.now(UTC) + timedelta(minutes=5),
            }
            service._cleanup_memory_blacklist()
            assert "old" not in service._memory_blacklist
            assert "new" in service._memory_blacklist
