from datetime import UTC, datetime, timedelta
from typing import Any

from supabase import AClient

from exceptions import ConflictError, ExternalServiceError, PurrfectSpotsException
from logger import logger
from schemas.user import User
from utils.datetime_utils import utc_now_iso
from utils.supabase_client import get_async_supabase_admin_client

ERROR_FAILED_TO_CREATE_USER = "Failed to create user"
ERROR_EMAIL_ALREADY_REGISTERED = "Email already registered"


class UserService:
    """Service for user-related operations using Async Supabase Client"""

    SERVICE_SUPABASE_AUTH = "Supabase Auth"
    _cached_user_role_id: str | None = None

    def __init__(self, supabase_client: AClient, supabase_admin: AClient | None = None) -> None:
        self.supabase = supabase_client
        self.supabase_admin = supabase_admin

    async def _get_admin_client(self) -> AClient:
        if self.supabase_admin:
            return self.supabase_admin
        return await get_async_supabase_admin_client()

    async def _get_user_role_id(self) -> str | None:
        """Get the ID of the 'user' role from the roles table (Async)"""
        if UserService._cached_user_role_id:
            return UserService._cached_user_role_id

        try:
            admin = await self._get_admin_client()
            res = await admin.table("roles").select("id").eq("name", "user").execute()
            if res.data:
                UserService._cached_user_role_id = res.data[0]["id"]
                return UserService._cached_user_role_id
        except Exception as e:
            logger.warning("Failed to fetch default user role ID: %s", e)
        return None

    def _map_db_user_to_model(self, data: dict[str, Any]) -> User:
        """Map DB result with nested role/permissions to User model"""
        permissions: list[str] = []

        role_data = data.get("roles")
        if role_data and isinstance(role_data, dict):
            rps = role_data.get("role_permissions", [])
            for rp in rps:
                perm = rp.get("permissions")
                if perm and "code" in perm:
                    permissions.append(perm["code"])

        user_fields = data.copy()
        if isinstance(role_data, dict) and "name" in role_data:
            user_fields["role"] = role_data["name"]

        if "roles" in user_fields:
            del user_fields["roles"]

        return User(**user_fields, permissions=permissions)

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID from database with Role and Permissions (Async)"""
        try:
            query = "*, roles(name, role_permissions(permissions(code)))"
            admin = await self._get_admin_client()
            result = await admin.table("users").select(query).eq("id", user_id).execute()
            if result.data:
                return self._map_db_user_to_model(result.data[0])
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by ID: %s", e)
            return None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email from database (Async)"""
        try:
            admin = await self._get_admin_client()
            result = await admin.table("users").select("*").eq("email", email).maybe_single().execute()
            return result.data if result and result.data else None
        except Exception as e:
            logger.debug("Failed to retrieve profile by email: %s", e)
            return None

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username from database (Async)"""
        try:
            admin = await self._get_admin_client()
            query = "*, roles(name, role_permissions(permissions(code)))"
            result = await admin.table("users").select(query).eq("username", username).maybe_single().execute()
            if result and result.data:
                return self._map_db_user_to_model(result.data)
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by username: %s", e)
            return None

    async def create_unverified_user(self, email: str, password: str, name: str) -> dict[str, Any]:
        """Create a new user without sending a confirmation email (Async)"""
        try:
            admin = await self._get_admin_client()
            res = await admin.auth.admin.create_user(
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
            msg = str(e)
            if any(term in msg.lower() for term in ["already registered", "unique constraint"]):
                raise ConflictError(ERROR_EMAIL_ALREADY_REGISTERED)
            logger.error("Failed to create unverified account: %s", msg)
            raise PurrfectSpotsException(ERROR_FAILED_TO_CREATE_USER)

    async def create_or_get_user(self, user_data: dict[str, Any]) -> User:
        """Create new user or get existing user from database for OAuth (Async)"""
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
            }

            admin = await self._get_admin_client()
            existing_check = await admin.table("users").select("role_id").eq("id", user_id).execute()
            if not existing_check.data or not existing_check.data[0].get("role_id"):
                user_record["role_id"] = await self._get_user_role_id()

            await admin.table("users").upsert(user_record, on_conflict="id").execute()

            user = await self.get_user_by_id(user_id)
            if not user:
                raise ExternalServiceError("Failed to retrieve user after creation", service="Supabase Database")
            return user
        except Exception as e:
            raise ExternalServiceError(f"Database error: {e!s}", service="Supabase Database")

    async def authenticate_user(self, email: str, password: str) -> dict[str, Any] | None:
        """Authenticate user using Supabase Auth (Async)"""
        try:
            res = await self.supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.user and res.session:
                user = await self.get_user_by_id(res.user.id)
                if user:
                    user_dict = user.model_dump()
                    user_dict.update(
                        {
                            "access_token": res.session.access_token,
                            "refresh_token": res.session.refresh_token,
                        }
                    )
                    return user_dict

                return {
                    "id": res.user.id,
                    "email": res.user.email,
                    "name": res.user.user_metadata.get("name", ""),
                    "picture": res.user.user_metadata.get("avatar_url", ""),
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                    "created_at": res.user.created_at,
                    "permissions": [],
                    "role": "user",
                }
            return None
        except Exception as e:
            logger.warning("Authentication failure: %s", e)
            return None

    async def update_user_profile(
        self, user_id: str, update_data: dict[str, Any], jwt_token: str | None = None
    ) -> dict[str, Any]:
        """Update user profile (Async)"""
        try:
            admin = await self._get_admin_client()
            result = await admin.table("users").update(update_data).eq("id", user_id).execute()
            if not result or not result.data:
                raise ValueError("User not found or update failed")
            from typing import cast

            return cast(dict[str, Any], result.data[0])
        except Exception as e:
            raise PurrfectSpotsException(f"Failed to update profile: {e!s}")

    async def cancel_account_deletion(self, user_id: str) -> dict[str, str]:
        """Cancel an ongoing account deletion request"""
        try:
            admin = await self._get_admin_client()

            # Check if pending request exists
            existing_reqs = await admin.table("account_deletion_requests").select("id").eq("user_id", user_id).eq("status", "pending").execute()
            if not existing_reqs.data:
                raise ConflictError("ไม่มีคำขอลบบัญชีที่รอดำเนินการ")

            # Update users table to remove deleted_at
            await admin.table("users").update({"deleted_at": None}).eq("id", user_id).execute()

            # Update request status to cancelled
            await admin.table("account_deletion_requests").update({"status": "cancelled"}).eq("user_id", user_id).eq("status", "pending").execute()

            # Insert audit log
            await admin.table("audit_logs").insert({
                "action": "ACCOUNT_DELETION_CANCELLED",
                "user_id": user_id,
                "resource": "users",
            }).execute()

            logger.info("account_deletion_cancelled", extra={"user_id": user_id})
            return {"status": "success", "message": "Account deletion request cancelled successfully."}
        except Exception as e:
            if isinstance(e, ConflictError):
                raise
            logger.error("Failed to cancel account deletion: %s", e)
            raise PurrfectSpotsException("Failed to cancel account deletion")

    async def request_account_deletion(self, user_id: str, client_ip: str) -> dict[str, str]:
        """Request soft deletion of the user account"""
        try:
            admin = await self._get_admin_client()
            user_record = await self.get_user_by_id(user_id)
            if not user_record:
                raise PurrfectSpotsException("User not found")
        except Exception as e:
            if isinstance(e, (ConflictError, PurrfectSpotsException)):
                raise e
            raise ConflictError("Failed to request account deletion")

        scheduled_date = datetime.now(UTC) + timedelta(days=30)

        try:
            admin = await self._get_admin_client()
            # Soft delete in users table
            await admin.table("users").update({"deleted_at": datetime.now(UTC).isoformat()}).eq("id", user_id).execute()

            # Disable related components if needed, e.g., if we want to immediately hide reviews, we could add deleted_at to reviews or just filter by user.deleted_at on read.

            # Insert into account_deletion_requests
            await admin.table("account_deletion_requests").insert({
                "user_id": user_id,
                "scheduled_deletion_at": scheduled_date.isoformat(),
                "status": "pending",
                "client_ip": client_ip
            }).execute()

            # Insert audit log
            await admin.table("audit_logs").insert({
                "action": "ACCOUNT_SOFT_DELETED",
                "user_id": user_id,
                "resource": "users",
            }).execute()

            logger.info(
                "account_deletion_requested",
                extra={
                    "user_id": user_id,
                    "scheduled_for": scheduled_date.isoformat(),
                }
            )
            return {"status": "success", "message": "Account marked for deletion. You have 30 days to cancel."}
        except Exception as e:
            logger.error("Failed to request account deletion: %s", e)
            raise PurrfectSpotsException("Failed to request account deletion")

    async def execute_hard_delete(self) -> None:
        """Service to be run by a Cron Job to permanently delete expired accounts"""
        try:
            admin = await self._get_admin_client()
            now = datetime.now(UTC).isoformat()

            expired_reqs = await admin.table("account_deletion_requests").select("user_id, id").eq("status", "pending").lte("scheduled_deletion_at", now).execute()

            if not expired_reqs.data:
                return

            for req in expired_reqs.data:
                user_id = req["user_id"]
                try:
                    # Note: You can add photo cleanup here: wait admin.storage.from_("avatars").remove([f"{user_id}/avatar.png"])

                    # Hard delete user from Auth
                    await admin.auth.admin.delete_user(user_id)

                    await admin.table("account_deletion_requests").update({"status": "completed"}).eq("id", req["id"]).execute()

                    await admin.table("audit_logs").insert({
                        "action": "ACCOUNT_HARD_DELETED",
                        "user_id": user_id,
                        "resource": "users",
                    }).execute()

                    logger.info("account_hard_deleted", extra={"user_id": user_id})
                except Exception as e:
                    logger.error("account_hard_delete_failed", extra={"user_id": user_id, "error": str(e)})
        except Exception as e:
            logger.error("Failed to run execute_hard_delete: %s", e)
