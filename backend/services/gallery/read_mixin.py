from typing import Any, cast

from postgrest.types import CountMethod

import structlog  # type: ignore[import-untyped, unused-ignore]
from services.gallery.base_mixin import GalleryBaseMixin
from utils.cache import cached_gallery, cached_user_likes

logger = structlog.get_logger(__name__)


class GalleryReadMixin(GalleryBaseMixin):
    """READ operations for GalleryService"""

    # _process_photos moved to GalleryBaseMixin

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

    async def get_all_photos_simple(self) -> list[dict[str, Any]]:
        """Simple get all photos wrapper returning only the data list."""
        res = await self.get_all_photos(include_total=False)
        return cast(list[dict[str, Any]], res["data"])

    async def _fetch_photos(self, limit: int, offset: int, user_id: str | None) -> list[dict[str, Any]]:
        """Fetch photos with hydrated user details where possible."""
        return await self._fetch_photos_supabase(limit, offset, user_id)

    async def _fetch_photos_supabase(self, limit: int, offset: int, user_id: str | None) -> list[dict[str, Any]]:
        query = self._apply_visibility_filter(self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS))
        res = await query.order("uploaded_at", desc=True).range(offset, offset + limit - 1).execute()
        return cast(list[dict[str, Any]], res.data or [])

    async def _fetch_total_count(self, data: list[dict[str, Any]]) -> int:
        """Fetch total count of photos with fallback from SQL to Supabase client."""
        try:
            res_count = await self._apply_visibility_filter(
                self.supabase.table("cat_photos").select("id", count=CountMethod.exact)
            ).execute()
            return res_count.count or 0
        except Exception as e:
            logger.error(f"Supabase count fetch failed as well: {e}")
            return len(data)

    @cached_gallery
    async def get_map_locations(self) -> list[dict[str, Any]]:
        """Fetch all cat locations using the standard Supabase client path."""
        try:
            res = (
                await self._apply_visibility_filter(
                    self.supabase.table("cat_photos").select(
                        "id,latitude,longitude,location_name,image_url,user_id,uploaded_at"
                    )
                )
                .order("uploaded_at", desc=True)
                .limit(2000)
                .execute()
            )
            data = cast(list[dict[str, Any]], res.data or [])

            # Final safety check: ensure all items are dicts and catch None image_urls
            sanitized_data = []
            for photo in data:
                photo_dict = dict(photo) if not isinstance(photo, dict) else photo
                img_url = photo_dict.get("image_url")

                if img_url and "supabase.co/storage/v1/object/public" in img_url:
                    sep = "&" if "?" in img_url else "?"
                    photo_dict["image_url"] = f"{img_url}{sep}width=100&resize=cover&format=webp"
                sanitized_data.append(photo_dict)

            return sanitized_data
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch map locations: {e!s}", service="Supabase")

    async def get_photo_by_id(self, photo_id: str, include_unapproved: bool = False) -> dict[str, Any] | None:
        """Fetch a single photo by ID using the standard Supabase client path."""
        try:
            res = (
                await self._apply_visibility_filter(
                    self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS),
                    include_unapproved=include_unapproved,
                )
                .eq("id", photo_id)
                .limit(1)
                .execute()
            )
            data = cast(list[dict[str, Any]], res.data or [])
            if data:
                return self._process_photos(data, width=1200)[0]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch photo {photo_id}: {e}")
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch photo {photo_id}", service="Supabase")

    async def enrich_with_user_data(
        self, photos: list[dict[str, Any]], user_id: str | None = None
    ) -> list[dict[str, Any]]:
        if not photos or not user_id:
            return photos
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
            admin_client = await self.get_supabase_admin()
            if not admin_client:
                logger.warning("No admin client available; skipping user likes fetch")
                return set()

            res = await admin_client.table("photo_likes").select("photo_id").eq("user_id", user_id).execute()
            data_list = cast(list[dict[str, Any]], res.data or [])
            return {cast(str, item["photo_id"]) for item in data_list}
        except Exception as e:
            logger.error(f"Failed to fetch user liked photo IDs: {e!s}")
            return set()
