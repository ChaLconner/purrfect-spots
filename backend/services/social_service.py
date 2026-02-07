from typing import Any, Dict, List

from supabase import Client

from exceptions import NotFoundError, ExternalServiceError
from logger import logger


class SocialService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

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
            # Use atomic RPC function to toggle like
            result = self.supabase.rpc(
                "toggle_photo_like",
                {"p_user_id": user_id, "p_photo_id": photo_id}
            ).execute()
            
            if not result.data or len(result.data) == 0:
                raise ExternalServiceError("Toggle like returned no data", service="Supabase")
            
            row = result.data[0]
            liked = row["liked"]
            likes_count = row["likes_count"]
            
            # Send notification only when liking (not unliking)
            if liked:
                self._send_like_notification(user_id, photo_id)
            
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
            
            logger.error(f"Toggle like failed: {e}")
            raise ExternalServiceError(
                message=f"Failed to toggle like: {error_msg}",
                service="Supabase",
                retryable=True
            )

    def _send_like_notification(self, user_id: str, photo_id: str) -> None:
        """
        Send notification to photo owner about the like.
        
        This is a fire-and-forget operation - failures are logged but don't
        affect the like operation.
        """
        try:
            # Get photo owner and location in one query
            photo_res = (
                self.supabase.table("cat_photos")
                .select("user_id, location_name")
                .eq("id", photo_id)
                .single()
                .execute()
            )
            
            if not photo_res.data:
                return
                
            owner_id = photo_res.data.get("user_id")
            
            # Don't notify if user liked their own photo
            if not owner_id or owner_id == user_id:
                return
            
            # Get actor name
            actor_res = (
                self.supabase.table("users")
                .select("name")
                .eq("id", user_id)
                .single()
                .execute()
            )
            actor_name = actor_res.data.get("name") if actor_res.data else "Someone"
            
            location = photo_res.data.get("location_name") or "your photo"
            
            # Insert notification
            self.supabase.table("notifications").insert({
                "user_id": owner_id,
                "actor_id": user_id,
                "type": "like",
                "title": "New Like",
                "message": f"{actor_name} liked your photo at {location}",
                "resource_id": photo_id,
                "resource_type": "photo"
            }).execute()
            
        except Exception as e:
            # Log but don't fail the like operation
            logger.warning(f"Failed to send like notification: {e}")

    async def add_comment(self, user_id: str, photo_id: str, content: str) -> Dict[str, Any]:
        """Add a comment to a photo."""
        # Validate photo exists first
        photo_check = (
            self.supabase.table("cat_photos")
            .select("id, user_id")
            .eq("id", photo_id)
            .is_("deleted_at", "null")
            .single()
            .execute()
        )
        
        if not photo_check.data:
            raise NotFoundError(
                message="Photo not found",
                resource_type="photo",
                resource_id=photo_id
            )
        
        res = self.supabase.table("photo_comments").insert({
            "user_id": user_id,
            "photo_id": photo_id,
            "content": content
        }).execute()
        
        comment = res.data[0]
        
        # Enrich with user info for immediate display
        user_res = self.supabase.table("users").select("name, picture").eq("id", user_id).single().execute()
        user_name = "Someone"
        if user_res.data:
            user_name = user_res.data.get("name")
            comment["user_name"] = user_name
            comment["user_picture"] = user_res.data.get("picture")
            
        # Trigger Notification
        try:
            owner_id = photo_check.data.get("user_id")
            if owner_id and owner_id != user_id:
                self.supabase.table("notifications").insert({
                    "user_id": owner_id,
                    "actor_id": user_id,
                    "type": "comment",
                    "title": "New Comment",
                    "message": f"{user_name} commented: {content[:50]}{'...' if len(content) > 50 else ''}",
                    "resource_id": photo_id,
                    "resource_type": "photo"
                }).execute()
        except Exception as e:
            logger.warning(f"Failed to send comment notification: {e}")
            
        return comment

    async def get_comments(self, photo_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get comments for a photo."""
        # Join with users to get name/picture
        res = self.supabase.table("photo_comments").select(
            "*, users(name, picture)"
        ).eq("photo_id", photo_id).order("created_at", desc=False).limit(limit).execute()
        
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
        # RLS handles ownership check, but explicit check good for feedback
        res = self.supabase.table("photo_comments").delete().eq("id", comment_id).eq("user_id", user_id).execute()
        return len(res.data) > 0
