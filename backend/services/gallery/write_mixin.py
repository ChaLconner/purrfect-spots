import contextlib
from typing import TYPE_CHECKING, Any, cast

import structlog
from sqlalchemy import String, bindparam, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

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
                try:
                    result = await self.db.execute(
                        text(
                            "SELECT id, user_id, image_url FROM cat_photos WHERE id = :id AND deleted_at IS NULL LIMIT 1"
                        ),
                        {"id": photo_id},
                    )
                    row = result.fetchone()
                    if row:
                        photo = dict(row._mapping)
                except Exception as e:
                    logger.warning("SQL ownership check failed, falling back to Supabase client: %s", e)

            if not photo:
                from typing import cast

                res = await (
                    self.supabase.table("cat_photos")
                    .select("id,user_id,image_url")
                    .eq("id", photo_id)
                    .is_("deleted_at", "null")
                    .limit(1)
                    .execute()
                )
                data_list = cast(list[dict[str, Any]], res.data or [])
                photo = data_list[0] if data_list else None
            return photo if (photo and photo.get("user_id") == user_id) else None
        except Exception as e:
            logger.error(f"Ownership check failed: {e}")
            return None

    async def save_photo(self, photo_data: dict[str, Any]) -> dict[str, Any]:
        """Save photo metadata to database."""
        if self.db:
            try:
                query = text(
                    "INSERT INTO cat_photos ("
                    "id, image_url, latitude, longitude, description, location_name, "
                    "user_id, status, tags, metadata, uploaded_at, location_blurred"
                    ") VALUES ("
                    ":id, :image_url, :latitude, :longitude, :description, :location_name, "
                    ":user_id, :status, :tags, :metadata, :uploaded_at, :location_blurred"
                    ") RETURNING id, image_url, latitude, longitude, description, location_name, "
                    "uploaded_at, tags, likes_count, comments_count, user_id"
                ).bindparams(
                    bindparam("tags", type_=ARRAY(String())),
                    bindparam("metadata", type_=JSONB),
                )
                params = {
                    "id": photo_data.get("id"),
                    "image_url": photo_data.get("image_url"),
                    "latitude": photo_data.get("latitude"),
                    "longitude": photo_data.get("longitude"),
                    "description": photo_data.get("description"),
                    "location_name": photo_data.get("location_name"),
                    "user_id": photo_data.get("user_id"),
                    "status": photo_data.get("status"),
                    "tags": list(cast(list[str], photo_data.get("tags") or [])),
                    "metadata": cast(dict[str, Any] | None, photo_data.get("metadata")),
                    "uploaded_at": photo_data.get("uploaded_at"),
                    "location_blurred": bool(photo_data.get("location_blurred", False)),
                }
                result = await self.db.execute(query, params)
                row = result.fetchone()
                if not row:
                    from utils.exceptions import ExternalServiceError

                    raise ExternalServiceError("Database insert returned no data", service="PostgreSQL")
                await self.db.commit()
                return dict(row._mapping)
            except Exception as e:
                with contextlib.suppress(Exception):
                    await self.db.rollback()
                logger.warning(f"SQLAlchemy save photo failed, falling back to Supabase client: {e}")
                # Don't raise here, allow falling through to the Supabase client code below
        try:
            admin = await self.get_supabase_admin()
            if not admin:
                from utils.exceptions import ExternalServiceError

                raise ExternalServiceError(
                    "Supabase admin credentials missing (required for write operations)", service="Supabase"
                )

            res = await admin.table("cat_photos").insert(photo_data).execute()
            if not res.data:
                from utils.exceptions import ExternalServiceError

                raise ExternalServiceError("Database insert returned no data", service="Supabase")
            data_list = cast(list[dict[str, Any]], res.data)
            return data_list[0]
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
                        admin = await self.get_supabase_admin()
                        if admin:
                            await admin.table("cat_photos").delete().eq("id", photo_id).execute()
            else:
                admin = await self.get_supabase_admin()
                if admin:
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
