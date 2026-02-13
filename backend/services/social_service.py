import asyncio
from typing import Any, Dict, List

from supabase import Client

from exceptions import ExternalServiceError, NotFoundError
from logger import logger
from schemas.notification import NotificationType
from services.notification_service import NotificationService


class SocialService:
    def __init__(self, supabase_client: Client) -> None:
        self.supabase = supabase_client
        self.notification_service = NotificationService(supabase_client)

    async def toggle_like(self, user_id: str, photo_id: str) -> Dict[str, Any]:
        """
        Toggle like status for a photo using atomic database function.
        
        This uses a PostgreSQL function to ensure atomicity and prevent race conditions.
        The function handles:
        - Photo existence validation
        - Atomic toggle (check + insert/delete in one transaction)
        - Likes count update via trigger
        
        Args:
            user_id: The ID of the user performing the action
            photo_id: The ID of the photo to like/unlike
            
        Returns:
            Dict with 'liked' (bool) and 'likes_count' (int)
            
        Raises:
            NotFoundError: If the photo doesn't exist
            ExternalServiceError: If the database operation fails
        """
        try:
            # Run sync Supabase RPC call in thread pool to avoid blocking event loop
            def _rpc_toggle() -> Any:
                return self.supabase.rpc(
                    "toggle_photo_like",
                    {"p_user_id": user_id, "p_photo_id": photo_id}
                ).execute()

            result = await asyncio.to_thread(_rpc_toggle)
            
            if not result.data or len(result.data) == 0:
                raise ExternalServiceError("Toggle like returned no data", service="Supabase")
            
            row = result.data[0]
            liked = row["liked"]
            likes_count = row["likes_count"]
            
            # Notification is now handled by database trigger
            
            # Invalidate caches to reflect new like status
            from utils.cache import invalidate_gallery_cache, invalidate_user_cache
            await invalidate_user_cache(user_id)
            await invalidate_gallery_cache()
            
            return {"liked": liked, "likes_count": likes_count}
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for specific error codes from our RPC function
            if "P0002" in error_msg or "Photo not found" in error_msg:
                raise NotFoundError(
                    message="Photo not found",
                    resource_type="photo",
                    resource_id=photo_id
                )
            
            logger.error(f"Toggle like failed for user={user_id} photo={photo_id}: {e}")
            raise ExternalServiceError(
                message=f"Failed to toggle like: {error_msg}",
                service="Supabase",
                retryable=True
            )

    async def add_comment(self, user_id: str, photo_id: str, content: str) -> Dict[str, Any]:
        """Add a comment to a photo."""
        # Validate photo exists first (run in thread pool)
        def _check_photo() -> Any:
            return (
                self.supabase.table("cat_photos")
                .select("id, user_id")
                .eq("id", photo_id)
                .is_("deleted_at", "null")
                .single()
                .execute()
            )

        photo_check = await asyncio.to_thread(_check_photo)
        
        if not photo_check.data:
            raise NotFoundError(
                message="Photo not found",
                resource_type="photo",
                resource_id=photo_id
            )
        
        def _insert_comment() -> Any:
            return self.supabase.table("photo_comments").insert({
                "user_id": user_id,
                "photo_id": photo_id,
                "content": content
            }).execute()

        res = await asyncio.to_thread(_insert_comment)
        
        comment = res.data[0]
        
        # Enrich with user info for immediate display
        def _fetch_user_info() -> Any:
            return self.supabase.table("users").select("name, picture").eq("id", user_id).single().execute()

        user_res = await asyncio.to_thread(_fetch_user_info)
        user_name = "Someone"
        if user_res.data:
            user_name = user_res.data.get("name")
            comment["user_name"] = user_name
            comment["user_picture"] = user_res.data.get("picture")
            
        # Trigger Notification
        try:
            owner_id = photo_check.data.get("user_id")
            if owner_id and owner_id != user_id:
                await self.notification_service.create_notification(
                    user_id=owner_id,
                    actor_id=user_id,
                    type=NotificationType.COMMENT.value,
                    title="New Comment",
                    message=f"{user_name} commented: {content[:50]}{'...' if len(content) > 50 else ''}",
                    resource_id=photo_id,
                    resource_type="photo"
                )
        except Exception as e:
            logger.warning(f"Failed to send comment notification: {e}")
            
        from typing import cast
        return cast(dict[str, Any], comment)

    async def get_comments(self, photo_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get comments for a photo."""
        def _fetch_comments() -> Any:
            return self.supabase.table("photo_comments").select(
                "*, users(name, picture)"
            ).eq("photo_id", photo_id).order("created_at", desc=False).limit(limit).execute()

        res = await asyncio.to_thread(_fetch_comments)
        
        comments = []
        for item in res.data:
            user_data = item.get("users", {}) or {}
            # Flatten structure
            item["user_name"] = user_data.get("name")
            item["user_picture"] = user_data.get("picture")
            del item["users"]
            comments.append(item)
            
        return comments

    async def delete_comment(self, user_id: str, comment_id: str) -> bool:
        """Delete a comment."""
        def _delete() -> Any:
            return self.supabase.table("photo_comments").delete().eq("id", comment_id).eq("user_id", user_id).execute()

        res = await asyncio.to_thread(_delete)
        return len(res.data) > 0
