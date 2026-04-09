from typing import Any, cast

import structlog
from sqlalchemy import text

from services.gallery.base_mixin import GalleryBaseMixin
from utils.cache import cache

logger = structlog.get_logger(__name__)


class GalleryLocationMixin(GalleryBaseMixin):
    """LOCATION operations for GalleryService"""

    @cache(expire=300, key_prefix="nearby", skip_args=1)
    async def get_nearby_photos(
        self, latitude: float, longitude: float, radius_km: float = 5.0, limit: int = 50
    ) -> list[dict[str, Any]]:
        from services.feature_flags import FeatureFlagService

        if FeatureFlagService.is_enabled("ENABLE_POSTGIS_SEARCH"):
            return await self._get_nearby_photos_postgis(latitude, longitude, radius_km, limit)
        return await self._get_nearby_photos_bounding_box(latitude, longitude, radius_km, limit)

    async def _get_nearby_photos_postgis(
        self, latitude: float, longitude: float, radius_km: float, limit: int
    ) -> list[dict[str, Any]]:
        try:
            res = await self.supabase.rpc(
                "search_nearby_photos",
                {"lat": latitude, "lng": longitude, "radius_meters": radius_km * 1000, "result_limit": limit},
            ).execute()
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
        try:
            import math

            lat_delta = radius_km / 111.0
            lng_delta = radius_km / (111.0 * max(0.001, abs(math.cos(math.radians(latitude)))))
            min_lat, max_lat = latitude - lat_delta, latitude + lat_delta
            min_lng, max_lng = longitude - lng_delta, longitude + lng_delta

            data = []
            if self.db:
                result = await self.db.execute(
                    text(
                        f"SELECT {self.PHOTO_COLUMNS} FROM cat_photos WHERE latitude >= :min_lat AND latitude <= :max_lat AND longitude >= :min_lng AND longitude <= :max_lng AND {self._sql_visibility_clause()} ORDER BY uploaded_at DESC LIMIT :limit"  # noqa: S608
                    ),
                    {"min_lat": min_lat, "max_lat": max_lat, "min_lng": min_lng, "max_lng": max_lng, "limit": limit},
                )
                data = [dict(row._asdict()) for row in result.fetchall()]
            if not data:
                res = await (
                    self._apply_visibility_filter(self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS))
                    .gte("latitude", min_lat)
                    .lte("latitude", max_lat)
                    .gte("longitude", min_lng)
                    .lte("longitude", max_lng)
                    .order("uploaded_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                data = cast(list[dict[str, Any]], res.data or [])
            return self._process_photos(data)
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch nearby photos: {e!s}", service="Supabase")
