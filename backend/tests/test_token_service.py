"""
Tests for token service
"""
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.token_service import TokenService


class TestTokenService:
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock = AsyncMock()
        return mock

    @pytest.fixture
    def mock_supabase_admin(self):
        """Mock Supabase admin client"""
        mock = MagicMock()
        mock.table.return_value = mock
        mock.insert.return_value = mock
        mock.select.return_value = mock
        mock.eq.return_value = mock
        mock.execute.return_value = MagicMock(data=[], count=0)
        return mock

    @pytest.fixture
    def token_service(self, mock_redis, mock_supabase_admin):
        """Create TokenService instance with mocked dependencies"""
        with patch("services.token_service.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = TokenService(mock_redis)
            return service

    @pytest.mark.asyncio
    async def test_blacklist_token_redis(self, token_service, mock_redis):
        """Test blacklisting a token with Redis enabled"""
        token = "test-token"
        token_hash = token_service._hash_token(token)
        
        result = await token_service.blacklist_token(token=token, reason="test-logout", ttl_seconds=3600)
        
        assert result is True
        mock_redis.setex.assert_called_once_with(f"blacklist:{token_hash}", 3600, "test-logout")

    @pytest.mark.asyncio
    async def test_blacklist_token_memory_fallback(self, mock_supabase_admin):
        """Test blacklisting with memory fallback when Redis is None"""
        with patch("services.token_service.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = TokenService(None)
            token = "memory-token"
            token_hash = service._hash_token(token)
            
            result = await service.blacklist_token(token=token, reason="memory-logout")
            
            assert result is True
            assert token_hash in service._memory_blacklist
            assert service._memory_blacklist[token_hash] > datetime.now(timezone.utc)

    @pytest.mark.asyncio
    async def test_blacklist_token_db_persistence(self, token_service, mock_supabase_admin):
        """Test blacklisting with DB persistence"""
        token = "db-token"
        user_id = "user-123"
        jti = "jti-123"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        result = await token_service.blacklist_token(
            token=token, 
            user_id=user_id, 
            jti=jti, 
            expires_at=expires_at
        )
        
        assert result is True
        mock_supabase_admin.table.assert_called_with("token_blacklist")
        mock_supabase_admin.insert.assert_called_once()

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
        with patch("services.token_service.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = TokenService(None)
            token = "memory-check"
            token_hash = service._hash_token(token)
            service._memory_blacklist[token_hash] = datetime.now(timezone.utc) + timedelta(minutes=5)
            
            result = await service.is_blacklisted(token=token)
            assert result is True

    @pytest.mark.asyncio
    async def test_is_blacklisted_db(self, token_service, mock_redis, mock_supabase_admin):
        """Test checking blacklist status via Database in production environment"""
        token = "db-check"
        jti = "jti-check"
        token_hash = token_service._hash_token(token)
        
        # Ensure Redis check returns False
        mock_redis.exists.return_value = 0
        
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            mock_supabase_admin.table.return_value = mock_supabase_admin
            mock_supabase_admin.select.return_value = mock_supabase_admin
            mock_supabase_admin.eq.return_value = mock_supabase_admin
            mock_supabase_admin.execute.return_value = MagicMock(
                data=[{"expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}]
            )
            
            result = await token_service.is_blacklisted(token=token, jti=jti)
            
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
        invalidated_at = datetime.now(timezone.utc)
        mock_redis.get.return_value = invalidated_at.isoformat().encode()
        
        # Token issued BEFORE invalidation
        token_iat = invalidated_at - timedelta(minutes=1)
        result = await token_service.is_user_invalidated(user_id, token_iat)
        assert result is True
        
        # Token issued AFTER invalidation
        token_iat_new = invalidated_at + timedelta(minutes=1)
        result = await token_service.is_user_invalidated(user_id, token_iat_new)
        assert result is False

    @pytest.mark.asyncio
    async def test_singleton_initialization(self):
        """Test singleton lazy initialization"""
        from services.token_service import get_token_service, _token_service
        
        # Reset singleton if it exists
        with patch("services.token_service._token_service", None):
            with patch.dict(os.environ, {"REDIS_URL": "redis://localhost:6379"}):
                with patch("redis.asyncio.from_url") as mock_from_url:
                    mock_r = AsyncMock()
                    mock_from_url.return_value = mock_r
                    
                    service = await get_token_service()
                    assert service is not None
                    mock_r.ping.assert_called_once()
    @pytest.mark.asyncio
    async def test_blacklist_token_redis_failure(self, token_service, mock_redis):
        """Test Redis failure in blacklist_token doesn't abort"""
        mock_redis.setex.side_effect = Exception("Redis down")
        token = "fail-token"
        result = await token_service.blacklist_token(token=token)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_db_blacklist_exception_prod(self, token_service, mock_supabase_admin):
        """Test DB check exception in production blocks for security (fail-closed)"""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            mock_supabase_admin.execute.side_effect = Exception("DB error")
            result = token_service._check_db_blacklist("jti", "hash")
            assert result is True

    @pytest.mark.asyncio
    async def test_check_db_blacklist_not_prod(self, token_service, mock_supabase_admin):
        """Test DB check skipped in dev if no production flag"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            result = token_service._check_db_blacklist("jti", "hash")
            assert result is False

    @pytest.mark.asyncio
    async def test_is_user_invalidated_naive_dates(self, token_service, mock_redis):
        """Test is_user_invalidated with naive datetime objects"""
        user_id = "u1"
        invalidated_at = datetime.now() # naive
        mock_redis.get.return_value = invalidated_at.isoformat().encode()
        
        token_iat = datetime.now() - timedelta(minutes=1) # naive
        result = await token_service.is_user_invalidated(user_id, token_iat)
        assert result is True

    def test_cleanup_memory_blacklist(self, mock_supabase_admin):
        """Test clearing expired entries from memory blacklist"""
        with patch("services.token_service.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = TokenService(None)
            service._memory_blacklist = {
                "old": datetime.now(timezone.utc) - timedelta(minutes=1),
                "new": datetime.now(timezone.utc) + timedelta(minutes=5)
            }
            service._cleanup_memory_blacklist()
            assert "old" not in service._memory_blacklist
            assert "new" in service._memory_blacklist

    @pytest.mark.asyncio
    async def test_get_token_service_sync(self):
        """Test sync accessor for token service"""
        from services.token_service import get_token_service_sync
        with patch("services.token_service._token_service", None):
            service = get_token_service_sync()
            assert isinstance(service, TokenService)
