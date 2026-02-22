"""
Tests for Password Service

# nosec python:S2068 - Hardcoded passwords in this file are intentional test fixtures
# These are not real credentials; they are used only for unit testing password hashing
"""

from unittest.mock import MagicMock, patch

import pytest

from services.password_service import password_service


class TestPasswordService:
    """Test suite for PasswordService"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = password_service.hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = password_service.hash_password(password)
        result = password_service.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        hashed = password_service.hash_password(password)
        result = password_service.verify_password("wrong_password", hashed)
        assert result is False

    def test_verify_password_error(self):
        """Test password verification with invalid hash"""
        result = password_service.verify_password("password", "invalid_hash")
        assert result is False

    def test_validate_complexity(self):
        """Test password complexity validation"""
        assert password_service.validate_complexity("short") is False
        assert password_service.validate_complexity("long_enough_123") is True

    @pytest.mark.asyncio
    async def test_is_password_pwned_leaked(self):
        """Test HIBP check for leaked password"""
        import hashlib

        password = "password123"
        sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
        sha1[:5]
        suffix = sha1[5:]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = f"{suffix}:1234\nOTHER:1"

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await password_service.is_password_pwned(password)
            assert result is True

    @pytest.mark.asyncio
    async def test_is_password_pwned_safe(self):
        """Test HIBP check for safe password"""
        import hashlib

        password = "very_unique_password_2024"
        hashlib.sha1(password.encode()).hexdigest().upper()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "NOT_YOUR_SUFFIX:1"

        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await password_service.is_password_pwned(password)
            assert result is False

    @pytest.mark.asyncio
    async def test_is_password_pwned_error(self):
        """Test HIBP check with API error"""
        with patch("httpx.AsyncClient.get", side_effect=Exception("API Down")):
            result = await password_service.is_password_pwned("password123")
            assert result is False  # Should fail safe (not blocked)

    @pytest.mark.asyncio
    async def test_validate_new_password_too_short(self):
        """Test new password validation with short password"""
        is_valid, error = await password_service.validate_new_password("short")
        assert is_valid is False
        assert "at least 8 characters" in error

    @pytest.mark.asyncio
    async def test_validate_new_password_pwned(self):
        """Test new password validation with leaked password"""
        with patch.object(password_service, "is_password_pwned", return_value=True):
            is_valid, error = await password_service.validate_new_password("password123")
            assert is_valid is False
            assert "data breach" in error

    @pytest.mark.asyncio
    async def test_validate_new_password_success(self):
        """Test new password validation success"""
        with patch.object(password_service, "is_password_pwned", return_value=False):
            is_valid, error = await password_service.validate_new_password("secure_password_123")
            assert is_valid is True
            assert error is None
