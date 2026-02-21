import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional, cast

import jwt
from supabase import AClient, acreate_client

from config import config
from logger import logger
from schemas.auth import LoginResponse
from services.email_service import email_service
from services.google_auth_service import google_auth_service
from services.password_service import password_service
from services.token_service import get_token_service
from services.user_service import UserService
from user_models.user import User, UserResponse
from utils.datetime_utils import utc_now
from utils.supabase_client import get_async_supabase_admin_client

try:
    from redis.exceptions import RedisError
except ImportError:

    class RedisError(Exception):  # type: ignore[no-redef]
        pass


class AuthService:
    """Authentication service using Async Supabase Client"""

    def __init__(self, supabase_client: AClient, supabase_admin: Optional[AClient] = None) -> None:
        self.supabase = supabase_client
        self.supabase_admin = supabase_admin
        self.user_service = UserService(supabase_client, supabase_admin)
        self.jwt_secret = config.JWT_SECRET
        self.jwt_algorithm = config.JWT_ALGORITHM
        self.jwt_expiration_hours = config.JWT_ACCESS_EXPIRATION_HOURS

        if not self.jwt_secret:
            raise ValueError("JWT_SECRET is not configured")

    async def _get_admin_client(self) -> AClient:
        if self.supabase_admin:
            return self.supabase_admin
        return await get_async_supabase_admin_client()

    async def _find_or_create_google_user(self, user_info: dict[str, Any], google_id: str) -> dict[str, Any]:
        """Find existing user by Google ID or email to handle account linking (Async)"""
        existing_user = None
        email = user_info.get("email")
        try:
            admin = await self._get_admin_client()
            # 1. Check by google_id
            res = await admin.table("users").select("id").eq("google_id", google_id).execute()
            if res.data:
                existing_user = res.data[0]
            elif email:
                # 2. Check by email (account linking scenario)
                res_email = await admin.table("users").select("id").eq("email", email).execute()
                if res_email.data:
                    existing_user = res_email.data[0]
                    # Link account by updating google_id
                    await admin.table("users").update({"google_id": google_id}).eq("id", existing_user["id"]).execute()
        except Exception as e:
            logger.debug("Identity check unsuccessful: %s", e)

        user_id = existing_user["id"] if existing_user else str(uuid.uuid4())
        return {
            "id": user_id,
            "sub": user_id,
            "google_id": google_id,
            "email": email,
            "name": user_info.get("name", ""),
            "picture": user_info.get("picture", ""),
        }

    def _generate_fingerprint(self, ip: str, user_agent: str) -> str:
        """Generate SHA256 fingerprint from IP (subnet) and User-Agent"""
        if not user_agent:
            user_agent = "unknown"
        ip_segment = "unknown"
        if ip:
            if "." in ip:
                parts = ip.split(".")
                if len(parts) >= 2:
                    ip_segment = f"{parts[0]}.{parts[1]}"
            elif ":" in ip:
                parts = ip.split(":")
                if len(parts) >= 3:
                    ip_segment = f"{parts[0]}:{parts[1]}:{parts[2]}"
        raw = f"{user_agent}|{ip_segment}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token JTI is in blacklist (Async)"""
        if not jti:
            return False
        try:
            token_service = await get_token_service()
            return await token_service.is_blacklisted(jti=jti)
        except Exception as e:
            logger.error("Failed to check revocation status: %s", e)
            return True

    async def revoke_token(self, jti: str, user_id: str, expires_at: datetime) -> bool:
        """Add token to blacklist (Async)"""
        try:
            token_service = await get_token_service()
            return await token_service.blacklist_token(
                token=None, jti=jti, user_id=user_id, expires_at=expires_at, reason="logout"
            )
        except Exception as e:
            logger.error("Failed to revoke session: %s", e)
            return False

    def verify_google_token(self, token: str) -> dict[str, Any]:
        """Verify Google OAuth token"""
        return google_auth_service.verify_google_token(token)

    async def create_or_get_user(self, user_data: dict[str, Any]) -> User:
        """Delegated to UserService (Async)"""
        return await self.user_service.create_or_get_user(user_data)

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any] | None:
        """Authenticate user (Async) - Delegated to UserService"""
        return await self.user_service.authenticate_user(email, password)

    async def create_user_with_password(self, email: str, password: str, name: str) -> dict[str, Any]:
        """Create new user with password (Async) - Delegated to UserService"""
        return await self.user_service.create_unverified_user(email, password, name)

    async def get_user_by_email_unverified(self, email: str) -> dict[str, Any] | None:
        """Get user by email including unverified ones (Async) - Delegated to UserService"""
        return await self.user_service.get_user_by_email(email)

    async def confirm_user_email(self, email: str) -> bool:
        """Confirm user email via Admin Client (Async)"""
        try:
            admin = await self._get_admin_client()
            # 1. Find user ID from email since admin.update_user_by_id is preferred
            res = await admin.table("users").select("id").eq("email", email).execute()
            if not res.data:
                # If not in users table, try auth metadata search
                return False

            user_id = res.data[0]["id"]

            # 2. Update auth user to confirm email
            # In Supabase Admin Auth, we can set email_confirm: True
            await admin.auth.admin.update_user_by_id(user_id, {"email_confirm": True})

            # 3. Update verified flag in users table if it exists (schema check)
            # In this app, it seems we mostly rely on auth metadata and role-based permissions,
            # but let's see if there's a confirmed_at or similar. The user model doesn't show it.
            return True
        except Exception as e:
            logger.error("Failed to confirm user email: %s", e)
            return False

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID (Async) - Delegated to UserService"""
        return await self.user_service.get_user_by_id(user_id)

    async def update_user_profile(
        self, user_id: str, update_data: dict[str, Any], jwt_token: str | None = None
    ) -> dict[str, Any]:
        """Update user profile (Async) - Delegated to UserService"""
        return await self.user_service.update_user_profile(user_id, update_data, jwt_token)

    def create_access_token(
        self,
        user_id: str,
        user_data: dict[str, Any] | None = None,
        role: str = "user",
        permissions: list[str] | None = None,
    ) -> str:
        """Create JWT access token"""
        expire = utc_now() + timedelta(hours=self.jwt_expiration_hours)
        jti = str(uuid.uuid4())
        to_encode = {
            "user_id": user_id,
            "sub": user_id,
            "role": role,
            "permissions": permissions or [],
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

    def verify_access_token(self, token: str) -> str | None:
        """Verify access token and return user_id"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload.get("sub") or payload.get("user_id")
        except Exception as e:
            logger.debug(f"Token verification failed: {e}")
            return None

    async def exchange_google_code(
        self, code: str, code_verifier: str, redirect_uri: str, ip: str | None = None, user_agent: str | None = None
    ) -> LoginResponse:
        """Exchange Google authorization code for access token (Async)"""
        try:
            result = await google_auth_service.exchange_google_code(code, code_verifier, redirect_uri)
            user_info = result["user_info"]
            google_id = user_info["google_id"]

            user_data = await self._find_or_create_google_user(user_info, google_id)
            user = await self.user_service.create_or_get_user(user_data)

            jwt_token = self.create_access_token(user.id, user_data, role=user.role, permissions=user.permissions)
            refresh_token = self.create_refresh_token(user.id, ip, user_agent)

            return LoginResponse(
                access_token=jwt_token,
                token_type="bearer",
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
        except Exception as e:
            logger.error("[OAuth] Exchange exception: %s", e)
            raise ValueError(f"Code exchange failed: {e}")

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
        return jwt.encode(to_encode, cast(str, config.JWT_REFRESH_SECRET), algorithm=self.jwt_algorithm)

    async def verify_refresh_token(
        self, token: str, ip: str | None = None, user_agent: str | None = None
    ) -> dict[str, Any] | None:
        """Verify refresh token (Async)"""
        try:
            payload = jwt.decode(token, cast(str, config.JWT_REFRESH_SECRET), algorithms=[self.jwt_algorithm])
            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")
            payload.get("user_id")
            payload.get("iat")

            if jti and await self.is_token_revoked(jti):
                return None

            token_fingerprint = payload.get("fingerprint")
            if token_fingerprint and (ip or user_agent):
                current_fingerprint = self._generate_fingerprint(ip or "", user_agent or "")
                if token_fingerprint != current_fingerprint:
                    return None
            return payload
        except Exception as e:
            logger.error("Session verification unsuccessful: %s", e)
            return None

    async def create_password_reset_token(self, email: str) -> bool:
        """Request password reset via Supabase Auth (Async)"""
        try:
            params = {
                "type": "recovery",
                "email": email,
                "options": {"redirect_to": f"{config.FRONTEND_URL}/reset-password"},
            }
            admin = await self._get_admin_client()
            res = await admin.auth.admin.generate_link(cast(Any, params))
            if not res or not hasattr(res, "properties"):
                return False
            action_link = getattr(res.properties, "action_link", None)
            if not action_link:
                return False
            return email_service.send_reset_email(email, action_link)
        except Exception as e:
            logger.error("Failed to process password reset: %s", e)
        return True

    async def reset_password(self, access_token: str, new_password: str) -> bool:
        """Reset password using Supabase Auth session (Async)"""
        try:
            is_valid, error = await password_service.validate_new_password(new_password)
            if not is_valid:
                raise ValueError(error)

            temp_client = await acreate_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            temp_client.postgrest.auth(access_token)
            user_res = await temp_client.auth.get_user(access_token)
            if not user_res or not user_res.user:
                raise ValueError("Invalid user session")

            user_id = user_res.user.id
            await temp_client.auth.update_user({"password": new_password})

            admin = await self._get_admin_client()
            await admin.table("users").update({"updated_at": utc_now().isoformat()}).eq("id", user_id).execute()

            if user_res.user.email:
                ts = await get_token_service()
                await ts.blacklist_all_user_tokens(user_id, reason="password_reset")
                email_service.send_password_changed_email(user_res.user.email)
            return True
        except Exception as e:
            logger.error(f"Reset password failed: {e}")
            return False

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change password (Async)"""
        try:
            user = await self.user_service.get_user_by_id(user_id)
            if not user or user.google_id:
                return False

            is_valid, error = await password_service.validate_new_password(new_password)
            if not is_valid:
                raise ValueError(error)

            # Manual verification check using authenticate_user
            auth_test = await self.user_service.authenticate_user(user.email, current_password)
            if not auth_test:
                raise ValueError("Incorrect current password")

            admin = await self._get_admin_client()
            await admin.auth.admin.update_user_by_id(user_id, {"password": new_password})

            ts = await get_token_service()
            await ts.blacklist_all_user_tokens(user_id, reason="password_change")
            email_service.send_password_changed_email(user.email)
            return True
        except Exception as e:
            logger.error(f"Change password failed: {e}")
            raise e
