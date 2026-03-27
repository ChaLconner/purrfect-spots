from typing import Any

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
            return self._process_photos(res.data or [])
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
                        f"SELECT {self.PHOTO_COLUMNS} FROM cat_photos WHERE latitude >= :min_lat AND latitude <= :max_lat AND longitude >= :min_lng AND longitude <= :max_lng AND deleted_at IS NULL ORDER BY uploaded_at DESC LIMIT :limit"
                    ),
                    {"min_lat": min_lat, "max_lat": max_lat, "min_lng": min_lng, "max_lng": max_lng, "limit": limit},
                )
                data = [dict(row._asdict()) for row in result.fetchall()]
            if not data:
                res = await (
                    self.supabase.table("cat_photos")
                    .select(self.PHOTO_COLUMNS)
                    .gte("latitude", min_lat)
                    .lte("latitude", max_lat)
                    .gte("longitude", min_lng)
                    .lte("longitude", max_lng)
                    .is_("deleted_at", "null")
                    .order("uploaded_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                data = res.data or []
            return self._process_photos(data)
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch nearby photos: {e!s}", service="Supabase")
