"""
Tests for Password Service

# nosec python:S2068 - Hardcoded passwords in this file are intentional test fixtures
# These are not real credentials; they are used only for unit testing password hashing
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.password_service import password_service


class TestPasswordService:
    """Test suite for PasswordService"""

    def test_hash_password(self) -> None:
        """Test password hashing"""
        password = "test_password_123"
        hashed = password_service.hash_password(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self) -> None:
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = password_service.hash_password(password)
        result = password_service.verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self) -> None:
        """Test password verification with incorrect password"""
        password = "test_password_123"
        hashed = password_service.hash_password(password)
        result = password_service.verify_password("wrong_password", hashed)
        assert result is False

    def test_verify_password_error(self) -> None:
        """Test password verification with invalid hash"""
        result = password_service.verify_password("password", "invalid_hash")
        assert result is False

    def test_validate_complexity(self) -> None:
        """Validate the minimum length without imposing character classes."""
        assert password_service.validate_complexity("short") is False
        assert password_service.validate_complexity("12345678901234") is False
        assert password_service.validate_complexity("123456789012345") is True

    @pytest.mark.asyncio
    async def test_is_password_pwned_leaked(self):
        """Test HIBP check for leaked password"""
        password = "correct horse battery staple"
        suffix = "AD6438836DBE526AA231ABDE2D0EEF74D42"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = f"{suffix}:1234\nOTHER:1"

        client = MagicMock(get=AsyncMock(return_value=mock_response))
        with patch("app.services.password_service.get_shared_httpx_client", return_value=client):
            result = await password_service.is_password_pwned(password)
            assert result is True

    @pytest.mark.asyncio
    async def test_is_password_pwned_safe(self):
        """Test HIBP check for safe password"""
        password = "very_unique_password_2024"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "NOT_YOUR_SUFFIX:1"

        client = MagicMock(get=AsyncMock(return_value=mock_response))
        with patch("app.services.password_service.get_shared_httpx_client", return_value=client):
            result = await password_service.is_password_pwned(password)
            assert result is False

    @pytest.mark.asyncio
    async def test_is_password_pwned_error(self):
        """Test HIBP check with API error"""
        client = MagicMock(get=AsyncMock(side_effect=Exception("API Down")))
        with patch("app.services.password_service.get_shared_httpx_client", return_value=client):
            result = await password_service.is_password_pwned("password123")
            assert result is False  # Should fail safe (not blocked)

    @pytest.mark.asyncio
    async def test_validate_new_password_rejects_password_shorter_than_minimum(self):
        """New passwords shorter than fifteen characters are rejected."""
        with patch.object(password_service, "is_password_pwned", return_value=False):
            is_valid, error = await password_service.validate_new_password("short")

        assert is_valid is False
        assert error == "Password must be at least 15 characters."

    @pytest.mark.asyncio
    async def test_validate_new_password_accepts_fifteen_character_passphrase(self):
        """Exactly fifteen characters is the inclusive minimum."""
        with patch.object(password_service, "is_password_pwned", return_value=False):
            is_valid, error = await password_service.validate_new_password("123456789012345")

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_new_password_rejects_empty_password(self):
        """An empty value is still not a password."""
        is_valid, error = await password_service.validate_new_password("")

        assert is_valid is False
        assert error == "Password is required."

    @pytest.mark.asyncio
    async def test_validate_new_password_pwned(self):
        """Test new password validation with leaked password"""
        with patch.object(password_service, "is_password_pwned", return_value=True):
            is_valid, error = await password_service.validate_new_password("PwnedPassphrase123!")
            assert is_valid is False
            assert error is not None
            assert "data breach" in error

    @pytest.mark.asyncio
    async def test_validate_new_password_success(self):
        """Test new password validation success"""
        with patch.object(password_service, "is_password_pwned", return_value=False):
            is_valid, error = await password_service.validate_new_password("secure-test-passphrase")
            assert is_valid is True
            assert error is None
