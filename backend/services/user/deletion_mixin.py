from datetime import UTC, datetime, timedelta

from sqlalchemy import text

import structlog  # type: ignore[import-untyped, unused-ignore]
from services.user.base_mixin import UserBaseMixin
from utils.exceptions import ConflictError, PurrfectSpotsException

logger = structlog.get_logger(__name__)


class UserDeletionMixin(UserBaseMixin):
    """Mixin for account deletion operations."""

    async def cancel_account_deletion(self, user_id: str) -> dict[str, str]:
        """Cancel an ongoing account deletion request"""
        try:
            if self.db:
                check_query = text(
                    "SELECT id FROM account_deletion_requests WHERE user_id = :u_id AND status = 'pending' LIMIT 1"
                )
                check_res = await self.db.execute(check_query, {"u_id": user_id})
                if not check_res.fetchone():
                    raise ConflictError("ไม่มีคำขอลบบัญชีที่รอดำเนินการ")

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
                existing_reqs = (
                    await admin.table("account_deletion_requests")
                    .select("id")
                    .eq("user_id", user_id)
                    .eq("status", "pending")
                    .execute()
                )
                if not existing_reqs.data:
                    raise ConflictError("ไม่มีคำขอลบบัญชีที่รอดำเนินการ")

                await admin.table("users").update({"deleted_at": None}).eq("id", user_id).execute()
                await (
                    admin.table("account_deletion_requests")
                    .update({"status": "cancelled"})
                    .eq("user_id", user_id)
                    .eq("status", "pending")
                    .execute()
                )
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
            # Need to use the main class's get_user_by_id (inherited via mixins)
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
                await (
                    admin.table("users")
                    .update({"deleted_at": datetime.now(UTC).isoformat()})
                    .eq("id", user_id)
                    .execute()
                )

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
            from typing import Any, cast

            data: list[dict[str, Any]] = []
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
                data = cast(list[dict[str, Any]], expired_reqs.data or [])

            if not data:
                return

            admin = await self._get_admin_client()
            for req in data:
                user_id = req["user_id"]
                try:
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
