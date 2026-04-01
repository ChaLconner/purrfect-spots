import re
from datetime import UTC
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
from supabase import AClient

_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _is_valid_uuid(value: str | None) -> bool:
    """Check if a string is a valid UUID format."""
    if not value or not isinstance(value, str):
        return False
    return bool(_UUID_PATTERN.match(value))


class NotificationService:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db

    async def create_notification(
        self,
        user_id: str,
        type: str,
        message: str,
        title: str | None = None,
        actor_id: str | None = None,
        resource_id: str | None = None,
        resource_type: str | None = None,
    ) -> dict[str, Any]:
        """Create a new notification.

        Validates user_id format before inserting to prevent PostgreSQL
        errors (22P02 invalid UUID, 23503 FK constraint violations).
        """
        if user_id == actor_id:
            return {}  # Don't notify self

        # Validate user_id is a valid UUID before hitting the DB
        if not _is_valid_uuid(user_id):
            logger.warning(
                "Skipping notification: invalid user_id format '%s' (type=%s, resource_id=%s)",
                user_id,
                type,
                resource_id,
            )
            return {}

        # Validate actor_id format if provided (also a UUID FK)
        if actor_id and not _is_valid_uuid(actor_id):
            logger.warning(
                "Skipping notification: invalid actor_id format '%s'",
                actor_id,
            )
            return {}

        # Validate resource_id format if provided (UUID field in DB)
        valid_resource_id = resource_id
        if resource_id and not _is_valid_uuid(resource_id):
            logger.warning(
                "Notification: invalid resource_id format '%s' for type '%s'. Setting to None.",
                resource_id,
                type,
            )
            valid_resource_id = None

        data = {
            "user_id": user_id,
            "type": type,
            "message": message,
            "title": title,
            "actor_id": actor_id,
            "resource_id": valid_resource_id,
            "resource_type": resource_type,
        }

        try:
            if self.db:
                db_session = self.db
                query = text(
                    "INSERT INTO notifications (user_id, type, message, title, actor_id, resource_id, resource_type) "
                    "VALUES (:user_id, :type, :message, :title, :actor_id, :resource_id, :resource_type) "
                    "RETURNING *"
                )
                result = await db_session.execute(query, data)
                await db_session.commit()
                row = result.fetchone()
                return dict(row._mapping) if row else {}
            res = await self.supabase.table("notifications").insert(data).execute()
            return res.data[0] if res.data else {}
        except Exception as e:
            error_str = str(e)
            # Handle FK constraint violation (user doesn't exist) gracefully
            if "23503" in error_str:
                logger.warning(
                    "Notification skipped: user_id '%s' does not exist in users table (FK violation)",
                    user_id,
                )
            else:
                logger.error("Failed to create notification for user %s: %s", user_id, e)
            return {}

    async def get_notifications(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """Get user notifications with actor details."""
        from datetime import datetime, timedelta

        thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()

        try:
            if self.db:
                db_session = self.db
                query = text(
                    "SELECT n.*, u.name as actor_name, u.picture as actor_picture "
                    "FROM notifications n "
                    "LEFT JOIN users u ON n.actor_id = u.id "
                    "WHERE n.user_id = :u_id AND n.created_at >= :since "
                    "ORDER BY n.created_at DESC LIMIT :lim OFFSET :off"
                )
                db_res = await db_session.execute(
                    query, {"u_id": user_id, "since": thirty_days_ago, "lim": limit, "off": offset}
                )
                notifications = []
                for row in db_res.fetchall():
                    notifications.append(dict(row._mapping))
                return notifications
            supa_res = await (
                self.supabase.table("notifications")
                .select("*, actor:users!actor_id(name, picture)")
                .eq("user_id", user_id)
                .gte("created_at", thirty_days_ago)
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )

            notifications = []
            for item in supa_res.data:
                actor = item.get("actor", {}) or {}
                item["actor_name"] = actor.get("name")
                item["actor_picture"] = actor.get("picture")
                item.pop("actor", None)
                notifications.append(item)

            return notifications
        except Exception as e:
            logger.error(f"Failed to fetch notifications for user {user_id}: {e}")
            return []

    async def mark_as_read(self, user_id: str, notification_id: str) -> None:
        """Mark single notification as read."""
        try:
            if self.db:
                db_session = self.db
                query = text("UPDATE notifications SET is_read = True WHERE id = :n_id AND user_id = :u_id")
                await db_session.execute(query, {"n_id": notification_id, "u_id": user_id})
                await db_session.commit()
            else:
                await (
                    self.supabase.table("notifications")
                    .update({"is_read": True})
                    .eq("id", notification_id)
                    .eq("user_id", user_id)
                    .execute()
                )
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")

    async def mark_all_as_read(self, user_id: str) -> None:
        """Mark all notifications as read."""
        try:
            if self.db:
                db_session = self.db
                query = text("UPDATE notifications SET is_read = True WHERE user_id = :u_id AND is_read = False")
                await db_session.execute(query, {"u_id": user_id})
                await db_session.commit()
            else:
                await (
                    self.supabase.table("notifications")
                    .update({"is_read": True})
                    .eq("user_id", user_id)
                    .eq("is_read", False)
                    .execute()
                )
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read: {e}")

    async def cleanup_old_notifications(self, days: int = 30) -> None:
        """Delete notifications older than specified days."""
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        try:
            if self.db:
                db_session = self.db
                query = text("DELETE FROM notifications WHERE created_at < :cutoff")
                result = await db_session.execute(query, {"cutoff": cutoff_date})
                await db_session.commit()
                deleted_count = cast(Any, result).rowcount
            else:
                res = await self.supabase.table("notifications").delete().lt("created_at", cutoff_date).execute()
                deleted_count = len(res.data) if res.data else 0
            logger.info(f"Successfully cleaned up {deleted_count} notifications older than {days} days")
        except Exception as e:
            logger.error(f"Failed to clean up old notifications: {e}")
