import re
from datetime import UTC
from typing import Any

from supabase import AClient

from logger import logger

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
    def __init__(self, supabase_client: AClient) -> None:
        self.supabase = supabase_client

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

        res = await (
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
        for item in res.data:
            actor = item.get("actor", {}) or {}
            item["actor_name"] = actor.get("name")
            item["actor_picture"] = actor.get("picture")
            del item["actor"]
            notifications.append(item)

        return notifications

    async def mark_as_read(self, user_id: str, notification_id: str) -> None:
        """Mark single notification as read."""

        await (
            self.supabase.table("notifications")
            .update({"is_read": True})
            .eq("id", notification_id)
            .eq("user_id", user_id)
            .execute()
        )

    async def mark_all_as_read(self, user_id: str) -> None:
        """Mark all notifications as read."""

        await (
            self.supabase.table("notifications")
            .update({"is_read": True})
            .eq("user_id", user_id)
            .eq("is_read", False)
            .execute()
        )

    async def cleanup_old_notifications(self, days: int = 30) -> None:
        """Delete notifications older than specified days."""
        from datetime import datetime, timedelta

        cutoff_date = (datetime.now(UTC) - timedelta(days=days)).isoformat()

        try:
            res = await self.supabase.table("notifications").delete().lt("created_at", cutoff_date).execute()
            deleted_count = len(res.data) if res.data else 0
            logger.info(f"Successfully cleaned up {deleted_count} notifications older than {days} days")
        except Exception as e:
            logger.error(f"Failed to clean up old notifications: {e}")
