from typing import Any, Dict, List, Optional

from supabase import Client


class NotificationService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def create_notification(
        self,
        user_id: str,
        type: str,
        message: str,
        title: Optional[str] = None,
        actor_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new notification."""
        if user_id == actor_id:
            return {} # Don't notify self

        data = {
            "user_id": user_id,
            "type": type,
            "message": message,
            "title": title,
            "actor_id": actor_id,
            "resource_id": resource_id,
            "resource_type": resource_type
        }
        res = self.supabase.table("notifications").insert(data).execute()
        return res.data[0] if res.data else {}

    async def get_notifications(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get user notifications with actor details."""
        res = self.supabase.table("notifications").select(
            "*, actor:users!actor_id(name, picture)"
        ).eq("user_id", user_id).order("created_at", desc=True).limit(limit).offset(offset).execute()
        
        notifications = []
        for item in res.data:
            actor = item.get("actor", {}) or {}
            item["actor_name"] = actor.get("name")
            item["actor_picture"] = actor.get("picture")
            del item["actor"]
            notifications.append(item)
            
        return notifications

    async def mark_as_read(self, user_id: str, notification_id: str):
        """Mark single notification as read."""
        self.supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).eq("user_id", user_id).execute()

    async def mark_all_as_read(self, user_id: str):
        """Mark all notifications as read."""
        self.supabase.table("notifications").update({"is_read": True}).eq("user_id", user_id).eq("is_read", False).execute()
