"""
Authentication service for Google OAuth and traditional email/password auth
"""

import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from google.auth.transport import requests
from google.oauth2 import id_token
from supabase import Client

from config import config
from dependencies import get_supabase_admin_client
from logger import logger
from services.email_service import email_service
from services.password_service import password_service
from services.token_service import get_token_service
from user_models.user import LoginResponse, User, UserResponse
from utils.datetime_utils import utc_now, utc_now_iso


class AuthService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.supabase_admin = get_supabase_admin_client()
        self.google_client_id = config.GOOGLE_CLIENT_ID
        self.google_client_secret = config.GOOGLE_CLIENT_SECRET
        self.jwt_secret = config.JWT_SECRET
        self.jwt_algorithm = config.JWT_ALGORITHM
        self.jwt_expiration_hours = config.JWT_ACCESS_EXPIRATION_HOURS

        if not self.google_client_id:
            logger.warning("[OAuth] GOOGLE_CLIENT_ID is not set!")
        if not self.google_client_secret:
            logger.warning("[OAuth] GOOGLE_CLIENT_SECRET is not set!")



    def _generate_fingerprint(self, ip: str, user_agent: str) -> str:
        """Generate SHA256 fingerprint from IP (subnet) and User-Agent"""
        if not user_agent:
            user_agent = "unknown"

        # Enhance security: Include IP subnet (e.g., first 2 octets for IPv4)
        # to allow minor roaming but prevent cross-country attacks.
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
            logger.error(f"Failed to check token revocation: {e!s}")
            return False

    async def revoke_token(self, jti: str, user_id: str, expires_at: datetime) -> bool:
        """Add token to blacklist"""
        try:
            token_service = await get_token_service()
            return await token_service.blacklist_token(
                token=None, jti=jti, user_id=user_id, expires_at=expires_at, reason="logout"
            )
        except Exception as e:
            logger.error(f"Failed to revoke token: {e!s}")
            return False



    def verify_google_token(self, token: str) -> dict:
        """Verify Google OAuth token and return user info"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.google_client_id,
                clock_skew_in_seconds=10,
            )

            if idinfo["iss"] not in [
                "accounts.google.com",
                "https://accounts.google.com",
            ]:
                raise ValueError("Wrong issuer.")

            return {
                "google_id": idinfo["sub"],
                "email": idinfo["email"],
                "name": idinfo["name"],
                "picture": idinfo.get("picture", ""),
            }
        except ValueError as e:
            raise ValueError(f"Invalid token: {e!s}")

    def create_or_get_user(self, user_data: dict) -> User:
        """Create new user or get existing user from database"""
        try:
            user_id = user_data.get("id") or user_data.get("sub")

            if not user_id:
                raise ValueError("Missing user_id (sub) in user_data")

            email = user_data.get("email", "")
            name = user_data.get("name", "")
            picture = user_data.get("picture", "")
            google_id = user_data.get("google_id")

            user_record = {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "google_id": google_id,
                "bio": None,
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
                "password_hash": None,
            }

            # Use admin client for user creation (bypass RLS)
            result = self.supabase_admin.table("users").upsert(user_record, on_conflict="id").execute()

            user_dict = result.data[0]
            if "password_hash" not in user_dict:
                user_dict["password_hash"] = None

            return User(**user_dict)

        except Exception as e:
            logger.error(f"Database error in create_or_get_user: {e}")
            raise Exception("Database error occurred")

    def create_access_token(self, user_id: str, user_data: dict | None = None) -> str:
        """Create JWT access token with user data"""
        expire = utc_now() + timedelta(hours=self.jwt_expiration_hours)
        jti = str(uuid.uuid4())

        to_encode = {
            "user_id": user_id,
            "sub": user_id,
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

        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt

    async def _check_user_invalidated(self, user_id: str, iat: int) -> bool:
        """Check if user has been globally invalidated since token issuance"""
        try:
            token_service = await get_token_service()
            token_issued_at = datetime.fromtimestamp(iat, timezone.utc)
            return await token_service.is_user_invalidated(user_id, token_issued_at)
        except Exception as e:
            logger.warning(f"User invalidation check failed: {e}")
            return False

    def verify_access_token(self, token: str) -> str | None:
        """Verify JWT access token and return user_id"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload.get("user_id")
        except jwt.PyJWTError:
            return None

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID from database"""
        try:
            result = self.supabase_admin.table("users").select("*").eq("id", user_id).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.debug(f"Failed to get user by ID {user_id}: {e}")
            return None

    def get_user_by_email(self, email: str) -> dict | None:
        """Get user by email from database"""
        try:
            result = self.supabase_admin.table("users").select("*").eq("email", email).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.debug(f"Failed to get user by email {email}: {e}")
            return None

    def create_user_with_password(self, email: str, password: str, name: str) -> dict:
        """Create new user without auto-confirmation (OTP verification will be done separately)"""
        try:
            # Create user via Supabase Admin API with email_confirm=False
            # This creates the user but does not verify their email
            res = self.supabase_admin.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": False,  # Don't auto-confirm - we'll use OTP
                "user_metadata": {
                    "name": name,
                    "full_name": name
                }
            })
            
            if not res or not res.user:
                raise Exception("Failed to create user")

            user = res.user
            
            return {
                "id": user.id,
                "email": user.email,
                "name": name,
                "created_at": user.created_at,
                "picture": "",
                "bio": None,
                "verification_required": True
            }

        except Exception as e:
            # Clean up error message
            msg = str(e)
            if "already registered" in msg.lower() or "already been registered" in msg.lower():
                raise Exception("Email already registered")
            if "unique constraint" in msg.lower():
                raise Exception("Email already registered")
            logger.error(f"Failed to create user: {msg}")
            raise Exception("Failed to create user")

    def create_user(self, email: str, password: str, name: str) -> dict:
        return self.create_user_with_password(email, password, name)

    def confirm_user_email(self, email: str) -> bool:
        """
        Confirm user's email address after OTP verification.
        Uses Supabase Admin API to set email_confirmed_at.
        """
        try:
            # First, get the user by email
            users = self.supabase_admin.auth.admin.list_users()
            target_user = None
            for user in users:
                if user.email and user.email.lower() == email.lower():
                    target_user = user
                    break
            
            if not target_user:
                logger.error(f"User not found for email confirmation: {email}")
                return False
            
            # Update user to confirm email
            self.supabase_admin.auth.admin.update_user_by_id(
                target_user.id,
                {"email_confirm": True}
            )
            
            logger.info(f"Email confirmed for user: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to confirm email for {email}: {e}")
            return False

    def get_user_by_email_unverified(self, email: str) -> dict | None:
        """Get user by email, including unverified users"""
        try:
            users = self.supabase_admin.auth.admin.list_users()
            for user in users:
                if user.email and user.email.lower() == email.lower():
                    return {
                        "id": user.id,
                        "email": user.email,
                        "name": user.user_metadata.get("name", "") if user.user_metadata else "",
                        "picture": user.user_metadata.get("avatar_url", "") if user.user_metadata else "",
                        "created_at": user.created_at,
                        "email_confirmed_at": user.email_confirmed_at
                    }
            return None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None

    def authenticate_user(self, email: str, password: str) -> dict | None:
        """Authenticate user using Supabase Auth"""
        try:
            res = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if res.user and res.session:
                # Return dict with user and tokens
                return {
                    "id": res.user.id,
                    "email": res.user.email,
                    "name": res.user.user_metadata.get("name", ""),
                    "picture": res.user.user_metadata.get("avatar_url", ""),
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                    "created_at": res.user.created_at,
                    # We might need to fetch profile for bio if strictly required
                }
            return None
        except Exception as e:
            logger.warning(f"Login failed: {e}")
            return None

    def update_user_profile(self, user_id: str, update_data: dict) -> dict:
        """Update user profile"""
        try:
            result = self.supabase_admin.table("users").update(update_data).eq("id", user_id).execute()
            if not result.data:
                raise ValueError("User not found")
            return result.data[0]
        except Exception as e:
            logger.error(f"Failed to update profile: {e}")
            raise Exception("Failed to update profile")

    async def exchange_google_code(
        self, code: str, code_verifier: str, redirect_uri: str, ip: str | None = None, user_agent: str | None = None
    ) -> LoginResponse:
        """Exchange Google authorization code for access token using PKCE flow"""
        try:
            if not code or not code_verifier or not redirect_uri:
                raise ValueError("Missing required OAuth parameters")

            token_url = "https://oauth2.googleapis.com/token"  # nosec B105
            data = {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, headers=headers)

                if response.status_code != 200:
                    logger.warning(f"[OAuth] Google exchange error: {response.text}")
                    raise ValueError("Token exchange failed")

                token_data = response.json()
                access_token = token_data.get("access_token")
                id_token_str = token_data.get("id_token")

                if not access_token or not id_token_str:
                    logger.error("[OAuth] Missing tokens in Google response")
                    raise ValueError("Missing tokens in response")

                # Verify ID token
                idinfo = id_token.verify_oauth2_token(
                    id_token_str,
                    requests.Request(),
                    self.google_client_id,
                    clock_skew_in_seconds=10,
                )

                google_sub = idinfo["sub"]

                # Check for existing user by Google ID
                existing_user = None
                try:
                    result = self.supabase_admin.table("users").select("*").eq("google_id", google_sub).execute()
                    if result.data:
                        existing_user = result.data[0]
                except Exception as e:
                    # User might not exist yet, which is expected for new sign-ups
                    logger.debug(f"Failed to check for existing Google user (may be new): {e}")

                user_uuid = existing_user["id"] if existing_user else str(uuid.uuid4())

                user_data = {
                    "id": user_uuid,
                    "sub": user_uuid,
                    "google_id": google_sub,
                    "email": idinfo["email"],
                    "name": idinfo["name"],
                    "picture": idinfo.get("picture", ""),
                }

                user = self.create_or_get_user(user_data)

                jwt_token = self.create_access_token(user.id, user_data)
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
                    ),
                    refresh_token=refresh_token,
                )

        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"[OAuth] Exchange exception: {e}")
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

        encoded_jwt = jwt.encode(to_encode, config.JWT_REFRESH_SECRET, algorithm=self.jwt_algorithm)  # type: ignore[arg-type]
        return encoded_jwt

    async def verify_refresh_token(
        self, token: str, ip: str | None = None, user_agent: str | None = None
    ) -> dict | None:
        """Verify refresh token"""
        try:
            payload = jwt.decode(token, config.JWT_REFRESH_SECRET, algorithms=[self.jwt_algorithm])  # type: ignore[arg-type]

            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")
            user_id = payload.get("user_id")
            iat = payload.get("iat")

            if jti and await self.is_token_revoked(jti):
                logger.warning(f"Attempt to use revoked refresh token: {jti}")
                return None
            
            # Check for global user invalidation (e.g. password reset)
            if user_id and iat and await self._check_user_invalidated(user_id, iat):
                logger.warning(f"Refresh token rejected due to user invalidation: {user_id}")
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
            logger.error(f"Verify refresh token error: {e}")
            return None

    async def create_password_reset_token(self, email: str) -> bool:
        """
        Request password reset via Supabase Auth.
        Generates recovery link and sends via custom EmailService.
        """
        try:
            # 1. Generate Link via Supabase Admin (bypasses standard email)
            # This allows us to use our own EmailService
            params = {
                "type": "recovery",
                "email": email,
                "options": {
                    "redirect_to": f"{config.FRONTEND_URL}/reset-password"
                }
            }
            
            res = self.supabase_admin.auth.admin.generate_link(params)
            
            if not res or not hasattr(res, "properties"):
                 logger.error(f"Failed to generate recovery link for {email}")
                 return False

            action_link = getattr(res.properties, "action_link", None)
            
            if not action_link:
                logger.error(f"No action_link returned for {email}")
                return False

            # 2. Send Email via our custom EmailService
            sent = email_service.send_reset_email(email, action_link)
            return sent

        except Exception as e:
            logger.error(f"Failed to process password reset for {email}: {e}")
            # We return True to prevent email enumeration, but log the actual error
            return True



    async def reset_password(self, access_token: str, new_password: str) -> bool:
        """
        Reset password using Supabase Auth session.
        The access_token comes from the recovery email link.
        """
        try:
            # 0.1 Security Check: Complexity & Leaks (Using PasswordService)
            # Use validate_new_password which checks both complexity and breaches
            is_valid, error = await password_service.validate_new_password(new_password)
            if not is_valid:
                 logger.warning(f"Password validation failed during reset: {error}")
                 raise ValueError(error) # e.g. "Password must be at least 8 characters" or "Data breach found"

            # 1. Initialize a temporary client using the recovery access_token
            # This validates the token and sets the user context
            from supabase import create_client
            temp_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            temp_client.postgrest.auth(access_token)
            
            # 2. Get user info to verify token validity
            user_res = temp_client.auth.get_user(access_token)
            if not user_res or not user_res.user:
                 logger.warning("Invalid or expired reset token used")
                 return False
            
            user_id = user_res.user.id
            
            # 3. Update Auth Password using the user's own context
            # This is safer than Admin API as it validates the session ownership
            temp_client.auth.update_user({"password": new_password})
            
            # 4. Sync new password hash to our database (for local verification if needed)
            # though usually we rely on Supabase Auth for login.
            # Changing password_hash here is for consistency.
            self.supabase_admin.table("users").update({
                "password_hash": password_service.hash_password(new_password),
                "updated_at": utc_now_iso()
            }).eq("id", user_id).execute()
            
            # 5. Global Invalidation (Invalidate all sessions for this user)
            try:
                # Add current time to invalidation list to reject all older tokens
                # from services.token_service import get_token_service (Already imported)
                ts = await get_token_service()
                await ts.blacklist_all_user_tokens(user_id, reason="password_reset")
            except Exception as e:
                logger.warning(f"Global session invalidation failed for {user_id}: {e}")

            # 6. Send Notification Email
            try:
                email_service.send_password_changed_email(user_res.user.email)
            except Exception as e:
                logger.warning(f"Failed to send password reset notification email: {e}")

            from utils.security import log_security_event
            log_security_event("password_reset_success", user_id=user_id, severity="INFO")

            return True
        except Exception as e:
            logger.error(f"Reset password failed: {e}")
            from utils.security import log_security_event
            log_security_event("password_reset_failed", details={"error": str(e)}, severity="ERROR")
            return False

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change password for an authenticated user.
        Updates both database profile and Supabase Auth.
        """
        try:
            # 1. Verify user exists in database
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # 2. Check if user is a Google User
            # Google users have google_id set and usually no password_hash
            if user.google_id:
                raise ValueError("This account uses Google Login. Please manage your password through Google Settings.")

            # 2.5 & 2.6 Security Check: Complexity & Leaks (Using PasswordService)
            is_valid, error = await password_service.validate_new_password(new_password)
            if not is_valid:
                raise ValueError(error)

            # 3. Verify current password
            password_verified = False
            
            if user.password_hash:
                # If we have a hash in our DB, verify it manually first (fast)
                try:
                    password_verified = password_service.verify_password(current_password, user.password_hash)
                except Exception as e:
                    logger.debug(f"Password verification exception: {e}")
                    password_verified = False
            
            if not password_verified:
                # Fallback or alternate: Verify via Supabase Auth Login attempt
                # This is the most reliable way as it's the source of truth
                try:
                    # We use self.supabase (Client) which should be configured with the correct URL/Key
                    auth_res = self.supabase.auth.sign_in_with_password({
                        "email": user.email,
                        "password": current_password
                    })
                    if auth_res and auth_res.user:
                        password_verified = True
                except Exception as e:
                    logger.debug(f"Supabase verification failed: {e}")
                    password_verified = False

            if not password_verified:
                raise ValueError("Incorrect current password")

            # 4. Update Supabase Auth Password (via Admin API as we are backend)
            # This ensures sync between Auth and DB
            self.supabase_admin.auth.admin.update_user_by_id(user_id, {"password": new_password})

            # 5. Update local database profile with new hash
            # This ensures next time manual verification works
            self.supabase_admin.table("users").update({
                "password_hash": password_service.hash_password(new_password), 
                "updated_at": utc_now_iso()
            }).eq("id", user_id).execute()

            # 5. Global Session Invalidation
            try:
                # from services.token_service import get_token_service (Already imported)
                ts = await get_token_service()
                await ts.blacklist_all_user_tokens(user_id, reason="password_change")
            except Exception as e:
                logger.warning(f"Failed to blacklist tokens on password change: {e}")

            # 6. Send Notification Email
            try:
                email_service.send_password_changed_email(user.email)
            except Exception as e:
                logger.warning(f"Failed to send password change notification email: {e}")

            from utils.security import log_security_event
            log_security_event("password_change_success", user_id=user_id, severity="INFO")

            return True
        except ValueError as e:
            from utils.security import log_security_event
            log_security_event("password_change_failed_validation", user_id=user_id, details={"error": str(e)}, severity="WARNING")
            raise e
        except Exception as e:
            logger.error(f"Change password failed for {user_id}: {e}")
            from utils.security import log_security_event
            log_security_event("password_change_error", user_id=user_id, details={"error": str(e)}, severity="ERROR")
            raise Exception("Failed to change password")
