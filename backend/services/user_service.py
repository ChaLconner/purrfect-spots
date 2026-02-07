"""
User management service for CRUD operations on user profiles

Handles:
- User creation (with password)
- User retrieval (by ID, email)
- User profile updates
- Email confirmation flow
"""


from supabase import Client

from dependencies import get_supabase_admin_client
from exceptions import ConflictError, ExternalServiceError, PurrfectSpotsException
from logger import logger
from services.email_service import email_service
from services.password_service import password_service
from user_models.user import User
from utils.datetime_utils import utc_now_iso

ERROR_FAILED_TO_CREATE_USER = "Failed to create user"
ERROR_EMAIL_ALREADY_REGISTERED = "Email already registered"


class UserService:
    """Service for user-related operations"""

    SERVICE_SUPABASE_AUTH = "Supabase Auth"

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.supabase_admin = get_supabase_admin_client()

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID from database"""
        try:
            result = self.supabase_admin.table("users").select("*").eq("id", user_id).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by ID: %s", e)
            return None

    def get_user_by_email(self, email: str) -> dict | None:
        """Get user by email from database"""
        try:
            result = self.supabase_admin.table("users").select("*").eq("email", email).single().execute()
            return result.data if result.data else None
        except Exception as e:
            logger.debug("Failed to retrieve profile by email: %s", e)
            return None

    def get_user_by_username(self, username: str) -> User | None:
        """Get user by username from database"""
        try:
            result = self.supabase_admin.table("users").select("*").eq("username", username).single().execute()
            if result.data:
                return User(**result.data)
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by username: %s", e)
            return None

    def create_user_with_password(self, email: str, password: str, name: str) -> dict:
        """Create new user and send confirmation email (Manual Flow via Admin)"""
        try:
            # 1. Generate Signup Link (Creates user if not exists)
            # We use generate_link to get the URL without sending via Supabase SMTP which is failing
            # We use generate_link to get the URL without sending via Supabase SMTP which is failing

            params = {
                "type": "signup",
                "email": email,
                "password": password,
                "options": {
                    "data": {"name": name, "full_name": name},
                },
            }

            # This returns a UserResponse object from gotrue-py
            # Structure: res.user (User), res.properties.action_link (str)
            res = self.supabase_admin.auth.admin.generate_link(params)

            if not res or not res.user:
                raise ExternalServiceError(ERROR_FAILED_TO_CREATE_USER, service=self.SERVICE_SUPABASE_AUTH)

            user = res.user
            # Extract action_link safely
            action_link = getattr(res.properties, "action_link", None) if hasattr(res, "properties") else None

            if not action_link:
                # Fallback or error?
                # If no link, we can't verify.
                logger.error("No action_link returned from generate_link")
                raise ExternalServiceError("Failed to generate confirmation link", service=self.SERVICE_SUPABASE_AUTH)

            # 2. Send Email via our custom EmailService
            sent = email_service.send_confirmation_email(email, action_link)

            if not sent:
                logger.error("Failed to send custom confirmation email")
                # Proceeding anyway, but user might be stuck.

            return {
                "id": user.id,
                "email": user.email,
                "name": name,
                "created_at": user.created_at,
                "picture": "",
                "bio": None,
                "verification_required": True,
            }

        except Exception as e:
            # Clean up error message
            msg = str(e)

            if "already registered" in msg.lower():
                raise ConflictError(ERROR_EMAIL_ALREADY_REGISTERED)
            raise PurrfectSpotsException(f"Failed to create user: {msg}")

    def create_user(self, email: str, password: str, name: str) -> dict:
        """Alias for create_user_with_password"""
        return self.create_user_with_password(email, password, name)

    def create_unverified_user(self, email: str, password: str, name: str) -> dict:
        """
        Create a new user without sending a confirmation email automatically.
        Used for the OTP flow where verification is handled separately.
        """
        try:
            # Create user via Supabase Admin API with email_confirm=False
            res = self.supabase_admin.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": False,
                    "user_metadata": {"name": name, "full_name": name},
                }
            )

            if not res or not res.user:
                raise ExternalServiceError("Failed to create user", service=self.SERVICE_SUPABASE_AUTH)

            user = res.user

            return {
                "id": user.id,
                "email": user.email,
                "name": name,
                "created_at": user.created_at,
                "picture": "",
                "bio": None,
                "verification_required": True,
            }

        except Exception as e:
            # Clean up error message
            msg = str(e)

            if "already registered" in msg.lower() or "already been registered" in msg.lower():
                raise ConflictError(ERROR_EMAIL_ALREADY_REGISTERED)
            if "unique constraint" in msg.lower():
                raise ConflictError(ERROR_EMAIL_ALREADY_REGISTERED)
            logger.error("Failed to create unverified account: %s", msg)
            raise PurrfectSpotsException(ERROR_FAILED_TO_CREATE_USER)

    def create_or_get_user(self, user_data: dict) -> User:
        """Create new user or get existing user from database (for OAuth)"""
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
            raise ExternalServiceError(f"Database error: {e!s}", service="Supabase Database")

    def authenticate_user(self, email: str, password: str) -> dict | None:
        """Authenticate user using Supabase Auth"""
        try:
            res = self.supabase.auth.sign_in_with_password({"email": email, "password": password})

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
                }
            return None
        except Exception as e:
            logger.warning("Authentication failure: %s", e)
            return None

    def update_user_profile(self, user_id: str, update_data: dict) -> dict:
        """Update user profile"""
        try:
            result = self.supabase_admin.table("users").update(update_data).eq("id", user_id).execute()
            if not result.data:
                raise ValueError("User not found")
            return result.data[0]
        except Exception as e:
            raise PurrfectSpotsException(f"Failed to update profile: {e!s}")

    def update_password_hash(self, user_id: str, new_password: str) -> bool:
        """Update user's password hash in database"""
        try:
            self.supabase_admin.table("users").update(
                {"password_hash": password_service.hash_password(new_password), "updated_at": utc_now_iso()}
            ).eq("id", user_id).execute()
            return True
        except RuntimeError:
            logger.error("Failed to update security data for user: %s", user_id)
            return False
