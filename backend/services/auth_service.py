"""
Authentication service for Google OAuth and traditional email/password auth
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import jwt
from supabase import Client, create_client

from config import config
from dependencies import get_supabase_admin_client
from logger import logger
from schemas.auth import LoginResponse
from services.email_service import email_service
from services.google_auth_service import google_auth_service
from services.password_service import password_service
from services.token_service import get_token_service
from services.user_service import UserService
from user_models.user import User, UserResponse
from utils.datetime_utils import utc_now
from utils.security import log_security_event

try:
    from redis.exceptions import RedisError
except ImportError:
    class RedisError(Exception):  # type: ignore
        """Fallback if redis is not installed"""
        pass



class AuthService:
    MAX_CONCURRENT_SESSIONS = 5  # Maximum concurrent sessions per user

    def __init__(self, supabase_client: Client) -> None:
        self.supabase = supabase_client
        self.supabase_admin = get_supabase_admin_client()
        self.user_service = UserService(supabase_client)
        self.jwt_secret = config.JWT_SECRET
        self.jwt_algorithm = config.JWT_ALGORITHM
        self.jwt_expiration_hours = config.JWT_ACCESS_EXPIRATION_HOURS

        if not self.jwt_secret:
            raise ValueError("JWT_SECRET is not configured")

    def _find_or_create_google_user(self, user_info: dict[str, Any], google_id: str) -> dict[str, Any]:
        """Find existing user by Google ID or prepare data for new user"""
        existing_user = None
        try:
            # Use admin client to check existence
            res = self.supabase_admin.table("users").select("id").eq("google_id", google_id).execute()
            if res.data:
                existing_user = res.data[0]
        except Exception as e:
            logger.debug("Identity check unsuccessful: %s", e)

        user_id = existing_user["id"] if existing_user else str(uuid.uuid4())

        return {
            "id": user_id,
            "sub": user_id,
            "google_id": google_id,
            "email": user_info["email"],
            "name": user_info["name"],
            "picture": user_info.get("picture", ""),
        }

    def _generate_fingerprint(self, ip: str, user_agent: str) -> str:
        """Generate SHA256 fingerprint from IP (subnet) and User-Agent"""
        if not user_agent:
            user_agent = "unknown"

        ip_segment = "unknown"
        if ip:
            if "." in ip:  # IPv4
                parts = ip.split(".")
                if len(parts) >= 2:
                    ip_segment = f"{parts[0]}.{parts[1]}"
            elif ":" in ip:  # IPv6
                parts = ip.split(":")
                if len(parts) >= 3:
                    ip_segment = f"{parts[0]}:{parts[1]}:{parts[2]}"

        raw = f"{user_agent}|{ip_segment}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token JTI is in blacklist"""
        if not jti:
            return False

        try:
            token_service = await get_token_service()
            return await token_service.is_blacklisted(jti=jti)
        except Exception as e:
            logger.error("Failed to check revocation status: %s", e)
            # SECURITY: Fail closed for token revocation check
            return True

    async def revoke_token(self, jti: str, user_id: str, expires_at: datetime) -> bool:
        """Add token to blacklist"""
        try:
            token_service = await get_token_service()
            return await token_service.blacklist_token(
                token=None, jti=jti, user_id=user_id, expires_at=expires_at, reason="logout"
            )
        except Exception as e:
            logger.error("Failed to revoke session: %s", e)
            return False

    def verify_google_token(self, token: str) -> dict[str, Any]:
        """Verify Google OAuth token - Delegated to GoogleAuthService"""
        return google_auth_service.verify_google_token(token)

    def create_or_get_user(self, user_data: dict[str, Any]) -> User:
        """Delegated to UserService"""
        return self.user_service.create_or_get_user(user_data)

    def create_access_token(self, user_id: str, user_data: dict[str, Any] | None = None, role: str = "user") -> str:
        """Create JWT access token with user data"""
        expire = utc_now() + timedelta(hours=self.jwt_expiration_hours)
        jti = str(uuid.uuid4())

        to_encode = {
            "user_id": user_id,
            "sub": user_id,
            "role": role,
            "jti": jti,
            "exp": expire,
            "iat": utc_now(),
        }

        if user_data:
            to_encode.update(
                {
                    "email": user_data.get("email", ""),
                    "user_metadata": {
                        "name": user_data.get("name", ""),
                        "avatar_url": user_data.get("picture", ""),
                        "provider_id": user_data.get("google_id"),
                    },
                    "app_metadata": {"provider": "google" if user_data.get("google_id") else "email"},
                }
            )

        return jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def _check_concurrent_sessions(self, user_id: str) -> bool:
        """
        Check if user has exceeded maximum concurrent sessions.
        Uses Redis if available, otherwise falls back to database.
        """
        try:
            active_sessions = await self._get_active_session_count(user_id)
            if active_sessions > self.MAX_CONCURRENT_SESSIONS:
                logger.warning("User %s exceeded max concurrent sessions: %d", user_id, active_sessions)
                return False
            return True
        except RedisError as e:
            logger.error("Redis error while checking sessions: %s", e)
            # Fail open on Redis error to avoid blocking users
            return True
        except Exception as e:
            logger.error("Failed to check concurrent sessions: %s", e)
            return True

    async def _get_active_session_count(self, user_id: str) -> int:
        """Helper to get active session count from Redis or DB"""
        token_service = await get_token_service()
        if token_service.redis:
            count = await self._get_redis_session_count(user_id, token_service.redis)
            if count is not None:
                return count
        return self._get_db_session_count(user_id)

    async def _get_redis_session_count(self, user_id: str, redis_client: Any) -> int | None:
        try:
            session_count_key = f"user_sessions:{user_id}"
            session_count = await redis_client.incr(session_count_key)
            await redis_client.expire(session_count_key, self.jwt_expiration_hours * 3600)
            return int(session_count)
        except Exception as e:
            logger.warning("Failed to get session count from Redis: %s", e)
            return None

    def _get_db_session_count(self, user_id: str) -> int:
        result = self.supabase_admin.table("token_blacklist").select("*").eq("user_id", user_id).execute()
        if not result.data:
            return 0
        now = utc_now()
        return sum(
            1 for entry in result.data if datetime.fromisoformat(entry["expires_at"].replace("Z", "+00:00")) > now
        )

    async def _check_user_invalidated(self, user_id: str, iat: int) -> bool:
        """Check if user has been globally invalidated"""
        try:
            token_service = await get_token_service()
            token_issued_at = datetime.fromtimestamp(iat, timezone.utc)
            return await token_service.is_user_invalidated(user_id, token_issued_at)
        except Exception as e:
            logger.warning("Session invalidation check failed: %s", e)
            return False

    def verify_access_token(self, token: str) -> str | None:
        """Verify JWT access token and return user_id"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload.get("user_id")
        except jwt.PyJWTError:
            return None

    def get_user_by_id(self, user_id: str) -> User | None:
        """Delegated to UserService"""
        return self.user_service.get_user_by_id(user_id)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Delegated to UserService"""
        return self.user_service.get_user_by_email(email)

    def create_user_with_password(self, email: str, password: str, name: str) -> dict[str, Any]:
        """Delegated to UserService (unverified flow)"""
        return self.user_service.create_unverified_user(email, password, name)

    def create_user(self, email: str, password: str, name: str) -> dict[str, Any]:
        return self.create_user_with_password(email, password, name)

    def confirm_user_email(self, email: str) -> bool:
        """Confirm user's email address (Admin API) - Logic specific to Auth/OTP flow"""
        try:
            # Need to find user first
            user_data = self.user_service.get_user_by_email(email)
            if not user_data:
                logger.error("User not found for email confirmation: %s", email)
                return False

            user_id = user_data["id"]
            self.supabase_admin.auth.admin.update_user_by_id(user_id, {"email_confirm": True})
            return True
        except Exception:
            logger.error("Failed to confirm email")
            return False

    def get_user_by_email_unverified(self, email: str) -> dict[str, Any] | None:
        """
        Get user by email, including unverified users.
        UserService.get_user_by_email wraps supabase select.
        """
        return self.user_service.get_user_by_email(email)

    def authenticate_user(self, email: str, password: str) -> dict[str, Any] | None:
        """Delegated to UserService"""
        return self.user_service.authenticate_user(email, password)

    async def update_user_profile(
        self, user_id: str, update_data: dict[str, Any], jwt_token: str | None = None
    ) -> dict[str, Any]:
        """Delegated to UserService"""
        return await self.user_service.update_user_profile(user_id, update_data, jwt_token=jwt_token)

    async def exchange_google_code(
        self, code: str, code_verifier: str, redirect_uri: str, ip: str | None = None, user_agent: str | None = None
    ) -> LoginResponse:
        """Exchange Google authorization code for access token using PKCE flow"""
        try:
            # Use GoogleAuthService for the exchange
            result = await google_auth_service.exchange_google_code(code, code_verifier, redirect_uri)

            user_info = result["user_info"]
            google_id = user_info["google_id"]

            # Check for existing user by Google ID or create new
            user_data = self._find_or_create_google_user(user_info, google_id)
            user = self.user_service.create_or_get_user(user_data)

            jwt_token = self.create_access_token(user.id, user_data, role=user.role)
            refresh_token = self.create_refresh_token(user.id, ip, user_agent)

            return LoginResponse(
                access_token=jwt_token,
                token_type="bearer",  # nosec B106
                user=UserResponse(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    picture=user.picture,
                    bio=user.bio,
                    created_at=user.created_at,
                    google_id=user.google_id,
                ),
                refresh_token=refresh_token,
            )

        except Exception:
            logger.error("[OAuth] Exchange exception")
            raise ValueError("Code exchange failed")

    def create_refresh_token(self, user_id: str, ip: str | None = None, user_agent: str | None = None) -> str:
        """Create long-lived refresh token"""
        expire = utc_now() + timedelta(days=config.JWT_REFRESH_EXPIRATION_DAYS)
        jti = str(uuid.uuid4())

        to_encode = {
            "user_id": user_id,
            "sub": user_id,
            "jti": jti,
            "exp": expire,
            "iat": utc_now(),
            "type": "refresh",
        }

        if ip or user_agent:
            to_encode["fingerprint"] = self._generate_fingerprint(ip or "", user_agent or "")

        return jwt.encode(to_encode, cast("str", config.JWT_REFRESH_SECRET), algorithm=self.jwt_algorithm)

    async def verify_refresh_token(
        self, token: str, ip: str | None = None, user_agent: str | None = None
    ) -> dict[str, Any] | None:
        """Verify refresh token"""
        try:
            payload = jwt.decode(token, cast("str", config.JWT_REFRESH_SECRET), algorithms=[self.jwt_algorithm])

            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")
            user_id = payload.get("user_id")
            iat = payload.get("iat")

            if jti and await self.is_token_revoked(jti):
                logger.warning("Attempt to use revoked refresh token")
                return None

            # Check for global user invalidation
            if user_id and iat and await self._check_user_invalidated(user_id, iat):
                logger.warning("Refresh token rejected due to user invalidation")
                return None

            token_fingerprint = payload.get("fingerprint")
            if token_fingerprint and (ip or user_agent):
                current_fingerprint = self._generate_fingerprint(ip or "", user_agent or "")
                if token_fingerprint != current_fingerprint:
                    logger.warning("Token fingerprint mismatch!")
                    return None

            return payload
        except jwt.PyJWTError:
            return None
        except Exception as e:
            logger.error("Session verification unsuccessful: %s", e)
            return None

    def create_password_reset_token(self, email: str) -> bool:
        """Request password reset via Supabase Auth"""
        try:
            params = {
                "type": "recovery",
                "email": email,
                "options": {"redirect_to": f"{config.FRONTEND_URL}/reset-password"},
            }

            res = self.supabase_admin.auth.admin.generate_link(cast(Any, params))

            if not res or not hasattr(res, "properties"):
                logger.error("Failed to generate recovery link for %s", email)
                return False

            action_link = getattr(res.properties, "action_link", None)

            if not action_link:
                logger.error("No action_link returned for %s", email)
                return False

            # Send Email via EmailService
            return email_service.send_reset_email(email, action_link)

        except Exception as e:
            # SECURITY: Return True to prevent email enumeration
            logger.error("Failed to process password reset: %s", e)
        
        return True

    async def reset_password(self, access_token: str, new_password: str) -> bool:
        """Reset password using Supabase Auth session"""
        try:
            await self._validate_and_update_password(access_token, new_password)
            return True
        except Exception as e:
            logger.error(f"Reset password failed: {e}")
            log_security_event(
                "password_reset_failed", details={"error": "An internal error occurred"}, severity="ERROR"
            )
            return False

    async def _validate_and_update_password(self, access_token: str, new_password: str) -> None:
        is_valid, error = await password_service.validate_new_password(new_password)
        if not is_valid:
            logger.warning("Password validation failed during reset")
            raise ValueError(error)

        temp_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        temp_client.postgrest.auth(access_token)

        user_res = temp_client.auth.get_user(access_token)
        if not user_res or not user_res.user:
            raise ValueError("Invalid user session")

        user_id = user_res.user.id
        temp_client.auth.update_user({"password": new_password})

        self.supabase_admin.table("users").update(
            {"updated_at": utc_now().isoformat()}
        ).eq("id", user_id).execute()

        if user_res.user.email:
            await self._post_password_reset_cleanup(user_id, user_res.user.email)
        else:
            logger.warning(f"User {user_id} has no email, skipping cleanup notification")
        log_security_event("password_reset_success", user_id=user_id, severity="INFO")

    async def _post_password_reset_cleanup(self, user_id: str, email: str) -> None:
        try:
            ts = await get_token_service()
            await ts.blacklist_all_user_tokens(user_id, reason="password_reset")
        except Exception as e:
            logger.warning("Token cleanup unsuccessful: %s", e)

        try:
            email_service.send_password_changed_email(email)
        except Exception as e:
            logger.warning("Notification cleanup unsuccessful: %s", e)

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change password - Delegate checks to validators, then update via admin"""
        try:
            user = self.user_service.get_user_by_id(user_id)
            if not user:
                return False

            await self._verify_password_change_eligibility(user, current_password, new_password)

            # Update password
            self.supabase_admin.auth.admin.update_user_by_id(user_id, {"password": new_password})

            await self._post_password_change_cleanup(user_id, user.email)
            log_security_event("password_change_success", user_id=user_id, severity="INFO")
            return True
        except ValueError as e:
            log_security_event(
                "password_change_failed_validation", user_id=user_id, details={"error": str(e)}, severity="WARNING"
            )
            raise e
        except Exception as e:
            logger.error(f"Change password failed: {e}")
            log_security_event(
                "password_change_error",
                user_id=user_id,
                details={"error": "An internal error occurred"},
                severity="ERROR",
            )
            from exceptions import PurrfectSpotsException

            raise PurrfectSpotsException("Failed to change password", error_code="INTERNAL_ERROR")

    async def _verify_password_change_eligibility(self, user: User, current_pward: str, new_pward: str) -> None:
        if user.google_id:
            raise ValueError("This account uses Google Login. Please manage your password through Google Settings.")

        is_valid, error = await password_service.validate_new_password(new_pward)
        if not is_valid:
            raise ValueError(error)

        password_verified = self._verify_current_password(user, current_pward)
        if not password_verified:
            raise ValueError("Incorrect current password")

    def _verify_current_password(self, user: User, current_pward: str) -> bool:
        """
        Verify current password using Supabase Auth.
        We no longer store or check password hashes locally for security.
        """
        return bool(self.user_service.authenticate_user(user.email, current_pward))

    async def _post_password_change_cleanup(self, user_id: str, email: str) -> None:
        try:
            ts = await get_token_service()
            await ts.blacklist_all_user_tokens(user_id, reason="password_change")
        except Exception:
            logger.warning("Failed to blacklist tokens")

        try:
            email_service.send_password_changed_email(email)
        except Exception as e:
            logger.warning("Notification cleanup unsuccessful: %s", e)
