from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import text

from services.gallery.base_mixin import GalleryBaseMixin

if TYPE_CHECKING:
    from services.storage_service import StorageService

logger = structlog.get_logger(__name__)


class GalleryWriteMixin(GalleryBaseMixin):
    """WRITE operations for GalleryService"""

    async def verify_photo_ownership(self, photo_id: str, user_id: str) -> dict[str, Any] | None:
        """Verify if a user owns a photo."""
        try:
            photo = None
            if self.db:
                result = await self.db.execute(
                    text("SELECT id, user_id, image_url FROM cat_photos WHERE id = :id AND deleted_at IS NULL LIMIT 1"),
                    {"id": photo_id},
                )
                row = result.fetchone()
                if row:
                    photo = dict(row._asdict())
            if not photo:
                res = await (
                    self.supabase.table("cat_photos")
                    .select("id,user_id,image_url")
                    .eq("id", photo_id)
                    .is_("deleted_at", "null")
                    .limit(1)
                    .execute()
                )
                photo = (res.data or [None])[0]
            return photo if (photo and photo.get("user_id") == user_id) else None
        except Exception as e:
            logger.error(f"Ownership check failed: {e}")
            return None

    async def save_photo(self, photo_data: dict[str, Any]) -> dict[str, Any]:
        """Save photo metadata to database."""
        if self.db:
            try:
                columns = ", ".join(photo_data.keys())
                placeholders = ", ".join([f":{k}" for k in photo_data])
                query = text(f"INSERT INTO cat_photos ({columns}) VALUES ({placeholders}) RETURNING {self.PHOTO_COLUMNS}")  # noqa: S608
                result = await self.db.execute(query, photo_data)
                row = result.fetchone()
                if not row:
                    from utils.exceptions import ExternalServiceError

                    raise ExternalServiceError("Database insert returned no data", service="PostgreSQL")
                await self.db.commit()
                return dict(row._asdict())
            except Exception as e:
                await self.db.rollback()
                logger.error(f"SQLAlchemy save photo failed: {e}")
                raise e
        try:
            admin = await self.supabase_admin
            res = await admin.table("cat_photos").insert(photo_data).select(self.PHOTO_COLUMNS).execute()
            if not res.data:
                from utils.exceptions import ExternalServiceError

                raise ExternalServiceError("Database insert returned no data", service="Supabase")
            return res.data[0]
        except Exception as e:
            logger.error(f"Failed to save photo to database: {e}")
            raise e

    async def process_photo_deletion(
        self, photo_id: str, image_url: str, user_id: str, storage_service: "StorageService"
    ) -> None:
        """Background task to handle photo deletion."""
        try:
            logger.info("Starting background deletion for photo %s", photo_id)
            try:
                await storage_service.delete_file(image_url)
            except Exception as e:
                logger.error(f"Error deleting file from storage: {e}")

            from database import AsyncSessionLocal

            if AsyncSessionLocal is not None:
                async with AsyncSessionLocal() as db:
                    try:
                        await db.execute(text("DELETE FROM cat_photos WHERE id = :id"), {"id": photo_id})
                        await db.commit()
                    except Exception as db_err:
                        await db.rollback()
                        logger.warning(f"SQLAlchemy deletion failed: {db_err}")
                        admin = await self.supabase_admin
                        await admin.table("cat_photos").delete().eq("id", photo_id).execute()
            else:
                admin = await self.supabase_admin
                await admin.table("cat_photos").delete().eq("id", photo_id).execute()

            from utils.cache import invalidate_gallery_cache, invalidate_tags_cache, invalidate_user_cache

            await invalidate_gallery_cache()
            await invalidate_tags_cache()
            await invalidate_user_cache(user_id)

            from utils.security import log_security_event

            log_security_event("photo_deleted", user_id=user_id, details={"photo_id": photo_id})
            logger.info("Background deletion completed for photo %s", photo_id)
        except Exception as e:
            logger.error("Background deletion failed for %s: %s", photo_id, e)
