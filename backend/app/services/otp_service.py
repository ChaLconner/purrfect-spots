"""
OTP Service for email verification
Generates, stores, and verifies 6-digit OTP codes
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, cast

from sqlalchemy import bindparam, column, desc, select, table, text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.logger import logger
from app.utils.datetime_utils import utc_now
from app.utils.exceptions import ExternalServiceError, PurrfectSpotsException

TIMEZONE_UTC_OFFSET = "+00:00"

_EMAIL_VERIFICATION_COLUMN_NAMES = (
    "id",
    "email",
    "otp_hash",
    "attempts",
    "max_attempts",
    "expires_at",
    "verified_at",
    "locked_until",
    "created_at",
)
_EMAIL_VERIFICATIONS = table(
    "email_verifications",
    *(column(name) for name in _EMAIL_VERIFICATION_COLUMN_NAMES),
)
_EMAIL_VERIFICATION_COLUMNS = {name: getattr(_EMAIL_VERIFICATIONS.c, name) for name in _EMAIL_VERIFICATION_COLUMN_NAMES}


class OTPService:
    """Service for managing OTP verification codes"""

    OTP_EXPIRY_MINUTES = 10  # OTP valid for 10 minutes (NIST/OWASP recommendation)
    MAX_ATTEMPTS = 5  # Maximum verification attempts per OTP
    RESEND_COOLDOWN_SECONDS = 60  # Minimum time between resends
    LOCKOUT_DURATION_MINUTES = 15  # Account lockout duration after max attempts

    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        # Consistent column selection for OTPs
        self.OTP_COLUMNS = "id, otp_hash, attempts, max_attempts, expires_at"

    def _generate_otp(self) -> str:
        """Generate cryptographically secure 6-digit OTP"""
        # Use secrets module for cryptographic randomness
        return str(secrets.randbelow(1000000)).zfill(6)

    def _hash_otp(self, otp: str) -> str:
        """Hash OTP using SHA-256 for secure storage"""
        return hashlib.sha256(otp.encode()).hexdigest()

    def _constant_time_compare(self, val1: str, val2: str) -> bool:
        """Constant-time comparison to prevent timing attacks"""
        return secrets.compare_digest(val1, val2)

    async def _run_redis_otp_op(self, action: str, email: str, val: Any = None) -> tuple[bool, Any]:
        """Helper to run Redis operations for OTP lockout."""
        import os

        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return False, None
        try:
            import redis.asyncio as aioredis

            async with aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False) as redis_client:
                lockout_key = f"otp_lockout:{email}"
                if action == "exists":
                    return True, bool(await redis_client.exists(lockout_key))
                if action == "setex":
                    await redis_client.setex(lockout_key, self.LOCKOUT_DURATION_MINUTES * 60, val)
                    return True, None
                if action == "delete":
                    await redis_client.delete(lockout_key)
                    return True, None
        except Exception as e:
            logger.debug(f"Redis {action} failed for {email}, falling back to DB: {e}")
        return False, None

    async def _is_email_locked_out(self, email: str) -> bool:
        """
        Check if email is currently locked out due to too many failed attempts.
        Uses Redis if available, otherwise falls back to database.
        """
        try:
            handled, res = await self._run_redis_otp_op("exists", email)
            if handled:
                return bool(res)

            # Fallback to database check
            rec = await self._fetch_pending_verification(email, "locked_until")
            if rec and rec.get("locked_until"):
                locked_until = datetime.fromisoformat(cast(str, rec["locked_until"]).replace("Z", TIMEZONE_UTC_OFFSET))
                return utc_now() < locked_until

            return False
        except Exception:
            # On error, allow attempt (fail open for lockout check)
            return False

    async def _fetch_pending_verification(self, email: str, columns: str) -> dict[str, Any] | None:
        """Fetch latest unverified email verification record by email."""
        if self.db:
            requested_columns = tuple(part.strip() for part in columns.split(",") if part.strip())
            try:
                selected_columns = [_EMAIL_VERIFICATION_COLUMNS[name] for name in requested_columns]
            except KeyError as exc:
                raise ValueError("Unsupported email verification column") from exc
            if not selected_columns:
                raise ValueError("At least one email verification column is required")

            query = (
                select(*selected_columns)
                .where(
                    _EMAIL_VERIFICATIONS.c.email == bindparam("email"),
                    _EMAIL_VERIFICATIONS.c.verified_at.is_(None),
                )
                .order_by(desc(_EMAIL_VERIFICATIONS.c.created_at))
                .limit(1)
            )
            result = await self.db.execute(query, {"email": email})
            row = result.fetchone()
            return dict(row._mapping) if row else None
        supa_res = (
            await self.supabase.table("email_verifications")
            .select(columns)
            .eq("email", email)
            .is_("verified_at", "null")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return cast(dict[str, Any], supa_res.data[0]) if supa_res.data else None

    async def _lockout_email(self, email: str) -> None:
        """
        Lock out email for specified duration after too many failed attempts.
        Uses Redis if available, otherwise falls back to database.
        """
        try:
            locked_until = utc_now() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            handled, _ = await self._run_redis_otp_op("setex", email, locked_until.isoformat())
            if handled:
                logger.info("Email locked out in Redis: %s until %s", email, locked_until.isoformat())
                return

            # Fallback to database
            await self._update_email_lockout_db(email, locked_until)
            logger.info("Email locked out in database: %s until %s", email, locked_until.isoformat())
        except Exception as e:
            logger.error("Failed to lock out email: %s", e)

    async def _update_email_lockout_db(self, email: str, locked_until: datetime | None) -> None:
        """Helper method to update locked_until in database or Supabase."""
        locked_iso = locked_until.isoformat() if locked_until else None
        rec = await self._fetch_pending_verification(email, "id")
        if rec and rec.get("id"):
            record_id = rec["id"]
            if self.db:
                await self.db.execute(
                    text("UPDATE email_verifications SET locked_until = :locked_until WHERE id = :id"),
                    {"locked_until": locked_iso, "id": record_id},
                )
                await self.db.commit()
            else:
                await (
                    self.supabase.table("email_verifications")
                    .update({"locked_until": locked_iso})
                    .eq("id", record_id)
                    .execute()
                )

    async def _clear_email_lockout(self, email: str) -> None:
        """
        Clear email lockout after successful verification.
        Uses Redis if available, otherwise falls back to database.
        """
        try:
            handled, _ = await self._run_redis_otp_op("delete", email)
            if handled:
                return

            # Fallback to database
            await self._update_email_lockout_db(email, None)
        except Exception as e:
            logger.error("Failed to clear email lockout: %s", e)

    async def create_otp(self, email: str) -> tuple[str, str]:
        """
        Create and store OTP for email verification (Async)
        """
        try:
            # Invalidate any existing OTPs for this email
            await self.invalidate_existing_otps(email)

            # Generate new OTP
            otp = self._generate_otp()
            otp_hash = self._hash_otp(otp)
            expires_at = utc_now() + timedelta(minutes=self.OTP_EXPIRY_MINUTES)

            # Store in database
            data = {
                "email": email.lower(),
                "otp_hash": otp_hash,
                "attempts": 0,
                "max_attempts": self.MAX_ATTEMPTS,
                "expires_at": expires_at.isoformat(),
            }
            if self.db:
                query = text(
                    "INSERT INTO email_verifications (email, otp_hash, attempts, max_attempts, expires_at) "
                    "VALUES (:email, :otp_hash, :attempts, :max_attempts, :expires_at)"
                )
                await self.db.execute(query, data)
                await self.db.commit()
            else:
                result = await self.supabase.table("email_verifications").insert(cast(dict[str, Any], data)).execute()

                if not result.data:
                    raise ExternalServiceError("Failed to store OTP", service="Database")

            logger.info("OTP created and session initiated")
            return otp, expires_at.isoformat()

        except Exception as e:
            logger.error("Failed to create OTP: %s", e)
            raise PurrfectSpotsException("Failed to generate verification code", error_code="INTERNAL_ERROR")

    async def verify_otp(self, email: str, otp: str) -> dict:
        """
        Verify OTP code (Async)
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
            record = await self._fetch_pending_verification(email_lower, self.OTP_COLUMNS)

            if not record:
                logger.warning("No pending OTP found")
                return {
                    "success": False,
                    "error": "No pending verification found. Please request a new code.",
                    "attempts_remaining": 0,
                }

            record_id = record["id"]
            stored_hash = record["otp_hash"]
            attempts = record["attempts"]
            max_attempts = record["max_attempts"]
            expires_at = record["expires_at"]

            # Check if expired
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
                if self.db:
                    query = text("UPDATE email_verifications SET verified_at = :now WHERE id = :id")
                    await self.db.execute(query, {"now": utc_now().isoformat(), "id": record_id})
                    await self.db.commit()
                else:
                    await (
                        self.supabase.table("email_verifications")
                        .update({"verified_at": utc_now().isoformat()})
                        .eq("id", record_id)
                        .execute()
                    )

                logger.info("OTP verified successfully")
                return {"success": True}

            # Failed - increment attempts
            new_attempts = attempts + 1
            if self.db:
                query = text("UPDATE email_verifications SET attempts = :attempts WHERE id = :id")
                await self.db.execute(query, {"attempts": new_attempts, "id": record_id})
                await self.db.commit()
            else:
                await (
                    self.supabase.table("email_verifications")
                    .update({"attempts": new_attempts})
                    .eq("id", record_id)
                    .execute()
                )

            remaining = max_attempts - new_attempts
            logger.warning("Invalid OTP, %s attempts remaining", remaining)
            return {
                "success": False,
                "error": f"Invalid verification code. {remaining} attempts remaining.",
                "attempts_remaining": remaining,
            }

        except Exception as e:
            logger.error("OTP verification error: %s", e)
            return {"success": False, "error": "Verification failed. Please try again.", "attempts_remaining": 0}

    async def invalidate_existing_otps(self, email: str) -> None:
        """Invalidate all existing OTPs for an email (Async)"""
        try:
            if self.db:
                query = text("DELETE FROM email_verifications WHERE email = :email AND verified_at IS NULL")
                await self.db.execute(query, {"email": email.lower()})
                await self.db.commit()
            else:
                await (
                    self.supabase.table("email_verifications")
                    .delete()
                    .eq("email", email.lower())
                    .is_("verified_at", "null")
                    .execute()
                )
        except Exception:
            logger.warning("Failed to invalidate existing OTPs")

    async def can_resend_otp(self, email: str) -> tuple[bool, int]:
        """
        Check if user can request a new OTP (cooldown check) (Async)
        """
        try:
            email_lower = email.lower()

            # Get latest OTP record for this email
            row_created_at = None
            if self.db:
                query = text(
                    "SELECT created_at FROM email_verifications WHERE email = :email ORDER BY created_at DESC LIMIT 1"
                )
                result = await self.db.execute(query, {"email": email_lower})
                row = result.fetchone()
                if row:
                    row_created_at = row[0]
            else:
                supa_res = (
                    await self.supabase.table("email_verifications")
                    .select("created_at")
                    .eq("email", email_lower)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
                if supa_res.data:
                    row_created_at = cast(dict[str, Any], supa_res.data[0])["created_at"]

            if not row_created_at:
                return True, 0

            created_at = datetime.fromisoformat(row_created_at.replace("Z", TIMEZONE_UTC_OFFSET))
            elapsed = (utc_now() - created_at).total_seconds()

            if elapsed < self.RESEND_COOLDOWN_SECONDS:
                remaining = int(self.RESEND_COOLDOWN_SECONDS - elapsed)
                return False, remaining

            return True, 0

        except Exception:
            logger.warning("Resend check error")
            return True, 0  # Allow resend on error
