"""
Tests for Password Service

# nosec python:S2068 - Hardcoded passwords in this file are intentional test fixtures
# These are not real credentials; they are used only for unit testing password hashing
"""

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
