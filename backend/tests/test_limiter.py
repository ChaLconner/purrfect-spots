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
        request.client.host = "192.168.1.1"
        return request

    def test_get_user_id_from_request_with_valid_token(self, mock_request):
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

        assert result == "user:user-123"

    def test_get_user_id_from_request_with_user_id_claim(self, mock_request):
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

        assert result == "user:user-456"

    def test_get_user_id_from_request_no_auth_header(self, mock_request):
        """Test fallback to IP when no Authorization header"""
        mock_request.headers = {}

        with patch("limiter.get_remote_address") as mock_get_ip:
            mock_get_ip.return_value = "192.168.1.1"

            from limiter import get_user_id_from_request

            result = get_user_id_from_request(mock_request)

            assert result == "192.168.1.1"

    def test_get_user_id_from_request_invalid_token(self, mock_request):
        """Test fallback to IP when token is invalid"""
        mock_request.headers = {"Authorization": "Bearer invalid-token"}

        with patch("limiter.get_remote_address") as mock_get_ip:
            mock_get_ip.return_value = "192.168.1.1"

            from limiter import get_user_id_from_request

            result = get_user_id_from_request(mock_request)

            # Should fallback to IP
            assert result == "192.168.1.1"

    def test_get_identifier_with_endpoint(self, mock_request):
        """Test combined user/endpoint identifier"""
        mock_request.headers = {}
        mock_request.url.path = "/api/v1/upload/cat"

        with patch("limiter.get_remote_address") as mock_get_ip:
            mock_get_ip.return_value = "10.0.0.1"

            from limiter import get_identifier_with_endpoint

            result = get_identifier_with_endpoint(mock_request)

            assert result == "10.0.0.1:/api/v1/upload/cat"


class TestRedisConfiguration:
    """Test Redis configuration functions"""

    def test_get_redis_url_not_configured(self):
        """Test behavior when REDIS_URL is not set"""
        # Ensure no REDIS_URL from real environment leaks in
        with patch("config.config.REDIS_URL", None):
            from limiter import get_redis_url

            result = get_redis_url()
            assert result is None

    def test_get_redis_url_valid_format(self):
        """Test with valid Redis URL format"""
        with patch("config.config.REDIS_URL", "redis://localhost:6379/0"):
            from limiter import get_redis_url

            result = get_redis_url()
            assert result == "redis://localhost:6379/0"

    def test_get_redis_url_invalid_format(self):
        """Test with invalid Redis URL format"""
        with patch("config.config.REDIS_URL", "http://localhost:6379"):
            from limiter import get_redis_url

            result = get_redis_url()
            assert result is None

    def test_get_redis_url_ssl_format(self):
        """Test with Redis SSL URL format"""
        with patch("config.config.REDIS_URL", "rediss://user:pass@prod.redis.io:6380"):
            from limiter import get_redis_url

            result = get_redis_url()
            assert result == "rediss://user:pass@prod.redis.io:6380"

    def test_test_redis_connection_success(self):
        """Test successful Redis connection"""
        with patch("redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            from limiter import test_redis_connection

            result = test_redis_connection("redis://localhost:6379")

            assert result is True
            mock_client.ping.assert_called_once()

    def test_test_redis_connection_failure(self):
        """Test failed Redis connection"""
        with patch("redis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection refused")

            from limiter import test_redis_connection

            result = test_redis_connection("redis://localhost:6379")

            assert result is False

    def test_test_redis_connection_import_error(self):
        """Test that connection errors are handled gracefully"""
        # The test_redis_connection function handles errors gracefully.
        # We test connection failure scenario which returns False
        from limiter import test_redis_connection

        # Test with an invalid URI that will cause connection failure
        result = test_redis_connection("redis://invalid-host-that-does-not-exist:6379")
        assert result is False


class TestRateLimitInfo:
    """Test rate limit info function"""

    def test_get_rate_limit_info_memory_storage(self):
        """Test rate limit info with in-memory storage"""
        with patch("limiter._storage_uri", None), patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = None

            from limiter import get_rate_limit_info

            info = get_rate_limit_info()

            assert info["storage_type"] == "memory"
            assert "limits" in info
            assert "default" in info["limits"]

    def test_get_rate_limit_info_redis_storage(self):
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

    def test_limiter_exists(self):
        """Test that main limiter is created"""
        from limiter import limiter

        assert limiter is not None

    def test_strict_limiter_exists(self):
        """Test that strict limiter is created"""
        from limiter import strict_limiter

        assert strict_limiter is not None

    def test_upload_limiter_exists(self):
        """Test that upload limiter is created"""
        from limiter import upload_limiter

        assert upload_limiter is not None

    def test_auth_limiter_exists(self):
        """Test that auth limiter is created"""
        from limiter import auth_limiter

        assert auth_limiter is not None
