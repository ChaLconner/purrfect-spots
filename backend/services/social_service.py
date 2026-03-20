from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from logger import logger, sanitize_log_value
from schemas.notification import NotificationType
from services.notification_service import NotificationService
from utils.exceptions import ExternalServiceError, NotFoundError

PHOTO_NOT_FOUND = "Photo not found"


class SocialService:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        self.notification_service = NotificationService(supabase_client)

    async def toggle_like(self, user_id: str, photo_id: str) -> dict[str, Any]:
        """
        Toggle like status for a photo using atomic database function.
        """
        try:
            if self.db:
                # Use SQLAlchemy to call the RPC function
                query = text("SELECT liked, likes_count FROM toggle_photo_like(:p_user_id, :p_photo_id)")
                result = await self.db.execute(query, {"p_user_id": user_id, "p_photo_id": photo_id})
                row = result.fetchone()

                if not row:
                    raise ExternalServiceError("Toggle like returned no data", service="Postgres")

                # Commit the transaction as RPC might have side effects (inserting/deleting likes)
                await self.db.commit()

                liked = row[0]
                likes_count = row[1]
            else:
                from utils.supabase_client import get_async_supabase_admin_client

                # Use admin client to bypass RLS/JWT issues with RPC
                admin_client = await get_async_supabase_admin_client()

                res = await admin_client.rpc(
                    "toggle_photo_like", {"p_user_id": user_id, "p_photo_id": photo_id}
                ).execute()

                data = res.data
                if not data or len(data) == 0:
                    raise ExternalServiceError("Toggle like returned no data", service="Supabase")

                row = data[0]
                liked = row["liked"]
                likes_count = row["likes_count"]

            # Light invalidation (only for the user's view if needed)
            from utils.cache import invalidate_user_cache

            await invalidate_user_cache(user_id)

            return {"liked": liked, "likes_count": likes_count}

        except Exception as e:
            if self.db:
                await self.db.rollback()

            error_msg = str(e)

            # Check for specific error codes from our RPC function
            if "P0002" in error_msg or "Photo not found" in error_msg:
                raise NotFoundError(message=PHOTO_NOT_FOUND, resource_type="photo", resource_id=photo_id)

            logger.error(
                "Toggle like failed for user=%s photo=%s: %s",
                sanitize_log_value(user_id),
                sanitize_log_value(photo_id),
                e,
            )
            raise ExternalServiceError(
                message=f"Failed to toggle like: {error_msg}", service="Database", retryable=True
            )

    async def add_comment(self, user_id: str, photo_id: str, content: str) -> dict[str, Any]:
        """Add a comment to a photo."""
        if self.db:
            photo_owner_id, comment = await self._add_comment_sql(user_id, photo_id, content)
        else:
            photo_owner_id, comment = await self._add_comment_supabase(user_id, photo_id, content)

        # Trigger Notification
        await self._send_comment_notification(user_id, photo_id, photo_owner_id, content, comment)

        return comment

    async def _add_comment_sql(self, user_id: str, photo_id: str, content: str) -> tuple[str, dict[str, Any]]:
        """Internal helper for SQL-based comment addition"""
        if not self.db:
            raise ExternalServiceError("Database session not available", service="Postgres")

        try:
            # 1. Validate photo exists
            photo_query = text("SELECT user_id FROM cat_photos WHERE id = :p_id AND deleted_at IS NULL LIMIT 1")
            photo_res = await self.db.execute(photo_query, {"p_id": photo_id})
            photo_row = photo_res.fetchone()

            if not photo_row:
                raise NotFoundError(message=PHOTO_NOT_FOUND, resource_type="photo", resource_id=photo_id)

            photo_owner_id = photo_row[0]

            # 2. Insert comment
            comment_query = text(
                "INSERT INTO photo_comments (user_id, photo_id, content) VALUES (:u_id, :p_id, :content) RETURNING *"
            )
            comment_res = await self.db.execute(comment_query, {"u_id": user_id, "p_id": photo_id, "content": content})
            comment_row = comment_res.fetchone()

            if not comment_row:
                raise ExternalServiceError("Failed to create comment", service="Postgres")

            comment = dict(comment_row._mapping)

            # 3. Enrichment
            user_query = text("SELECT name, picture FROM users WHERE id = :u_id LIMIT 1")
            user_res = await self.db.execute(user_query, {"u_id": user_id})
            user_row = user_res.fetchone()

            if user_row:
                comment["user_name"] = user_row[0]
                comment["user_picture"] = user_row[1]

            await self.db.commit()
            return photo_owner_id, comment
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, NotFoundError):
                raise
            logger.error(f"SQLAlchemy add_comment failed: {e}")
            raise ExternalServiceError(f"Failed to add comment via SQLAlchemy: {e}", service="Database")

    async def _add_comment_supabase(self, user_id: str, photo_id: str, content: str) -> tuple[str, dict[str, Any]]:
        """Internal helper for Supabase-based comment addition"""
        from utils.supabase_client import get_async_supabase_admin_client

        # Validate photo exists first
        supa_res = (
            await self.supabase.table("cat_photos")
            .select("id, user_id")
            .eq("id", photo_id)
            .is_("deleted_at", "null")
            .limit(1)
            .execute()
        )

        if not supa_res.data:
            raise NotFoundError(message=PHOTO_NOT_FOUND, resource_type="photo", resource_id=photo_id)

        photo_owner_id = supa_res.data[0].get("user_id")

        # Insert comment using service role client
        admin_client = await get_async_supabase_admin_client()
        supa_res = (
            await admin_client.table("photo_comments")
            .insert({"user_id": user_id, "photo_id": photo_id, "content": content})
            .execute()
        )

        if not supa_res.data:
            raise ExternalServiceError("Failed to create comment", service="Supabase")

        comment = supa_res.data[0]

        # Enrichment
        user_res = await self.supabase.table("users").select("name, picture").eq("id", user_id).limit(1).execute()

        if user_res.data:
            comment["user_name"] = user_res.data[0].get("name")
            comment["user_picture"] = user_res.data[0].get("picture")

        return photo_owner_id, comment

    async def _send_comment_notification(
        self, user_id: str, photo_id: str, photo_owner_id: str | None, content: str, comment: dict[str, Any]
    ) -> dict[str, Any]:
        """Internal helper to end comment notification"""
        try:
            if photo_owner_id and photo_owner_id != user_id:
                user_name = comment.get("user_name", "Someone")
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

        return comment

    async def get_comments(self, photo_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get comments for a photo."""
        if self.db:
            try:
                query = text(
                    "SELECT c.*, u.name as user_name, u.picture as user_picture "
                    "FROM photo_comments c "
                    "LEFT JOIN users u ON c.user_id = u.id "
                    "WHERE c.photo_id = :p_id "
                    "ORDER BY c.created_at ASC "
                    "LIMIT :limit"
                )
                result = await self.db.execute(query, {"p_id": photo_id, "limit": limit})

                comments = []
                for row in result:
                    item = dict(row._mapping)
                    comments.append(item)
                return comments
            except Exception as e:
                logger.error(f"SQLAlchemy get_comments failed: {e}")
                # Fallback to Supabase

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
                item.pop("users", None)
            comments.append(item)

        return comments

    async def delete_comment(self, user_id: str, comment_id: str) -> bool:
        """Delete a comment."""
        if self.db:
            try:
                query = text("DELETE FROM photo_comments WHERE id = :c_id AND user_id = :u_id RETURNING id")
                result = await self.db.execute(query, {"c_id": comment_id, "u_id": user_id})
                row = result.fetchone()
                await self.db.commit()
                return row is not None
            except Exception as e:
                await self.db.rollback()
                logger.error(f"SQLAlchemy delete_comment failed: {e}")
                # Fallback to Supabase

        from utils.supabase_client import get_async_supabase_admin_client

        # Delete using admin client to ensure success or check ownership
        admin_client = await get_async_supabase_admin_client()
        res = await admin_client.table("photo_comments").delete().eq("id", comment_id).eq("user_id", user_id).execute()

        return len(res.data) > 0

    async def update_comment(self, user_id: str, comment_id: str, content: str) -> dict[str, Any] | None:
        """Update a comment's content."""
        if self.db:
            try:
                query = text(
                    "UPDATE photo_comments "
                    "SET content = :content, updated_at = NOW() "
                    "WHERE id = :c_id AND user_id = :u_id "
                    "RETURNING *"
                )
                result = await self.db.execute(query, {"content": content, "c_id": comment_id, "u_id": user_id})
                row = result.fetchone()

                if not row:
                    await self.db.commit()
                    return None

                item = dict(row._mapping)

                # Enrichment
                user_query = text("SELECT name, picture FROM users WHERE id = :u_id LIMIT 1")
                user_res = await self.db.execute(user_query, {"u_id": user_id})
                user_row = user_res.fetchone()

                if user_row:
                    item["user_name"] = user_row[0]
                    item["user_picture"] = user_row[1]

                await self.db.commit()
                return item
            except Exception as e:
                await self.db.rollback()
                logger.error(f"SQLAlchemy update_comment failed: {e}")
                # Fallback to Supabase

        from utils.supabase_client import get_async_supabase_admin_client

        # Update using admin client to ensure bypass of RLS issues if necessary
        admin_client = await get_async_supabase_admin_client()
        res = (
            await admin_client.table("photo_comments")
            .update({"content": content, "updated_at": "now()"})
            .select("*, users(name, picture)")  # type: ignore[attr-defined]
            .eq("id", comment_id)
            .eq("user_id", user_id)
            .execute()
        )

        if not res.data:
            return None

        item = res.data[0]
        user_data = item.get("users", {}) or {}

        # Flatten structure for consistency with CommentResponse
        item["user_name"] = user_data.get("name")
        item["user_picture"] = user_data.get("picture")
        item.pop("users", None)

        return cast(dict[str, Any] | None, item)
