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
        sort_field: str | None = None,
        sort_desc: bool = True,
    ) -> dict[str, Any]:
        """Get photos for public gallery with pagination."""
        try:
            limit = min(max(1, limit), 100)
            offset = max(0, offset)
            logger.info(f"Fetching gallery photos: limit={limit}, offset={offset}, user_id={user_id}")

            # PERF: Fetch data and count in a single query to eliminate N+1
            data, total = await self._fetch_photos(
                limit,
                offset,
                user_id,
                include_count=include_total,
                sort_field=sort_field,
                sort_desc=sort_desc,
            )
            if data and user_id:
                data = await self.enrich_with_user_data(data, user_id)
            data = self._process_photos(data)

            if total is None:
                total = 0

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

    async def _fetch_photos(
        self,
        limit: int,
        offset: int,
        user_id: str | None,
        include_count: bool = False,
        sort_field: str | None = None,
        sort_desc: bool = True,
    ) -> tuple[list[dict[str, Any]], int | None]:
        """Fetch photos with hydrated user details where possible."""
        return await self._fetch_photos_supabase(limit, offset, user_id, include_count, sort_field, sort_desc)

    async def _fetch_photos_supabase(
        self,
        limit: int,
        offset: int,
        user_id: str | None,
        include_count: bool = False,
        sort_field: str | None = None,
        sort_desc: bool = True,
    ) -> tuple[list[dict[str, Any]], int | None]:
        # PERF: Include count in same query to avoid separate roundtrip
        count_method = CountMethod.exact if include_count else None
        query = self._apply_visibility_filter(
            self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS, count=count_method)
        )
        # PERF: Sort at DB level instead of Python
        order_field = sort_field or "uploaded_at"

        try:
            res = await query.order(order_field, desc=sort_desc).range(offset, offset + limit - 1).execute()
            data = cast(list[dict[str, Any]], res.data or [])
            total = res.count if include_count and res.count is not None else None
            return data, total
        except Exception as e:
            # BUGFIX: Handle Supabase error 416 'JSON could not be generated' which occurs
            # on some rows when count='exact' is used.
            if "JSON could not be generated" in str(e) and include_count:
                logger.debug("Supabase count='exact' failed, retrying without count: %s", e)
                # Retry without count
                query_no_count = self._apply_visibility_filter(
                    self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS)
                )
                res = (
                    await query_no_count.order(order_field, desc=sort_desc).range(offset, offset + limit - 1).execute()
                )
                data = cast(list[dict[str, Any]], res.data or [])
                # Fetch count separately as fallback
                total = await self._fetch_total_count_fallback(data)
                return data, total

            # Re-raise if it's not the specific count error or if we weren't asking for count
            raise

    async def _fetch_total_count_fallback(self, data: list[dict[str, Any]]) -> int:
        """Fallback: fetch total count separately using a HEAD-style count-only query."""
        try:
            res_count = await self._apply_visibility_filter(
                self.supabase.table("cat_photos").select(count=CountMethod.exact)
            ).execute()
            return res_count.count or 0
        except Exception as e:
            logger.error(f"Supabase count fetch failed as well: {e}")
            return len(data)

    @cached_gallery
    async def get_map_locations(self, limit: int = 500) -> list[dict[str, Any]]:
        """Fetch a bounded legacy marker list using the standard Supabase client path."""
        try:
            limit = min(max(1, limit), 500)
            res = (
                await self._apply_visibility_filter(
                    self.supabase.table("cat_photos").select(
                        "id,latitude,longitude,location_name,image_url,user_id,uploaded_at"
                    )
                )
                .order("uploaded_at", desc=True)
                .limit(limit)
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
