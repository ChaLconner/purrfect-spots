from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
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

    def __init__(
        self, supabase_client: AClient, supabase_admin: AClient | None = None, db: AsyncSession | None = None
    ) -> None:
        self.supabase = supabase_client
        self.supabase_admin = supabase_admin
        self.db = db

    async def _get_admin_client(self) -> AClient:
        if self.supabase_admin:
            return self.supabase_admin
        return await get_async_supabase_admin_client()

    async def _get_user_role_id(self) -> str | None:
        """Get the ID of the 'user' role from the roles table (Async)"""
        if UserService._cached_user_role_id:
            return UserService._cached_user_role_id

        try:
            if self.db:
                query = text("SELECT id FROM roles WHERE name = 'user' LIMIT 1")
                result = await self.db.execute(query)
                row = result.fetchone()
                if row:
                    UserService._cached_user_role_id = str(row[0])
                    return UserService._cached_user_role_id
            else:
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

        user_fields.pop("roles", None)

        return User(**user_fields, permissions=permissions)

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID from database with Role and Permissions (Async)"""
        try:
            if self.db:
                # Use SQLAlchemy with JOINs for efficiency
                query = text(
                    "SELECT u.*, r.name as role_name "
                    "FROM users u "
                    "LEFT JOIN roles r ON u.role_id = r.id "
                    "WHERE u.id = :u_id LIMIT 1"
                )
                db_res = await self.db.execute(query, {"u_id": user_id})
                row = db_res.fetchone()
                if row:
                    data = dict(row._mapping)
                    # Fetch permissions separately or via another join
                    perm_query = text(
                        "SELECT p.code FROM permissions p "
                        "JOIN role_permissions rp ON p.id = rp.permission_id "
                        "JOIN users u ON rp.role_id = u.role_id "
                        "WHERE u.id = :u_id"
                    )
                    perm_db_res = await self.db.execute(perm_query, {"u_id": user_id})
                    permissions = [r[0] for r in perm_db_res]

                    user_data = data.copy()
                    user_data["role"] = data.get("role_name")
                    return User(**user_data, permissions=permissions)
            else:
                query_str = "*, roles(name, role_permissions(permissions(code)))"
                admin = await self._get_admin_client()
                supa_res = await admin.table("users").select(query_str).eq("id", user_id).execute()
                if supa_res.data:
                    return self._map_db_user_to_model(supa_res.data[0])
            return None
        except Exception as e:
            logger.debug("Failed to retrieve profile by ID: %s", e)
            return None

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Get user by email from database (Async)"""
        try:
            if self.db:
                query = text("SELECT * FROM users WHERE email = :email LIMIT 1")
                db_res = await self.db.execute(query, {"email": email})
                row = db_res.fetchone()
                return dict(row._mapping) if row else None
            admin = await self._get_admin_client()
            supa_res = await admin.table("users").select("*").eq("email", email).maybe_single().execute()
            return supa_res.data if supa_res and supa_res.data else None
        except Exception as e:
            logger.debug("Failed to retrieve profile by email: %s", e)
            return None

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username from database (Async)"""
        try:
            if self.db:
                query = text(
                    "SELECT u.*, r.name as role_name "
                    "FROM users u "
                    "LEFT JOIN roles r ON u.role_id = r.id "
                    "WHERE u.username = :username LIMIT 1"
                )
                result = await self.db.execute(query, {"username": username})
                row = result.fetchone()
                if row:
                    data = dict(row._mapping)
                    # Fetch permissions
                    perm_query = text(
                        "SELECT p.code FROM permissions p "
                        "JOIN role_permissions rp ON p.id = rp.permission_id "
                        "JOIN users u ON rp.role_id = u.role_id "
                        "WHERE u.username = :username"
                    )
                    perm_res = await self.db.execute(perm_query, {"username": username})
                    permissions = [r[0] for r in perm_res]

                    user_data = data.copy()
                    user_data["role"] = data.get("role_name")
                    return User(**user_data, permissions=permissions)
            else:
                admin = await self._get_admin_client()
                query_str = "*, roles(name, role_permissions(permissions(code)))"
                supa_res = (
                    await admin.table("users").select(query_str).eq("username", username).maybe_single().execute()
                )
                if supa_res and supa_res.data:
                    return self._map_db_user_to_model(supa_res.data)
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

            user_record = self._prepare_user_record(user_data, user_id)

            if self.db:
                await self._upsert_user_sql(user_id, user_record)
            else:
                await self._upsert_user_supabase(user_id, user_record)

            user = await self.get_user_by_id(user_id)
            if not user:
                raise ExternalServiceError("Failed to retrieve user after creation", service="Supabase Database")
            return user
        except Exception as e:
            if self.db:
                await self.db.rollback()
            raise ExternalServiceError(f"Database error: {e!s}", service="Supabase Database")

    def _prepare_user_record(self, user_data: dict[str, Any], user_id: str) -> dict[str, Any]:
        """Prepare user record for upsert."""
        return {
            "id": user_id,
            "email": user_data.get("email", ""),
            "name": user_data.get("name", ""),
            "picture": user_data.get("picture", ""),
            "google_id": user_data.get("google_id"),
            "bio": None,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }

    async def _upsert_user_sql(self, user_id: str, user_record: dict[str, Any]) -> None:
        """Upsert user using SQLAlchemy."""
        if not self.db:
            return

        # Check for existing role
        check_query = text("SELECT role_id FROM users WHERE id = :u_id LIMIT 1")
        check_res = await self.db.execute(check_query, {"u_id": user_id})
        check_row = check_res.fetchone()

        if not check_row or not check_row[0]:
            user_record["role_id"] = await self._get_user_role_id()

        # Construct upsert query
        # Whitelist columns to prevent SQL injection
        allowed_columns = {"id", "email", "name", "picture", "google_id", "bio", "created_at", "updated_at", "role_id"}
        columns_list = [c for c in user_record if c in allowed_columns]
        columns = ", ".join(columns_list)
        placeholders = ", ".join([f":{c}" for c in columns_list])
        update_cols = ["email", "name", "picture", "google_id", "updated_at"]
        update_stmt = ", ".join([f"{c} = EXCLUDED.{c}" for c in update_cols])

        upsert_query = text(
            f"INSERT INTO users ({columns}) VALUES ({placeholders}) "  # noqa: S608
            f"ON CONFLICT (id) DO UPDATE SET {update_stmt}"
        )

        await self.db.execute(upsert_query, {k: user_record[k] for k in columns_list})
        await self.db.commit()

    async def _upsert_user_supabase(self, user_id: str, user_record: dict[str, Any]) -> None:
        """Upsert user using Supabase."""
        admin = await self._get_admin_client()
        existing_check = await admin.table("users").select("role_id").eq("id", user_id).execute()

        if not existing_check.data or not existing_check.data[0].get("role_id"):
            user_record["role_id"] = await self._get_user_role_id()

        await admin.table("users").upsert(user_record, on_conflict="id").execute()

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
            if self.db:
                # Construct dynamic UPDATE query
                # SAFETY: Columns are from checked set or model keys
                safe_cols = [k for k in update_data if k in {"name", "username", "bio", "picture", "role_id"}]
                cols = ", ".join([f"{k} = :{k}" for k in safe_cols])
                query = text(f"UPDATE users SET {cols}, updated_at = NOW() WHERE id = :u_id RETURNING *")  # noqa: S608
                params = {**{k: v for k, v in update_data.items() if k in safe_cols}, "u_id": user_id}
                db_res = await self.db.execute(query, params)
                row = db_res.fetchone()
                if not row:
                    raise ValueError("User not found or update failed")
                await self.db.commit()
                return dict(row._mapping)
            admin = await self._get_admin_client()
            supa_res = await admin.table("users").update(update_data).eq("id", user_id).execute()
            if not supa_res or not supa_res.data:
                raise ValueError("User not found or update failed")
            from typing import cast

            return cast(dict[str, Any], supa_res.data[0])
        except Exception as e:
            if self.db:
                await self.db.rollback()
            raise PurrfectSpotsException(f"Failed to update profile: {e!s}")

    async def cancel_account_deletion(self, user_id: str) -> dict[str, str]:
        """Cancel an ongoing account deletion request"""
        try:
            if self.db:
                # Check for pending request
                check_query = text(
                    "SELECT id FROM account_deletion_requests WHERE user_id = :u_id AND status = 'pending' LIMIT 1"
                )
                check_res = await self.db.execute(check_query, {"u_id": user_id})
                if not check_res.fetchone():
                    raise ConflictError("ไม่มีคำขอลบบัญชีที่รอดำเนินการ")

                # Update tables
                await self.db.execute(text("UPDATE users SET deleted_at = NULL WHERE id = :u_id"), {"u_id": user_id})
                await self.db.execute(
                    text(
                        "UPDATE account_deletion_requests SET status = 'cancelled' WHERE user_id = :u_id AND status = 'pending'"
                    ),
                    {"u_id": user_id},
                )
                await self.db.execute(
                    text(
                        "INSERT INTO audit_logs (action, user_id, resource) VALUES ('ACCOUNT_DELETION_CANCELLED', :u_id, 'users')"
                    ),
                    {"u_id": user_id},
                )
                await self.db.commit()
            else:
                admin = await self._get_admin_client()

                # Check if pending request exists
                existing_reqs = (
                    await admin.table("account_deletion_requests")
                    .select("id")
                    .eq("user_id", user_id)
                    .eq("status", "pending")
                    .execute()
                )
                if not existing_reqs.data:
                    raise ConflictError("ไม่มีคำขอลบบัญชีที่รอดำเนินการ")

                # Update users table to remove deleted_at
                await admin.table("users").update({"deleted_at": None}).eq("id", user_id).execute()

                # Update request status to cancelled
                await (
                    admin.table("account_deletion_requests")
                    .update({"status": "cancelled"})
                    .eq("user_id", user_id)
                    .eq("status", "pending")
                    .execute()
                )

                # Insert audit log
                await (
                    admin.table("audit_logs")
                    .insert(
                        {
                            "action": "ACCOUNT_DELETION_CANCELLED",
                            "user_id": user_id,
                            "resource": "users",
                        }
                    )
                    .execute()
                )

            logger.info("account_deletion_cancelled", extra={"user_id": user_id})
            return {"status": "success", "message": "Account deletion request cancelled successfully."}
        except Exception as e:
            if self.db:
                await self.db.rollback()
            if isinstance(e, ConflictError):
                raise
            logger.error("Failed to cancel account deletion: %s", e)
            raise PurrfectSpotsException("Failed to cancel account deletion")

    async def request_account_deletion(self, user_id: str, client_ip: str) -> dict[str, str]:
        """Request soft deletion of the user account"""
        try:
            user_record = await self.get_user_by_id(user_id)
            if not user_record:
                raise PurrfectSpotsException("User not found")
        except Exception as e:
            if isinstance(e, (ConflictError, PurrfectSpotsException)):
                raise e
            raise ConflictError("Failed to request account deletion")

        scheduled_date = datetime.now(UTC) + timedelta(days=30)

        try:
            if self.db:
                now_iso = datetime.now(UTC).isoformat()
                await self.db.execute(
                    text("UPDATE users SET deleted_at = :now WHERE id = :u_id"), {"now": now_iso, "u_id": user_id}
                )
                await self.db.execute(
                    text(
                        "INSERT INTO account_deletion_requests (user_id, scheduled_deletion_at, status, client_ip) VALUES (:u_id, :sched, 'pending', :ip)"
                    ),
                    {"u_id": user_id, "sched": scheduled_date.isoformat(), "ip": client_ip},
                )
                await self.db.execute(
                    text(
                        "INSERT INTO audit_logs (action, user_id, resource) VALUES ('ACCOUNT_SOFT_DELETED', :u_id, 'users')"
                    ),
                    {"u_id": user_id},
                )
                await self.db.commit()
            else:
                admin = await self._get_admin_client()
                # Soft delete in users table
                await (
                    admin.table("users")
                    .update({"deleted_at": datetime.now(UTC).isoformat()})
                    .eq("id", user_id)
                    .execute()
                )

                # Insert into account_deletion_requests
                await (
                    admin.table("account_deletion_requests")
                    .insert(
                        {
                            "user_id": user_id,
                            "scheduled_deletion_at": scheduled_date.isoformat(),
                            "status": "pending",
                            "client_ip": client_ip,
                        }
                    )
                    .execute()
                )

                # Insert audit log
                await (
                    admin.table("audit_logs")
                    .insert(
                        {
                            "action": "ACCOUNT_SOFT_DELETED",
                            "user_id": user_id,
                            "resource": "users",
                        }
                    )
                    .execute()
                )

            logger.info(
                "account_deletion_requested",
                extra={
                    "user_id": user_id,
                    "scheduled_for": scheduled_date.isoformat(),
                },
            )
            return {"status": "success", "message": "Account marked for deletion. You have 30 days to cancel."}
        except Exception as e:
            if self.db:
                await self.db.rollback()
            logger.error("Failed to request account deletion: %s", e)
            raise PurrfectSpotsException("Failed to request account deletion")

    async def execute_hard_delete(self) -> None:
        """Service to be run by a Cron Job to permanently delete expired accounts"""
        try:
            data = []
            if self.db:
                now = datetime.now(UTC).isoformat()
                query = text(
                    "SELECT user_id, id FROM account_deletion_requests WHERE status = 'pending' AND scheduled_deletion_at <= :now"
                )
                result = await self.db.execute(query, {"now": now})
                data = [dict(row._mapping) for row in result]
            else:
                admin = await self._get_admin_client()
                now = datetime.now(UTC).isoformat()
                expired_reqs = (
                    await admin.table("account_deletion_requests")
                    .select("user_id, id")
                    .eq("status", "pending")
                    .lte("scheduled_deletion_at", now)
                    .execute()
                )
                data = expired_reqs.data or []

            if not data:
                return

            admin = await self._get_admin_client()
            for req in data:
                user_id = req["user_id"]
                try:
                    # Hard delete user from Auth (must use Supabase client)
                    await admin.auth.admin.delete_user(user_id)

                    if self.db:
                        await self.db.execute(
                            text("UPDATE account_deletion_requests SET status = 'completed' WHERE id = :id"),
                            {"id": req["id"]},
                        )
                        await self.db.execute(
                            text(
                                "INSERT INTO audit_logs (action, user_id, resource) VALUES ('ACCOUNT_HARD_DELETED', :u_id, 'users')"
                            ),
                            {"u_id": user_id},
                        )
                        await self.db.commit()
                    else:
                        await (
                            admin.table("account_deletion_requests")
                            .update({"status": "completed"})
                            .eq("id", req["id"])
                            .execute()
                        )
                        await (
                            admin.table("audit_logs")
                            .insert(
                                {
                                    "action": "ACCOUNT_HARD_DELETED",
                                    "user_id": user_id,
                                    "resource": "users",
                                }
                            )
                            .execute()
                        )

                    logger.info("account_hard_deleted", extra={"user_id": user_id})
                except Exception as e:
                    if self.db:
                        await self.db.rollback()
                    logger.error("account_hard_delete_failed", extra={"user_id": user_id, "error": str(e)})
        except Exception as e:
            logger.error("Failed to run execute_hard_delete: %s", e)
