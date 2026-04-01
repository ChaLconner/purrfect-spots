from typing import Any, cast

import structlog
from postgrest.types import CountMethod
from sqlalchemy import text

from services.gallery.base_mixin import GalleryBaseMixin
from services.image_service import ImageService
from utils.cache import cached_gallery, cached_gallery_simple, cached_user_likes

logger = structlog.get_logger(__name__)


class GalleryReadMixin(GalleryBaseMixin):
    """READ operations for GalleryService"""

    def _process_photos(self, photos: list[dict[str, Any]], width: int = 500) -> list[dict[str, Any]]:
        """Process a list of photos with optimizations"""
        return ImageService.process_photos(photos, width)

    @cached_gallery
    async def get_all_photos(
        self,
        limit: int = 20,
        offset: int = 0,
        include_total: bool = True,
        user_id: str | None = None,
        jwt_token: str | None = None,
    ) -> dict[str, Any]:
        """Get photos for public gallery with pagination."""
        try:
            limit = min(max(1, limit), 100)
            offset = max(0, offset)
            logger.info(f"Fetching gallery photos: limit={limit}, offset={offset}, user_id={user_id}")

            data = await self._fetch_photos(limit, offset, user_id)
            if data and user_id:
                data = await self.enrich_with_user_data(data, user_id)
            data = self._process_photos(data)

            total = 0
            if include_total:
                total = await self._fetch_total_count(data)

            return {
                "data": data,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(data) < total if include_total else len(data) == limit,
            }
        except Exception as e:
            logger.error(f"Failed to fetch gallery images: {e!s}", exc_info=True)
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch gallery images: {e!s}", service="Supabase")

    async def _fetch_photos(self, limit: int, offset: int, user_id: str | None) -> list[dict[str, Any]]:
        """Fetch photos with hydrated user details where possible."""
        if self.db:
            return await self._fetch_photos_sql(limit, offset, user_id)
        return await self._fetch_photos_supabase(limit, offset, user_id)

    async def _fetch_photos_sql(self, limit: int, offset: int, user_id: str | None) -> list[dict[str, Any]]:
        if not self.db:
            return []
        query = text(
            f"SELECT {self.PHOTO_COLUMNS} FROM cat_photos WHERE {self._sql_visibility_clause()} ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"  # noqa: S608
        )
        result = await self.db.execute(query, {"limit": limit, "offset": offset})
        return [dict(row._asdict()) for row in result.fetchall()]

    async def _fetch_photos_supabase(self, limit: int, offset: int, user_id: str | None) -> list[dict[str, Any]]:
        query = self._apply_visibility_filter(self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS))
        res = await query.order("uploaded_at", desc=True).range(offset, offset + limit - 1).execute()
        return res.data or []

    async def _fetch_total_count(self, data: list[dict[str, Any]]) -> int:
        try:
            if self.db:
                total_res = await self.db.execute(
                    text(f"SELECT count(*) FROM cat_photos WHERE {self._sql_visibility_clause()}")  # noqa: S608
                )
                return total_res.scalar() or 0
            res_count = await self._apply_visibility_filter(
                self.supabase.table("cat_photos").select("id", count=CountMethod.exact)
            ).execute()
            return res_count.count or 0
        except Exception as e:
            logger.error(f"Count fetch failed: {e}")
            return len(data)

    @cached_gallery
    async def get_map_locations(self) -> list[dict[str, Any]]:
        try:
            if self.db:
                result = await self.db.execute(
                    text(
                        f"SELECT id, latitude, longitude, location_name, image_url, user_id FROM cat_photos WHERE {self._sql_visibility_clause()} ORDER BY uploaded_at DESC LIMIT 2000"  # noqa: S608
                    )
                )
                data = [dict(row._asdict()) for row in result.fetchall()]
            else:
                res = (
                    await self._apply_visibility_filter(
                        self.supabase.table("cat_photos").select(
                            "id,latitude,longitude,location_name,image_url,user_id"
                        )
                    )
                    .order("uploaded_at", desc=True)
                    .limit(2000)
                    .execute()
                )
                data = cast(list[dict[str, Any]], res.data or [])

            for photo in data:
                if (
                    "image_url" in photo
                    and photo["image_url"]
                    and "supabase.co/storage/v1/object/public" in photo["image_url"]
                ):
                    sep = "&" if "?" in photo["image_url"] else "?"
                    photo["image_url"] = f"{photo['image_url']}{sep}width=100&resize=cover&format=webp"
            return data
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch map locations: {e!s}", service="Supabase")

    async def get_photo_by_id(self, photo_id: str, include_unapproved: bool = False) -> dict[str, Any] | None:
        try:
            data = None
            if self.db:
                sql = f"SELECT {self.PHOTO_COLUMNS} FROM cat_photos WHERE id = :id AND {self._sql_visibility_clause(include_unapproved)} LIMIT 1"  # noqa: S608
                result = await self.db.execute(text(sql), {"id": photo_id})
                row = result.fetchone()
                if row:
                    data = [dict(row._asdict())]
            if not data:
                res = (
                    await self._apply_visibility_filter(
                        self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS),
                        include_unapproved=include_unapproved,
                    )
                    .eq("id", photo_id)
                    .limit(1)
                    .execute()
                )
                data = res.data or []
            if data:
                return self._process_photos(data, width=1200)[0]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch photo {photo_id}: {e}")
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch photo {photo_id}", service="Supabase")

    async def enrich_with_user_data(self, photos: list[dict[str, Any]], user_id: str) -> list[dict[str, Any]]:
        if not photos:
            return []
        try:
            liked_ids = await self._get_user_liked_photo_ids(user_id)
            for photo in photos:
                photo["liked"] = photo["id"] in liked_ids
            return photos
        except Exception as e:
            logger.error(f"Failed to enrich photos with user data: {e!s}")
            return list(photos)

    @cached_user_likes
    async def _get_user_liked_photo_ids(self, user_id: str) -> set[str]:
        try:
            admin_client = await self.supabase_admin
            res = await admin_client.table("photo_likes").select("photo_id").eq("user_id", user_id).execute()
            return {item["photo_id"] for item in (res.data or [])}
        except Exception as e:
            logger.error(f"Failed to fetch user liked photo IDs: {e!s}")
            return set()

    @cached_gallery_simple
    async def get_all_photos_simple(self, limit: int = 100) -> list[dict[str, Any]]:
        try:
            if self.db:
                db_res = await self.db.execute(
                    text(
                        f"SELECT {self.PHOTO_COLUMNS} FROM cat_photos WHERE {self._sql_visibility_clause()} ORDER BY uploaded_at DESC LIMIT :limit"  # noqa: S608
                    ),
                    {"limit": limit},
                )
                return [dict(row._asdict()) for row in db_res.fetchall()]
            supa_res = (
                await self._apply_visibility_filter(self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS))
                .order("uploaded_at", desc=True)
                .limit(limit)
                .execute()
            )
            return supa_res.data or []
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch gallery images: {e!s}", service="Supabase")
