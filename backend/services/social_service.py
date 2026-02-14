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

    async def toggle_like(self, user_id: str, photo_id: str, jwt_token: str | None = None) -> Dict[str, Any]:
        """
        Toggle like status for a photo using atomic database function.
        """
        from utils.async_client import async_supabase
        try:
            # Use async client for better performance and token propagation
            data = await async_supabase.rpc(
                "toggle_photo_like",
                {"p_user_id": user_id, "p_photo_id": photo_id},
                jwt_token=jwt_token
            )
            
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

    async def add_comment(self, user_id: str, photo_id: str, content: str, jwt_token: str | None = None) -> Dict[str, Any]:
        """Add a comment to a photo."""
        from utils.async_client import async_supabase
        
        # Validate photo exists first
        photo_check = await async_supabase.select(
            table="cat_photos",
            columns="id, user_id",
            filters={"id": f"eq.{photo_id}", "deleted_at": "is.null"},
            jwt_token=jwt_token,
            limit=1
        ) # Returns List[Dict]

        if not photo_check:
             raise NotFoundError(
                message="Photo not found",
                resource_type="photo",
                resource_id=photo_id
            )
        
        photo_owner_id = photo_check[0].get("user_id")

        # Insert comment
        data = await async_supabase.insert(
            table="photo_comments",
            data={
                "user_id": user_id,
                "photo_id": photo_id,
                "content": content
            },
            jwt_token=jwt_token
        )
        
        if not data:
             raise ExternalServiceError("Failed to create comment", service="Supabase")
        
        comment = data[0]
        
        # Enrich with user info for immediate display
        # We can use async_supabase.select to get user info, potentially with token (or without if public)
        # Assuming user profiles are public readable
        user_res = await async_supabase.select(
            table="users",
            columns="name, picture",
            filters={"id": f"eq.{user_id}"},
            jwt_token=jwt_token,
            limit=1
        )

        user_name = "Someone"
        if user_res:
            user_name = user_res[0].get("name")
            comment["user_name"] = user_name
            comment["user_picture"] = user_res[0].get("picture")
            
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
                    resource_type="photo"
                )
        except Exception as e:
            logger.warning(f"Failed to send comment notification: {e}")
            
        from typing import cast
        return cast(dict[str, Any], comment)

    async def get_comments(self, photo_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get comments for a photo."""
        from utils.async_client import async_supabase
        
        # Fetch comments with joined user data
        # AsyncSupabaseClient.select is basic and doesn't support complex joins in `columns` or embedded resources easily via REST unless we use proper syntax
        # "*, users(name, picture)" works in PostgREST if structured correctly.
        # columns="*, users(name, picture)"
        
        data = await async_supabase.select(
            table="photo_comments",
            columns="*, users(name, picture)",
            filters={"photo_id": f"eq.{photo_id}"},
            order="created_at.asc",
            limit=limit
        )

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
        from utils.async_client import async_supabase
        
        # Delete using token for RLS
        data = await async_supabase.delete(
            table="photo_comments",
            filters={"id": f"eq.{comment_id}", "user_id": f"eq.{user_id}"},
            jwt_token=jwt_token
        )
        return len(data) > 0

