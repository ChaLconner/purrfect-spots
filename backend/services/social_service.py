from typing import Any, cast

from supabase import AClient

from exceptions import ExternalServiceError, NotFoundError
from logger import logger
from schemas.notification import NotificationType
from services.notification_service import NotificationService


class SocialService:
    def __init__(self, supabase_client: AClient) -> None:
        self.supabase = supabase_client
        self.notification_service = NotificationService(supabase_client)

    async def toggle_like(self, user_id: str, photo_id: str, jwt_token: str | None = None) -> dict[str, Any]:
        """
        Toggle like status for a photo using atomic database function.
        """
        try:
            from utils.supabase_client import get_async_supabase_admin_client

            # Use admin client to bypass RLS/JWT issues with RPC
            admin_client = await get_async_supabase_admin_client()

            res = await admin_client.rpc("toggle_photo_like", {"p_user_id": user_id, "p_photo_id": photo_id}).execute()

            data = res.data
            if not data or len(data) == 0:
                raise ExternalServiceError("Toggle like returned no data", service="Supabase")

            row = data[0]
            liked = row["liked"]
            likes_count = row["likes_count"]

            # Invalidate caches to reflect new like status
            from utils.cache import invalidate_gallery_cache, invalidate_user_cache

            await invalidate_user_cache(user_id)
            await invalidate_gallery_cache()

            return {"liked": liked, "likes_count": likes_count}

        except Exception as e:
            error_msg = str(e)

            # Check for specific error codes from our RPC function
            if "P0002" in error_msg or "Photo not found" in error_msg:
                raise NotFoundError(message="Photo not found", resource_type="photo", resource_id=photo_id)

            logger.error("Toggle like failed for user=%r photo=%r: %s", user_id, photo_id, e)
            raise ExternalServiceError(
                message=f"Failed to toggle like: {error_msg}", service="Supabase", retryable=True
            )

    async def add_comment(
        self, user_id: str, photo_id: str, content: str, jwt_token: str | None = None
    ) -> dict[str, Any]:
        """Add a comment to a photo."""
        from utils.supabase_client import get_async_supabase_admin_client

        # Validate photo exists first
        res = (
            await self.supabase.table("cat_photos")
            .select("id, user_id")
            .eq("id", photo_id)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )

        if not res.data:
            raise NotFoundError(message="Photo not found", resource_type="photo", resource_id=photo_id)

        photo_owner_id = res.data[0].get("user_id")

        # Insert comment using service role client
        admin_client = await get_async_supabase_admin_client()
        res = (
            await admin_client.table("photo_comments")
            .insert({"user_id": user_id, "photo_id": photo_id, "content": content})
            .execute()
        )

        if not res.data:
            raise ExternalServiceError("Failed to create comment", service="Supabase")

        comment = res.data[0]

        # Enrichment
        user_res = await self.supabase.table("users").select("name, picture").eq("id", user_id).limit(1).execute()

        user_name = "Someone"
        if user_res.data:
            user_name = user_res.data[0].get("name")
            comment["user_name"] = user_name
            comment["user_picture"] = user_res.data[0].get("picture")

        # Trigger Notification
        try:
            if photo_owner_id and photo_owner_id != user_id:
                await self.notification_service.create_notification(
                    user_id=photo_owner_id,
                    actor_id=user_id,
                    type=NotificationType.COMMENT.value,
                    title="New Comment",
                    message=f"{user_name} commented: {content[:50]}{'...' if len(content) > 50 else ''}",
                    resource_id=photo_id,
                    resource_type="photo",
                )
        except Exception as e:
            logger.warning(f"Failed to send comment notification: {e}")

        return cast(dict[str, Any], comment)

    async def get_comments(self, photo_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get comments for a photo."""
        res = (
            await self.supabase.table("photo_comments")
            .select("*, users(name, picture)")
            .eq("photo_id", photo_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )

        data = res.data or []
        comments = []
        for item in data:
            user_data = item.get("users", {}) or {}
            # Flatten structure
            item["user_name"] = user_data.get("name")
            item["user_picture"] = user_data.get("picture")
            if "users" in item:
                del item["users"]
            comments.append(item)

        return comments

    async def delete_comment(self, user_id: str, comment_id: str, jwt_token: str | None = None) -> bool:
        """Delete a comment."""
        from utils.supabase_client import get_async_supabase_admin_client

        # Delete using admin client to ensure success or check ownership
        admin_client = await get_async_supabase_admin_client()
        res = await admin_client.table("photo_comments").delete().eq("id", comment_id).eq("user_id", user_id).execute()

        return len(res.data) > 0
