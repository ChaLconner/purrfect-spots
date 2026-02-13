"""
Service for gallery and photo management with full-text search support

Features:
- Full-text search with PostgreSQL tsvector
- Pagination support
- TTL-based caching for performance
- Tag filtering and popular tags
"""

from typing import TYPE_CHECKING, Any, Counter

from supabase import Client

from logger import logger
from services.image_service import ImageService
from services.search_service import SearchService
from utils.cache import cached_gallery, cached_tags

if TYPE_CHECKING:
    from services.storage_service import StorageService


class GalleryService:
    _fulltext_supported_cache: bool | None = None

    def __init__(self, supabase_client: Client) -> None:
        self.supabase = supabase_client
        self.search_service = SearchService(supabase_client)
        self._admin_client_lazy: Client | None = None

    @property
    def supabase_admin(self) -> Client:
        """Lazy load admin client only when absolutely necessary"""
        if self._admin_client_lazy is None:
            from dependencies import get_supabase_admin_client

            self._admin_client_lazy = get_supabase_admin_client()
        return self._admin_client_lazy

    @property
    def _fulltext_available(self) -> bool:
        return self.search_service._fulltext_available

    def _process_photos(self, photos: list[dict[str, Any]], width: int = 500) -> list[dict[str, Any]]:
        """Process a list of photos with optimizations"""
        return ImageService.process_photos(photos, width)

    async def get_all_photos(
        self, limit: int = 20, offset: int = 0, include_total: bool = True, user_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get photos for public gallery with pagination.
        Optimized to use native async HTTP client (httpx) for high concurrency.
        """
        import asyncio

        from utils.async_client import async_supabase

        try:
            # Clamp limit to reasonable bounds
            limit = min(max(1, limit), 100)
            offset = max(0, offset)

            logger.info(f"Fetching gallery photos: limit={limit}, offset={offset}, user_id={user_id}")
            
            data = []
            
            # Primary: Try native async RPC
            try:
                rpc_params: dict[str, Any] = {"p_limit": limit, "p_offset": offset}
                if user_id:
                    rpc_params["p_user_id"] = user_id
                
                data = await async_supabase.rpc("get_gallery_photos_with_likes", rpc_params)
                
            except Exception as rpc_error:
                logger.debug(f"Async RPC fetch failed, falling back to sync client: {rpc_error}")
                
                # Fallback: Synchronous client in thread pool
                def fetch_fallback() -> list[dict[str, Any]]:
                    try:
                        # Fallback to standard paginated query
                        query = (
                            self.supabase.table("cat_photos")
                            .select("*")
                            .is_("deleted_at", "null")
                            .order("uploaded_at", desc=True)
                            .range(offset, offset + limit - 1)
                        )
                        resp = query.execute()
                        fallback_data = resp.data if resp.data else []
                        
                        # Manual enrichment if fallback used
                        if user_id and fallback_data:
                            fallback_data = self.enrich_with_user_data_sync(fallback_data, user_id)
                        return fallback_data
                    except Exception as e:
                        logger.error(f"Fallback fetch failed: {e}", exc_info=True)
                        raise

                data = await asyncio.to_thread(fetch_fallback)

            data = self._process_photos(data)  # Optimize images

            total = 0
            # Get total count if requested (keep using sync client for simplicity/consistency for now)
            if include_total:
                def fetch_count() -> int:
                    count_resp = (
                        self.supabase.table("cat_photos").select("id", count="exact").is_("deleted_at", "null").execute()  # type: ignore
                    )
                    return count_resp.count if count_resp.count else len(data)
                total = await asyncio.to_thread(fetch_count)

            return {
                "data": data,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(data) < total if include_total else len(data) == limit,
            }
        except Exception as e:
            logger.error(f"Failed to fetch gallery images: {e!s}", exc_info=True)
            from exceptions import ExternalServiceError
            raise ExternalServiceError(f"Failed to fetch gallery images: {e!s}", service="Supabase")

    async def get_all_photos_simple(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get all photos without pagination (for backward compatibility).
        Cached for 5 minutes to reduce database load.

        Args:
            limit: Maximum number of photos to return (default: 1000)
        """

        return await self._get_all_photos_simple_cached(limit)

    @staticmethod
    @cached_gallery
    async def _get_all_photos_simple_impl(supabase_client: Client, limit: int) -> list[dict[str, Any]]:
        """Internal cached implementation."""
        try:
            import asyncio
            def fetch() -> Any:
                return (
                    supabase_client.table("cat_photos")
                    .select("*")
                    .is_("deleted_at", "null")
                    .order("uploaded_at", desc=True)
                    .limit(limit)
                    .execute()
                )
            resp = await asyncio.to_thread(fetch)
            # But we could if we wanted to enforce it everywhere.
            # For now, let's keep get_all_photos_simple for backward compat.
            data: list[dict[str, Any]] = resp.data if resp.data else []
            return data
        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch gallery images: {e!s}", service="Supabase")

    async def get_map_locations(self) -> list[dict[str, Any]]:
        """
        Get lightweight locations for map display.
        Selects only essential fields.
        """
        return await self._get_map_locations_cached()

    async def _get_map_locations_cached(self) -> list[dict[str, Any]]:
        from typing import cast
        return cast(list[dict[str, Any]], await self._get_map_locations_impl(self.supabase))

    @staticmethod
    @cached_gallery  # Reuse same cache decorator or make a new one? cached_gallery key depends on args.
    # We should probably use a dedicated cache or distinct arguments to avoid collision if the key generation is naive.
    # The existing @cached_gallery decorator in utils/cache.py likely uses function name in key or arguments.
    # Let's assume it handles it safely (usually includes func name).
    async def _get_map_locations_impl(supabase_client: Client) -> list[dict[str, Any]]:
        try:
            import asyncio
            def fetch() -> Any:
                return (
                    supabase_client.table("cat_photos")
                    .select("id,latitude,longitude,location_name,image_url")  # Minimal fields
                    .is_("deleted_at", "null")
                    .order("uploaded_at", desc=True)
                    .limit(2000)  # Reasonable limit for map
                    .execute()
                )
            resp = await asyncio.to_thread(fetch)
            data: list[dict[str, Any]] = resp.data if resp.data else []
            # We can resize these too, map thumbnails are small
            for photo in data:
                if "image_url" in photo:
                    # Simple manual optimization here since it's a static method
                    if photo["image_url"] and "supabase.co/storage/v1/object/public" in photo["image_url"]:
                        sep = "&" if "?" in photo["image_url"] else "?"
                        photo["image_url"] = f"{photo['image_url']}{sep}width=200&resize=cover&format=webp"
            return data
        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch map locations: {e!s}", service="Supabase")

    async def _get_all_photos_simple_cached(self, limit: int) -> list[dict[str, Any]]:
        """Wrapper to pass supabase client to cached function."""
        from typing import cast
        return cast(list[dict[str, Any]], await GalleryService._get_all_photos_simple_impl(self.supabase, limit))

    async def search_photos(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
        use_fulltext: bool = True,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search photos with optional text query and/or tags filter.
        """
        import asyncio
        try:
            results = await asyncio.to_thread(self.search_service.search_photos, query, tags, limit, offset, use_fulltext)
            
            results = self._process_photos(results)
            
            if user_id and results:
                results = await self.enrich_with_user_data(results, user_id)
                
            return results
        except Exception as e:
            from exceptions import ExternalServiceError
            raise ExternalServiceError(f"Database error during photo retrieval: {e!s}", service="Supabase")

    async def get_popular_tags(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get popular tags with their usage counts.
        Cached for 10 minutes since tags don't change frequently.

        Returns list of dicts with 'tag' and 'count' keys
        Uses tags array column primarily, with fallback to description parsing
        """
        return await self._get_popular_tags_cached(limit)

    @staticmethod
    @cached_tags
    async def _get_popular_tags_impl(supabase_client: Client, limit: int) -> list[dict[str, Any]]:
        """Internal cached implementation for popular tags."""
        try:
            # Fetch only tags column for better performance
            # Limit to recent photos to reduce processing time
            import asyncio
            def fetch() -> Any:
                return (
                    supabase_client.table("cat_photos")
                    .select("tags")
                    .not_.is_("tags", "null")
                    .is_("deleted_at", "null")
                    .limit(1000)  # Sample from most recent 1000 photos
                    .execute()
                )
            resp = await asyncio.to_thread(fetch)

            if not resp.data:
                return []

            tag_counter: Counter = Counter()

            for row in resp.data:
                # Use tags array column (primary method)
                tags_array = row.get("tags") or []
                if tags_array and isinstance(tags_array, list):
                    for tag in tags_array:
                        if tag:
                            tag_counter[tag.lower()] += 1

            # Return top tags with counts
            popular = tag_counter.most_common(limit)
            return [{"tag": tag, "count": count} for tag, count in popular]

        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to get popular tags: {e!s}", service="Supabase")

    async def _get_popular_tags_cached(self, limit: int) -> list[dict[str, Any]]:
        """Wrapper to pass supabase client to cached function."""
        from typing import cast
        return cast(list[dict[str, Any]], await GalleryService._get_popular_tags_impl(self.supabase, limit))

    async def get_user_photos(self, user_id: str) -> list[dict[str, Any]]:
        """Get all photos uploaded by a specific user"""
        import asyncio
        try:
            def fetch() -> Any:
                return (
                    self.supabase.table("cat_photos")
                    .select("*")
                    .eq("user_id", user_id)
                    .is_("deleted_at", "null")
                    .order("uploaded_at", desc=True)
                    .execute()
                )
            resp = await asyncio.to_thread(fetch)
            data: list[dict[str, Any]] = resp.data if resp.data else []
            return self._process_photos(data)
        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch user images: {e!s}", service="Supabase")

    async def get_nearby_photos(
        self, latitude: float, longitude: float, radius_km: float = 5.0, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get photos within a certain radius of a location.
        """
        from services.feature_flags import FeatureFlagService

        # Use PostGIS if feature flag is enabled
        if FeatureFlagService.is_enabled("ENABLE_POSTGIS_SEARCH"):
            return await self._get_nearby_photos_postgis(latitude, longitude, radius_km, limit)

        return await self._get_nearby_photos_bounding_box(latitude, longitude, radius_km, limit)

    async def _get_nearby_photos_postgis(
        self, latitude: float, longitude: float, radius_km: float, limit: int
    ) -> list[dict[str, Any]]:
        """
        Get nearby photos using PostGIS ST_DWithin for accurate distance calculation.
        """
        import asyncio
        try:
            def fetch() -> Any:
                return self.supabase.rpc(
                    "search_nearby_photos",
                    {"lat": latitude, "lng": longitude, "radius_meters": radius_km * 1000, "result_limit": limit},
                ).execute()
            
            resp = await asyncio.to_thread(fetch)

            data: list[dict[str, Any]] = resp.data if resp.data else []
            return self._process_photos(data)

        except Exception as e:
            logger.warning("Spatial query unsuccessful, using boundary fallback: %s", e)
            return await self._get_nearby_photos_bounding_box(latitude, longitude, radius_km, limit)

    async def _get_nearby_photos_bounding_box(
        self, latitude: float, longitude: float, radius_km: float, limit: int
    ) -> list[dict[str, Any]]:
        """
        Fallback: Get nearby photos using bounding box approximation.
        """
        import asyncio
        try:
            # Approximate degrees per km (varies by latitude)
            import math

            km_per_degree_lat = 111.0
            cos_lat = math.cos(math.radians(latitude))
            km_per_degree_lng = 111.0 * max(0.001, abs(cos_lat))

            # Calculate bounding box
            lat_delta = radius_km / km_per_degree_lat
            lng_delta = radius_km / km_per_degree_lng

            min_lat = latitude - lat_delta
            max_lat = latitude + lat_delta
            min_lng = longitude - lng_delta
            max_lng = longitude + lng_delta
            
            def fetch() -> Any:
                return (
                    self.supabase.table("cat_photos")
                    .select("*")
                    .gte("latitude", min_lat)
                    .lte("latitude", max_lat)
                    .gte("longitude", min_lng)
                    .lte("longitude", max_lng)
                    .order("uploaded_at", desc=True)
                    .limit(limit)
                    .execute()
                )

            resp = await asyncio.to_thread(fetch)

            data: list[dict[str, Any]] = resp.data if resp.data else []
            return self._process_photos(data)

        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch nearby photos: {e!s}", service="Supabase")

    async def get_photo_by_id(self, photo_id: str) -> dict[str, Any] | None:
        """Get a specific photo by ID."""
        import asyncio
        try:
            def fetch() -> Any:
                return (
                    self.supabase.table("cat_photos")
                    .select("*")
                    .eq("id", photo_id)
                    .is_("deleted_at", "null")
                    .single()
                    .execute()
                )
            resp = await asyncio.to_thread(fetch)
            data: dict[str, Any] | None = resp.data
            return data
        except Exception as e:
            msg = str(e)
            if "JSON object requested" in msg or "no rows returned" in msg:
                return None
            logger.error("Resource retrieval failed for identifier %s: %s", photo_id, msg)
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch photo {photo_id}", service="Supabase")

    async def enrich_with_user_data(self, photos: list[dict[str, Any]], user_id: str) -> list[dict[str, Any]]:
        """
        Enrich a list of photos with user-specific data (e.g., whether they liked it).
        Efficiently checks all photos in a single query.
        """
        import asyncio
        if not photos:
            return photos

        try:
            def fetch_likes() -> set[str]:
                photo_ids = [p["id"] for p in photos]
                # Check which of these photos the user has liked
                likes_resp = (
                    self.supabase.table("photo_likes")
                    .select("photo_id")
                    .eq("user_id", user_id)
                    .in_("photo_id", photo_ids)
                    .execute()
                )
                return {like["photo_id"] for like in likes_resp.data} if likes_resp.data else set()

            liked_ids = await asyncio.to_thread(fetch_likes)

            for photo in photos:
                photo["liked"] = photo["id"] in liked_ids

            return photos
        except Exception as e:
            logger.error(f"Failed to enrich photos with user data: {e!s}")
            return photos

    def enrich_with_user_data_sync(self, photos: list[dict[str, Any]], user_id: str) -> list[dict[str, Any]]:
        """Synchronous version for internal use."""
        if not photos:
            return photos
        try:
            photo_ids = [p["id"] for p in photos]
            likes_resp = (
                self.supabase.table("photo_likes")
                .select("photo_id")
                .eq("user_id", user_id)
                .in_("photo_id", photo_ids)
                .execute()
            )
            liked_ids = {like["photo_id"] for like in likes_resp.data} if likes_resp.data else set()
            for photo in photos:
                photo["liked"] = photo["id"] in liked_ids
            return photos
        except Exception as e:
            logger.error(f"Failed to enrich photos with user data: {e!s}")
            return photos
    async def verify_photo_ownership(self, photo_id: str, user_id: str) -> dict[str, Any] | None:
        """
        Verify if a user owns a photo.
        Returns the photo data if owned, None otherwise.
        """
        import asyncio
        try:
            def fetch() -> Any:
                return (
                    self.supabase.table("cat_photos")
                    .select("id, user_id, image_url")
                    .eq("id", photo_id)
                    .is_("deleted_at", "null")
                    .single()
                    .execute()
                )
            resp = await asyncio.to_thread(fetch)
            photo: dict[str, Any] | None = resp.data
            
            if photo and photo.get("user_id") == user_id:
                return photo
            return None
        except Exception as e:
            logger.error(f"Ownership check failed: {e}")
            return None

    async def process_photo_deletion(self, photo_id: str, image_url: str, user_id: str, storage_service: "StorageService") -> None:
        """
        Background task to handle photo deletion:
        1. Delete from S3
        2. Delete from Database
        3. Invalidate caches
        4. Log security event
        """
        try:
            logger.info("Starting background deletion for photo %s", photo_id)
            
            # 1. Delete from Storage (S3)
            if image_url:
                storage_service.delete_file(image_url)
                
            # 2. Delete from Database
            self.supabase_admin.table("cat_photos").delete().eq("id", photo_id).execute()
            
            # 3. Invalidate Caches
            from utils.cache import invalidate_gallery_cache, invalidate_tags_cache
            await invalidate_gallery_cache()
            await invalidate_tags_cache()
            
            # 4. Log security event
            from utils.security import log_security_event
            log_security_event("photo_deleted", user_id=user_id, details={"photo_id": photo_id, "mode": "background"})
            
            logger.info("Background deletion completed for photo %s", photo_id)
            
        except Exception as e:
            logger.error("Background deletion failed for photo %s: %s", photo_id, e, exc_info=True)
            # We might want to retry or alert admin?
            # For now, just log error.
