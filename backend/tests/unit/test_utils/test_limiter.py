"""
Tests for rate limiter functionality

# nosec python:S1313 - Hardcoded IP addresses in this file are intentional test fixtures
# These are private/test IPs used only for unit testing rate limiting, not real addresses
"""

from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import Request


class TestRateLimiterKeyFunctions:
    """Test key extraction functions for rate limiting"""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request"""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.url = MagicMock()
        request.url.path = "/api/v1/gallery"
        request.client = MagicMock()
        request.client.host = "192.168.1.1"  # NOSONAR python:S1313 - test fixture IP
        return request

    def test_get_user_id_from_request_with_valid_token(self, mock_request) -> None:
        """Test extracting user ID from valid JWT token"""
        # Create a test JWT (not signed, just for ID extraction)
        # Patch config.JWT_SECRET to match the token's secret
        with patch("config.config.JWT_SECRET", "secret_key_at_least_32_chars_long_for_security"):
            test_token = jwt.encode(
                {"sub": "user-123", "iss": "purrfect-spots"},
                "secret_key_at_least_32_chars_long_for_security",
                algorithm="HS256",
            )
            mock_request.headers = {"Authorization": f"Bearer {test_token}"}

            from limiter import get_user_id_from_request

            result = get_user_id_from_request(mock_request)

        assert result == "user:user-123:free"

    def test_get_user_id_from_request_with_user_id_claim(self, mock_request) -> None:
        """Test extracting user ID from token with user_id claim"""
        # Patch config.JWT_SECRET to match the token's secret
        with patch("config.config.JWT_SECRET", "secret_key_at_least_32_chars_long_for_security"):
            test_token = jwt.encode(
                {"user_id": "user-456", "iss": "purrfect-spots"},
                "secret_key_at_least_32_chars_long_for_security",
                algorithm="HS256",
            )
            mock_request.headers = {"Authorization": f"Bearer {test_token}"}

            from limiter import get_user_id_from_request

            result = get_user_id_from_request(mock_request)

        assert result == "user:user-456:free"

    def test_get_user_id_from_request_no_auth_header(self, mock_request) -> None:
        """Test fallback to IP when no Authorization header"""
        mock_request.headers = {}

        with patch("limiter.get_remote_address") as mock_get_ip:
            mock_get_ip.return_value = "192.168.1.1"  # NOSONAR python:S1313 - test fixture IP

            from limiter import get_user_id_from_request

            result = get_user_id_from_request(mock_request)

            assert result == "192.168.1.1:free"  # NOSONAR python:S1313 - test fixture IP

    def test_get_user_id_from_request_invalid_token(self, mock_request) -> None:
        """Test fallback to IP when token is invalid"""
        mock_request.headers = {"Authorization": "Bearer invalid-token"}

        with patch("limiter.get_remote_address") as mock_get_ip:
            mock_get_ip.return_value = "192.168.1.1"  # NOSONAR python:S1313 - test fixture IP

            from limiter import get_user_id_from_request

            result = get_user_id_from_request(mock_request)

            # Should fallback to IP
            assert result == "192.168.1.1:free"  # NOSONAR python:S1313 - test fixture IP

    def test_get_identifier_with_endpoint(self, mock_request) -> None:
        """Test combined user/endpoint identifier"""
        mock_request.headers = {}
        mock_request.url.path = "/api/v1/upload/cat"

        with patch("limiter.get_remote_address") as mock_get_ip:
            mock_get_ip.return_value = "10.0.0.1"  # NOSONAR python:S1313 - test fixture IP

            from limiter import get_identifier_with_endpoint

            result = get_identifier_with_endpoint(mock_request)

            assert result == "10.0.0.1:free:/api/v1/upload/cat"  # NOSONAR python:S1313 - test fixture IP


class TestRedisConfiguration:
    """Test Redis configuration functions"""

    def test_get_redis_url_not_configured(self) -> None:
        """Test behavior when REDIS_URL is not set"""
        # Ensure no REDIS_URL from real environment leaks in
        with patch("config.config.REDIS_URL", None):
            from limiter import get_redis_url

            result = get_redis_url()
            assert result is None

    def test_get_redis_url_valid_format(self) -> None:
        """Test with valid Redis URL format"""
        with patch("config.config.REDIS_URL", "redis://localhost:6379/0"):
            from limiter import get_redis_url

            result = get_redis_url()
            assert result == "redis://localhost:6379/0"

    def test_get_redis_url_invalid_format(self) -> None:
        """Test with invalid Redis URL format"""
        with patch(
            "config.config.REDIS_URL", "http://localhost:6379"
        ):  # NOSONAR python:S5332 - tests rejection of non-redis URL format
            from limiter import get_redis_url

            result = get_redis_url()
            assert result is None

    def test_get_redis_url_ssl_format(self) -> None:
        """Test with Redis SSL URL format"""
        with patch("config.config.REDIS_URL", "rediss://user:pass@prod.redis.io:6380"):
            from limiter import get_redis_url

            result = get_redis_url()
            assert result == "rediss://user:pass@prod.redis.io:6380"

    def test_test_redis_connection_success(self) -> None:
        """Test successful Redis connection"""
        with patch("redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            from limiter import test_redis_connection

            result = test_redis_connection("redis://localhost:6379")

            assert result is True
            mock_client.ping.assert_called_once()

    def test_test_redis_connection_failure(self) -> None:
        """Test failed Redis connection"""
        with patch("redis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")

            from limiter import test_redis_connection

            result = test_redis_connection("redis://localhost:6379")

            assert result is False

    def test_test_redis_connection_import_error(self) -> None:
        """Test that connection errors are handled gracefully"""
        # The test_redis_connection function handles errors gracefully.
        # We test connection failure scenario which returns False
        from limiter import test_redis_connection

        # Test with an invalid URI that will cause connection failure
        result = test_redis_connection("redis://invalid-host-that-does-not-exist:6379")
        assert result is False


class TestRateLimitInfo:
    """Test rate limit info function"""

    def test_get_rate_limit_info_memory_storage(self) -> None:
        """Test rate limit info with in-memory storage"""
        with patch("limiter._storage_uri", None), patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = None

            from limiter import get_rate_limit_info

            info = get_rate_limit_info()

            assert info["storage_type"] == "memory"
            assert "limits" in info
            assert "default" in info["limits"]

    def test_get_rate_limit_info_redis_storage(self) -> None:
        """Test rate limit info with Redis storage"""
        # This test verifies the function returns correct format
        # Actual storage type depends on whether Redis is available
        from limiter import get_rate_limit_info

        info = get_rate_limit_info()

        # Should always have these keys
        assert "storage_type" in info
        assert "limits" in info
        assert info["storage_type"] in ["memory", "redis"]

        # If Redis is configured and connected, it should be redis
        if info.get("redis_connected"):
            assert info["storage_type"] == "redis"


class TestLimiterInstances:
    """Test limiter instance configurations"""

    def test_limiter_exists(self) -> None:
        """Test that main limiter is created"""
        from limiter import limiter

        assert limiter is not None

    def test_strict_limiter_exists(self) -> None:
        """Test that strict limiter is created"""
        from limiter import strict_limiter

        assert strict_limiter is not None

    def test_upload_limiter_exists(self) -> None:
        """Test that upload limiter is created"""
        from limiter import upload_limiter

        assert upload_limiter is not None

    def test_auth_limiter_exists(self) -> None:
        """Test that auth limiter is created"""
        from limiter import auth_limiter

        assert auth_limiter is not None


class TestTieredRateLimiting:
    """Test tiered rate limiting logic"""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request"""
        request = MagicMock(spec=Request)
        request.headers = {}
        return request

    def test_get_user_tier_free_default(self, mock_request) -> None:
        """Test that default tier is free for unauthenticated/anonymous users"""
        mock_request.headers = {}
        from limiter import get_user_tier

        assert get_user_tier(mock_request) == "free"

    def test_get_user_tier_pro(self, mock_request) -> None:
        """Test extracting pro tier from valid JWT token"""
        with patch("config.config.JWT_SECRET", "secret_key_at_least_32_chars_long_for_security"):
            test_token = jwt.encode(
                {"sub": "user-123", "app_metadata": {"tier": "pro"}, "iss": "purrfect-spots"},
                "secret_key_at_least_32_chars_long_for_security",
                algorithm="HS256",
            )
            mock_request.headers = {"Authorization": f"Bearer {test_token}"}
            from limiter import get_user_tier

            assert get_user_tier(mock_request) == "pro"

    def test_get_user_tier_free_explicit(self, mock_request) -> None:
        """Test extracting free tier from valid JWT token"""
        with patch("config.config.JWT_SECRET", "secret_key_at_least_32_chars_long_for_security"):
            test_token = jwt.encode(
                {"sub": "user-123", "app_metadata": {"tier": "free"}, "iss": "purrfect-spots"},
                "secret_key_at_least_32_chars_long_for_security",
                algorithm="HS256",
            )
            mock_request.headers = {"Authorization": f"Bearer {test_token}"}
            from limiter import get_user_tier

            assert get_user_tier(mock_request) == "free"

    def test_dynamic_limit_resolvers(self, mock_request) -> None:
        """Test dynamic limit resolver functions"""
        from config import config
        from limiter import get_api_limit, get_strict_limit, get_upload_limit

        # Mock free user
        # Note: resolvers now expect the key string containing the tier
        assert get_strict_limit("user:123:free") == config.RATE_LIMIT_STRICT_FREE
        assert get_upload_limit("user:123:free") == config.RATE_LIMIT_UPLOAD_FREE
        assert get_api_limit("user:123:free") == config.RATE_LIMIT_API_FREE

        # Mock pro user
        assert get_strict_limit("user:123:pro") == config.RATE_LIMIT_STRICT_PRO
        assert get_upload_limit("user:123:pro") == config.RATE_LIMIT_UPLOAD_PRO
        assert get_api_limit("user:123:pro") == config.RATE_LIMIT_API_PRO
