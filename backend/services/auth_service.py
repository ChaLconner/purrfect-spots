"""
Authentication service for Google OAuth and traditional email/password auth
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import httpx
import jwt
from google.auth.transport import requests
from google.oauth2 import id_token
from supabase import Client

from config import config
from dependencies import get_supabase_admin_client
from logger import logger
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

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))

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
            raise Exception(f"Database error: {e!s}")

    def create_access_token(self, user_id: str, user_data: dict = None) -> str:
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
        except Exception:
            return None

    def get_user_by_email(self, email: str) -> dict | None:
        """Get user by email from database"""
        try:
            result = self.supabase_admin.table("users").select("*").eq("email", email).single().execute()
            return result.data if result.data else None
        except Exception:
            return None

    def create_user_with_password(self, email: str, password: str, name: str) -> dict:
        """Create new user with email and password"""
        try:
            password_hash = self.hash_password(password)
            user_data = {
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "bio": None,
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
            }
            result = self.supabase_admin.table("users").insert(user_data).execute()
            return result.data[0]
        except Exception as e:
            raise Exception(f"Failed to create user: {e!s}")

    def create_user(self, email: str, password: str, name: str) -> dict:
        return self.create_user_with_password(email, password, name)

    def authenticate_user(self, email: str, password: str) -> dict | None:
        """Authenticate user with email and password (timing-safe)"""
        try:
            user = self.get_user_by_email(email)

            # Use real hash if user exists, otherwise use a dummy hash to prevent timing attacks
            # (protects against user enumeration)
            if user and user.get("password_hash"):
                password_hash = user["password_hash"]
            else:
                # Valid bcrypt hash for "dummy_password" to ensure checkpw takes time
                password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQOqhN/Md.osUgsgW8.c2e.da"

            # Always perform the slow hashing operation
            is_valid = self.verify_password(password, password_hash)

            if user and is_valid:
                return user

            return None
        except Exception:
            return None

    def update_user_profile(self, user_id: str, update_data: dict) -> dict:
        """Update user profile"""
        try:
            result = self.supabase_admin.table("users").update(update_data).eq("id", user_id).execute()
            if not result.data:
                raise ValueError("User not found")
            return result.data[0]
        except Exception as e:
            raise Exception(f"Failed to update profile: {e!s}")

    async def exchange_google_code(
        self, code: str, code_verifier: str, redirect_uri: str, ip: str = None, user_agent: str = None
    ) -> LoginResponse:
        """Exchange Google authorization code for access token using PKCE flow"""
        try:
            if not code or not code_verifier or not redirect_uri:
                raise ValueError("Missing required OAuth parameters")

            token_url = "https://oauth2.googleapis.com/token"
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
                except Exception:
                    pass

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
                    token_type="bearer",
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
            raise ValueError(f"Code exchange failed: {e!s}")

    def create_refresh_token(self, user_id: str, ip: str = None, user_agent: str = None) -> str:
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
            to_encode["fingerprint"] = self._generate_fingerprint(ip, user_agent)

        encoded_jwt = jwt.encode(to_encode, config.JWT_REFRESH_SECRET, algorithm=self.jwt_algorithm)
        return encoded_jwt

    async def verify_refresh_token(self, token: str, ip: str = None, user_agent: str = None) -> dict | None:
        """Verify refresh token"""
        try:
            payload = jwt.decode(token, config.JWT_REFRESH_SECRET, algorithms=[self.jwt_algorithm])

            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")
            if jti and await self.is_token_revoked(jti):
                logger.warning(f"Attempt to use revoked refresh token: {jti}")
                return None

            token_fingerprint = payload.get("fingerprint")
            if token_fingerprint and (ip or user_agent):
                current_fingerprint = self._generate_fingerprint(ip, user_agent)
                if token_fingerprint != current_fingerprint:
                    logger.warning("Token fingerprint mismatch!")
                    return None

            return payload
        except jwt.PyJWTError:
            return None
        except Exception as e:
            logger.error(f"Verify refresh token error: {e}")
            return None

    def create_password_reset_token(self, email: str) -> str | None:
        # Same implementation...
        user = self.get_user_by_email(email)
        if not user:
            return None

        token = str(uuid.uuid4())
        expires_at = utc_now() + timedelta(hours=1)

        try:
            self.supabase_admin.table("password_resets").insert(
                {"user_id": user["id"], "token": token, "expires_at": expires_at.isoformat()}
            ).execute()
            return token
        except Exception:
            return None

    def reset_password(self, token: str, new_password: str) -> bool:
        # Same logic, minimized for brevity in this response but will write full file
        try:
            result = (
                self.supabase_admin.table("password_resets")
                .select("*")
                .eq("token", token)
                .eq("is_used", False)
                .gt("expires_at", utc_now_iso())
                .execute()
            )
            if not result.data:
                return False

            rec = result.data[0]
            self.supabase_admin.table("users").update(
                {"password_hash": self.hash_password(new_password), "updated_at": utc_now_iso()}
            ).eq("id", rec["user_id"]).execute()

            self.supabase_admin.table("password_resets").update({"is_used": True}).eq("id", rec["id"]).execute()
            return True
        except Exception:
            return False

    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        try:
            user = self.get_user_by_id(user_id)
            if not user or not user.password_hash:
                return False
            if not self.verify_password(current_password, user.password_hash):
                raise ValueError("Incorrect current password")

            self.supabase_admin.table("users").update(
                {"password_hash": self.hash_password(new_password), "updated_at": utc_now_iso()}
            ).eq("id", user_id).execute()
            return True
        except ValueError as e:
            raise e
        except Exception:
            raise Exception("Failed to change password")
