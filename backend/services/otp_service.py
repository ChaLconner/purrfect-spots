"""
OTP Service for email verification
Generates, stores, and verifies 6-digit OTP codes
"""

import hashlib
import secrets
from datetime import timedelta

from dependencies import get_supabase_admin_client
from exceptions import ExternalServiceError, PurrfectSpotsException
from logger import logger
from utils.datetime_utils import utc_now

TIMEZONE_UTC_OFFSET = "+00:00"


class OTPService:
    """Service for managing OTP verification codes"""

    OTP_EXPIRY_MINUTES = 10  # OTP valid for 10 minutes (NIST/OWASP recommendation)
    MAX_ATTEMPTS = 5  # Maximum verification attempts per OTP
    RESEND_COOLDOWN_SECONDS = 60  # Minimum time between resends
    LOCKOUT_DURATION_MINUTES = 15  # Account lockout duration after max attempts

    def __init__(self):
        self.supabase = get_supabase_admin_client()

    def _generate_otp(self) -> str:
        """Generate cryptographically secure 6-digit OTP"""
        # Use secrets module for cryptographic randomness
        return str(secrets.randbelow(900000) + 100000)  # Ensures 6 digits (100000-999999)

    def _hash_otp(self, otp: str) -> str:
        """Hash OTP using SHA-256 for secure storage"""
        return hashlib.sha256(otp.encode()).hexdigest()

    def _constant_time_compare(self, val1: str, val2: str) -> bool:
        """Constant-time comparison to prevent timing attacks"""
        return secrets.compare_digest(val1, val2)

    async def _is_email_locked_out(self, email: str) -> bool:
        """
        Check if email is currently locked out due to too many failed attempts.
        Uses Redis if available, otherwise falls back to database.
        """
        try:
            # Try Redis first for performance
            import os

            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                try:
                    import redis.asyncio as aioredis

                    redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False)
                    lockout_key = f"otp_lockout:{email}"
                    exists = await redis_client.exists(lockout_key)
                    await redis_client.close()
                    return bool(exists)
                except Exception:
                    pass

            # Fallback to database check
            result = (
                self.supabase.table("email_verifications")
                .select("locked_until")
                .eq("email", email)
                .is_("verified_at", "null")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data and result.data[0].get("locked_until"):
                from datetime import datetime

                locked_until = datetime.fromisoformat(result.data[0]["locked_until"].replace("Z", TIMEZONE_UTC_OFFSET))
                return utc_now() < locked_until

            return False
        except Exception:
            # On error, allow attempt (fail open for lockout check)
            return False

    async def _lockout_email(self, email: str) -> None:
        """
        Lock out email for specified duration after too many failed attempts.
        Uses Redis if available, otherwise falls back to database.
        """
        try:
            locked_until = utc_now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)

            # Try Redis first for performance
            import os

            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                try:
                    import redis.asyncio as aioredis

                    redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False)
                    lockout_key = f"otp_lockout:{email}"
                    await redis_client.setex(lockout_key, self.LOCKOUT_DURATION_MINUTES * 60, locked_until.isoformat())
                    await redis_client.close()
                    logger.info("Email locked out in Redis: %s until %s", email, locked_until.isoformat())
                    return
                except Exception:
                    pass

            # Fallback to database
            result = (
                self.supabase.table("email_verifications")
                .select("id")
                .eq("email", email)
                .is_("verified_at", "null")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                self.supabase.table("email_verifications").update({"locked_until": locked_until.isoformat()}).eq(
                    "id", result.data[0]["id"]
                ).execute()
                logger.info("Email locked out in database: %s until %s", email, locked_until.isoformat())
        except Exception as e:
            logger.error("Failed to lock out email: %s", e)

    async def _clear_email_lockout(self, email: str) -> None:
        """
        Clear email lockout after successful verification.
        Uses Redis if available, otherwise falls back to database.
        """
        try:
            # Try Redis first for performance
            import os

            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                try:
                    import redis.asyncio as aioredis

                    redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False)
                    lockout_key = f"otp_lockout:{email}"
                    await redis_client.delete(lockout_key)
                    await redis_client.close()
                    return
                except Exception:
                    pass

            # Fallback to database
            result = (
                self.supabase.table("email_verifications")
                .select("id")
                .eq("email", email)
                .is_("verified_at", "null")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                self.supabase.table("email_verifications").update({"locked_until": None}).eq(
                    "id", result.data[0]["id"]
                ).execute()
        except Exception as e:
            logger.error("Failed to clear email lockout: %s", e)

    def create_otp(self, email: str) -> tuple[str, str]:
        """
        Create and store OTP for email verification

        Args:
            email: User's email address

        Returns:
            Tuple of (otp_code, expires_at_iso)
        """
        try:
            # Invalidate any existing OTPs for this email
            self.invalidate_existing_otps(email)

            # Generate new OTP
            otp = self._generate_otp()
            otp_hash = self._hash_otp(otp)
            expires_at = utc_now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)

            # Store in database
            result = (
                self.supabase.table("email_verifications")
                .insert(
                    {
                        "email": email.lower(),
                        "otp_hash": otp_hash,
                        "attempts": 0,
                        "max_attempts": self.MAX_ATTEMPTS,
                        "expires_at": expires_at.isoformat(),
                    }
                )
                .execute()
            )

            if not result.data:
                raise ExternalServiceError("Failed to store OTP", service="Database")

            logger.info("OTP created and session initiated")
            return otp, expires_at.isoformat()

        except Exception:
            logger.error("Failed to create OTP")
            raise PurrfectSpotsException("Failed to generate verification code", error_code="INTERNAL_ERROR")

    async def verify_otp(self, email: str, otp: str) -> dict:
        """
        Verify OTP code

        Args:
            email: User's email address
            otp: 6-digit OTP code

        Returns:
            Dict with verification result:
            - success: bool
            - error: str (if failed)
            - attempts_remaining: int (if failed)
        """
        try:
            email_lower = email.lower()

            # SECURITY: Check if email is locked out due to too many failed attempts
            if await self._is_email_locked_out(email_lower):
                logger.warning("OTP verification attempted for locked out email: %s", email_lower)
                return {
                    "success": False,
                    "error": "Too many failed verification attempts. Please try again later.",
                    "attempts_remaining": 0,
                }

            # Get latest OTP record for this email
            result = (
                self.supabase.table("email_verifications")
                .select("*")
                .eq("email", email_lower)
                .is_("verified_at", "null")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not result.data:
                logger.warning("No pending OTP found")
                return {
                    "success": False,
                    "error": "No pending verification found. Please request a new code.",
                    "attempts_remaining": 0,
                }

            record = result.data[0]
            record_id = record["id"]
            stored_hash = record["otp_hash"]
            attempts = record["attempts"]
            max_attempts = record["max_attempts"]
            expires_at = record["expires_at"]

            # Check if expired
            from datetime import datetime

            expiry_time = datetime.fromisoformat(expires_at.replace("Z", TIMEZONE_UTC_OFFSET))
            if utc_now() > expiry_time:
                logger.warning("OTP expired")
                return {
                    "success": False,
                    "error": "Verification code has expired. Please request a new one.",
                    "attempts_remaining": 0,
                }

            # Check if max attempts exceeded
            if attempts >= max_attempts:
                # SECURITY: Lock out email for security after max attempts
                await self._lockout_email(email_lower)
                logger.warning("Max OTP attempts exceeded - locking out email: %s", email_lower)
                return {
                    "success": False,
                    "error": "Too many failed attempts. Please try again later.",
                    "attempts_remaining": 0,
                }

            # Verify OTP using constant-time comparison
            input_hash = self._hash_otp(otp)
            if self._constant_time_compare(input_hash, stored_hash):
                # Success - mark as verified and clear any lockout
                await self._clear_email_lockout(email_lower)
                self.supabase.table("email_verifications").update({"verified_at": utc_now().isoformat()}).eq(
                    "id", record_id
                ).execute()

                logger.info("OTP verified successfully")
                return {"success": True}
            else:
                # Failed - increment attempts
                new_attempts = attempts + 1
                self.supabase.table("email_verifications").update({"attempts": new_attempts}).eq(
                    "id", record_id
                ).execute()

                remaining = max_attempts - new_attempts
                logger.warning("Invalid OTP, %s attempts remaining", remaining)
                return {
                    "success": False,
                    "error": f"Invalid verification code. {remaining} attempts remaining.",
                    "attempts_remaining": remaining,
                }

        except Exception:
            logger.error("OTP verification error")
            return {"success": False, "error": "Verification failed. Please try again.", "attempts_remaining": 0}

    def invalidate_existing_otps(self, email: str) -> None:
        """Invalidate all existing OTPs for an email"""
        try:
            self.supabase.table("email_verifications").delete().eq("email", email.lower()).is_(
                "verified_at", "null"
            ).execute()
        except Exception:
            logger.warning("Failed to invalidate existing OTPs")

    def can_resend_otp(self, email: str) -> tuple[bool, int]:
        """
        Check if user can request a new OTP (cooldown check)

        Returns:
            Tuple of (can_resend, seconds_remaining)
        """
        try:
            email_lower = email.lower()

            # Get latest OTP record for this email
            result = (
                self.supabase.table("email_verifications")
                .select("created_at")
                .eq("email", email_lower)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

            if not result.data:
                return True, 0

            from datetime import datetime

            created_at = datetime.fromisoformat(result.data[0]["created_at"].replace("Z", TIMEZONE_UTC_OFFSET))
            elapsed = (utc_now() - created_at).total_seconds()

            if elapsed < self.RESEND_COOLDOWN_SECONDS:
                remaining = int(self.RESEND_COOLDOWN_SECONDS - elapsed)
                return False, remaining

            return True, 0

        except RuntimeError:
            logger.warning("Resend check error")
            return True, 0  # Allow resend on error


# Singleton instance
_otp_service: OTPService | None = None


def get_otp_service() -> OTPService:
    """Get OTP service singleton"""
    global _otp_service
    if _otp_service is None:
        _otp_service = OTPService()
    return _otp_service
