"""
OAuth service for Google OAuth authentication

Handles:
- Google OAuth token verification
- Google authorization code exchange (PKCE flow)
- OAuth provider management
"""

import hashlib
import uuid
from datetime import timedelta

import httpx
import jwt
from google.auth.transport import requests
from google.oauth2 import id_token
from supabase import Client

from config import config
from dependencies import get_supabase_admin_client
from logger import logger
from user_models.user import LoginResponse, User, UserResponse
from utils.datetime_utils import utc_now, utc_now_iso


class OAuthService:
    """Service for OAuth-related operations"""

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

    async def exchange_google_code(
        self, 
        code: str, 
        code_verifier: str, 
        redirect_uri: str, 
        ip: str | None = None, 
        user_agent: str | None = None
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

                user = self._create_or_get_user(user_data)

                jwt_token = self._create_access_token(user.id, user_data)
                refresh_token = self._create_refresh_token(user.id, ip, user_agent)

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
            raise ValueError(f"Code exchange failed: {e!s}")

    def _create_or_get_user(self, user_data: dict) -> User:
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

    def _create_access_token(self, user_id: str, user_data: dict | None = None) -> str:
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

    def _create_refresh_token(self, user_id: str, ip: str | None = None, user_agent: str | None = None) -> str:
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
