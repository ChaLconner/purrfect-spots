"""
Tests for OTP service
"""
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.otp_service import OTPService


class TestOTPService:
    @pytest.fixture
    def mock_supabase_admin(self):
        """Mock Supabase admin client"""
        mock = MagicMock()
        mock.table.return_value = mock
        mock.insert.return_value = mock
        mock.select.return_value = mock
        mock.update.return_value = mock
        mock.delete.return_value = mock
        mock.eq.return_value = mock
        mock.is_.return_value = mock
        mock.order.return_value = mock
        mock.limit.return_value = mock
        mock.execute.return_value = MagicMock(data=[], count=0)
        return mock

    @pytest.fixture
    def mock_redis_none(self):
        """Mock REDIS_URL to be None to test DB fallbacks"""
        with patch.dict(os.environ, {"REDIS_URL": ""}):
            yield

    @pytest.fixture
    def otp_service(self, mock_supabase_admin):
        """Create OTPService instance with mocked dependencies"""
        with patch("services.otp_service.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = OTPService()
            return service

    def test_generate_otp(self, otp_service):
        """Test OTP generation format"""
        otp = otp_service._generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()

    @pytest.mark.asyncio
    async def test_create_otp_success(self, otp_service, mock_supabase_admin):
        """Test successful OTP creation"""
        email = "test@example.com"
        mock_supabase_admin.execute.return_value = MagicMock(data=[{"id": 1}])
        
        otp, expires_at = otp_service.create_otp(email)
        
        assert len(otp) == 6
        assert expires_at is not None
        mock_supabase_admin.insert.assert_called_once()
        assert mock_supabase_admin.insert.call_args[0][0]["email"] == email

    @pytest.mark.asyncio
    async def test_verify_otp_success(self, otp_service, mock_supabase_admin):
        """Test successful OTP verification"""
        email = "test@example.com"
        otp = "123456"
        otp_hash = otp_service._hash_otp(otp)
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        
        mock_supabase_admin.execute.return_value = MagicMock(data=[{
            "id": "rec-1",
            "otp_hash": otp_hash,
            "attempts": 0,
            "max_attempts": 5,
            "expires_at": expires_at
        }])
        
        result = await otp_service.verify_otp(email, otp)
        
        assert result["success"] is True
        mock_supabase_admin.update.assert_called()
        assert "verified_at" in mock_supabase_admin.update.call_args[0][0]

    @pytest.mark.asyncio
    async def test_verify_otp_invalid(self, otp_service, mock_supabase_admin):
        """Test invalid OTP verification"""
        email = "test@example.com"
        stored_hash = otp_service._hash_otp("000000")
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        
        mock_supabase_admin.execute.return_value = MagicMock(data=[{
            "id": "rec-1",
            "otp_hash": stored_hash,
            "attempts": 0,
            "max_attempts": 5,
            "expires_at": expires_at
        }])
        
        result = await otp_service.verify_otp(email, "123456")
        
        assert result["success"] is False
        assert "Invalid" in result["error"]
        assert result["attempts_remaining"] == 4

    @pytest.mark.asyncio
    async def test_verify_otp_expired(self, otp_service, mock_supabase_admin):
        """Test expired OTP verification"""
        email = "test@example.com"
        expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        
        mock_supabase_admin.execute.return_value = MagicMock(data=[{
            "id": "rec-1",
            "otp_hash": "hash",
            "attempts": 0,
            "max_attempts": 5,
            "expires_at": expires_at
        }])
        
        result = await otp_service.verify_otp(email, "123456")
        
        assert result["success"] is False
        assert "expired" in result["error"]

    @pytest.mark.asyncio
    async def test_verify_otp_not_found(self, otp_service, mock_supabase_admin):
        """Test OTP verification when no record exists"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[])
        result = await otp_service.verify_otp("none@test.com", "123456")
        assert result["success"] is False
        assert "no pending verification" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_lockout_logic_db(self, otp_service, mock_supabase_admin, mock_redis_none):
        """Test lockout logic using DB fallback"""
        email = "lockout@example.com"
        
        locked_until = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        mock_supabase_admin.execute.side_effect = [
            MagicMock(data=[{"locked_until": locked_until}]),
            MagicMock(data=[])
        ]
        
        result = await otp_service.verify_otp(email, "111111")
        assert result["success"] is False
        assert "too many failed" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_lockout_trigger(self, otp_service, mock_supabase_admin, mock_redis_none):
        """Test triggering lockout after max attempts"""
        email = "max@example.com"
        
        mock_supabase_admin.execute.side_effect = [
            MagicMock(data=[]), # Not locked out yet
            MagicMock(data=[{
                "id": "rec-1",
                "otp_hash": "somehash",
                "attempts": 5,
                "max_attempts": 5,
                "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
            }])
        ]
        
        result = await otp_service.verify_otp(email, "123456")
        assert result["success"] is False
        assert "too many failed" in result["error"].lower()

    def test_can_resend_otp(self, otp_service, mock_supabase_admin):
        """Test resend cooldown logic"""
        email = "resend@example.com"
        
        # Case 1: No previous OTP
        mock_supabase_admin.execute.return_value = MagicMock(data=[])
        can, remaining = otp_service.can_resend_otp(email)
        assert can is True
        
        # Case 2: Just sent (cooldown active)
        created_at = datetime.now(timezone.utc).isoformat()
        mock_supabase_admin.execute.return_value = MagicMock(data=[{"created_at": created_at}])
        can, remaining = otp_service.can_resend_otp(email)
        assert can is False
        assert remaining >= 0

    @pytest.mark.asyncio
    async def test_redis_error_fail_open(self, otp_service, mock_supabase_admin):
        """Test that Redis errors don't block operations (fail-open)"""
        email = "redis-err@example.com"
        with patch.dict(os.environ, {"REDIS_URL": "redis://localhost"}):
            with patch("redis.asyncio.from_url") as mock_redis:
                mock_redis.side_effect = Exception("Redis connection error")
                mock_supabase_admin.execute.return_value = MagicMock(data=[])
                is_locked = await otp_service._is_email_locked_out(email)
                assert is_locked is False

    @pytest.mark.asyncio
    async def test_clear_lockout_db(self, otp_service, mock_supabase_admin, mock_redis_none):
        """Test clearing lockout in DB"""
        email = "clear@example.com"
        mock_supabase_admin.execute.return_value = MagicMock(data=[{"id": "rec-1"}])
        await otp_service._clear_email_lockout(email)
        mock_supabase_admin.update.assert_called_with({"locked_until": None})
