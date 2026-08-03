import math
from typing import Any, cast

from sqlalchemy import bindparam, column, desc, select, table

from app.compat import structlog
from app.services.gallery.base_mixin import GalleryBaseMixin
from app.utils.cache import cache
from app.utils.retry import retry_on_network_error

logger = structlog.get_logger(__name__)


class GalleryLocationMixin(GalleryBaseMixin):
    """LOCATION operations for GalleryService"""

    @cache(expire=300, key_prefix="nearby", skip_args=1)
    async def get_nearby_photos(
        self, latitude: float, longitude: float, radius_km: float = 5.0, limit: int = 50
    ) -> list[dict[str, Any]]:
        from app.services.feature_flags import FeatureFlagService

        if FeatureFlagService.is_enabled("ENABLE_POSTGIS_SEARCH"):
            return await self._get_nearby_photos_postgis(latitude, longitude, radius_km, limit)
        return await self._get_nearby_photos_bounding_box(latitude, longitude, radius_km, limit)

    @cache(expire=300, key_prefix="viewport", skip_args=1)
    async def get_viewport_photos(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch exactly the requested viewport, using PostGIS when available."""
        from app.services.feature_flags import FeatureFlagService

        min_lat, max_lat = min(south, north), max(south, north)
        min_lng, max_lng = min(west, east), max(west, east)
        safe_limit = max(1, min(int(limit), 500))

        if FeatureFlagService.is_enabled("ENABLE_POSTGIS_SEARCH"):
            try:
                res = await retry_on_network_error(
                    self.supabase.rpc(
                        "search_viewport_photos",
                        {
                            "north": max_lat,
                            "south": min_lat,
                            "east": max_lng,
                            "west": min_lng,
                            "result_limit": safe_limit,
                        },
                    ).execute
                )
                data = cast(list[dict[str, Any]], res.data or [])
                if any(not isinstance(photo, dict) or "status" not in photo for photo in data):
                    logger.warning("PostGIS viewport search missing moderation status; using bbox fallback")
                    return await self._get_photos_in_bounding_box(min_lat, max_lat, min_lng, max_lng, safe_limit)
                approved = [photo for photo in data if photo.get("status") == self.APPROVED_STATUS]
                return self._process_photos(approved[:safe_limit])
            except Exception as e:
                logger.warning("Spatial viewport query failed, fallback: %s", e)

        return await self._get_photos_in_bounding_box(min_lat, max_lat, min_lng, max_lng, safe_limit)

    async def _get_nearby_photos_postgis(
        self, latitude: float, longitude: float, radius_km: float, limit: int
    ) -> list[dict[str, Any]]:
        try:
            res = await retry_on_network_error(
                self.supabase.rpc(
                    "search_nearby_photos",
                    {"lat": latitude, "lng": longitude, "radius_meters": radius_km * 1000, "result_limit": limit},
                ).execute
            )
            data = cast(list[dict[str, Any]], res.data or [])
            if any(not isinstance(photo, dict) or "status" not in photo for photo in data):
                logger.warning("PostGIS nearby search missing moderation status; falling back to safe public query")
                return await self._get_nearby_photos_bounding_box(latitude, longitude, radius_km, limit)
            approved = [photo for photo in data if photo.get("status") == self.APPROVED_STATUS]
            return self._process_photos(approved[:limit])
        except Exception as e:
            logger.warning("Spatial query failed, fallback: %s", e)
            return await self._get_nearby_photos_bounding_box(latitude, longitude, radius_km, limit)

    async def _get_nearby_photos_bounding_box(
        self, latitude: float, longitude: float, radius_km: float, limit: int
    ) -> list[dict[str, Any]]:
        """Fetch nearby photos in a radius-derived bounding box."""
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * max(0.001, abs(math.cos(math.radians(latitude)))))
        return await self._get_photos_in_bounding_box(
            latitude - lat_delta,
            latitude + lat_delta,
            longitude - lng_delta,
            longitude + lng_delta,
            limit,
        )

    async def _get_photos_in_bounding_box(
        self,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Fetch photos in a bounding box with SQL fallback to Supabase client."""
        data: list[dict[str, Any]] = []
        sql_succeeded = False
        safe_limit = max(1, min(int(limit), 500))

        # Try SQL approach first
        if self.db:
            try:
                cat_photos = table(
                    "cat_photos",
                    column("id"),
                    column("image_url"),
                    column("latitude"),
                    column("longitude"),
                    column("description"),
                    column("location_name"),
                    column("uploaded_at"),
                    column("tags"),
                    column("likes_count"),
                    column("comments_count"),
                    column("user_id"),
                    column("deleted_at"),
                    column("status"),
                )
                query = (
                    select(
                        cat_photos.c.id,
                        cat_photos.c.image_url,
                        cat_photos.c.latitude,
                        cat_photos.c.longitude,
                        cat_photos.c.description,
                        cat_photos.c.location_name,
                        cat_photos.c.uploaded_at,
                        cat_photos.c.tags,
                        cat_photos.c.likes_count,
                        cat_photos.c.comments_count,
                        cat_photos.c.user_id,
                    )
                    .where(
                        cat_photos.c.latitude >= bindparam("min_lat"),
                        cat_photos.c.latitude <= bindparam("max_lat"),
                        cat_photos.c.longitude >= bindparam("min_lng"),
                        cat_photos.c.longitude <= bindparam("max_lng"),
                        cat_photos.c.deleted_at.is_(None),
                        cat_photos.c.status == bindparam("approved_status"),
                    )
                    .order_by(desc(cat_photos.c.uploaded_at))
                    .limit(safe_limit)
                )
                result = await retry_on_network_error(
                    self.db.execute,
                    query,
                    {
                        "min_lat": min_lat,
                        "max_lat": max_lat,
                        "min_lng": min_lng,
                        "max_lng": max_lng,
                        "approved_status": self.APPROVED_STATUS,
                    },
                )
                data = [dict(row._mapping) for row in result.fetchall()]
                sql_succeeded = True
            except Exception as e:
                logger.warning("SQL nearby search failed, falling back to Supabase client: %s", e)

        # Empty SQL result is valid. Fall back only when SQL path failed, avoiding
        # a duplicate network query for every valid no-result search.
        if not sql_succeeded:
            try:
                res = await retry_on_network_error(
                    self._apply_visibility_filter(self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS))
                    .gte("latitude", min_lat)
                    .lte("latitude", max_lat)
                    .gte("longitude", min_lng)
                    .lte("longitude", max_lng)
                    .order("uploaded_at", desc=True)
                    .limit(safe_limit)
                    .execute
                )
                data = cast(list[dict[str, Any]], res.data or [])
            except Exception as e:
                logger.error("Supabase nearby search failed as well: %s", e)
                # If everything fails, raise the error so the API can return 500
                from app.utils.exceptions import ExternalServiceError

                raise ExternalServiceError(f"Failed to fetch nearby photos: {e!s}", service="Supabase") from e

        return self._process_photos(data)
