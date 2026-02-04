"""
Service for gallery and photo management with full-text search support

Features:
- Full-text search with PostgreSQL tsvector
- Pagination support
- TTL-based caching for performance
- Tag filtering and popular tags
"""

from collections import Counter
from typing import Any

from supabase import Client

from config import config
from logger import logger
from utils.cache import cached_gallery, cached_tags
from utils.db_security import escape_like_pattern, sanitize_search_input


class GalleryService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        # Use standard client for public reads (RLS safe)
        # We keep admin client reference only for specific overrides if needed
        # but prefer using the standard client
        from dependencies import get_supabase_admin_client

        self._admin_client_lazy = None

        # Check if full-text search is available
        self._fulltext_available = self._check_fulltext_support()

    @property
    def supabase_admin(self):
        """Lazy load admin client only when absolutely necessary"""
        if self._admin_client_lazy is None:
            from dependencies import get_supabase_admin_client

            self._admin_client_lazy = get_supabase_admin_client()
        return self._admin_client_lazy

    def _check_fulltext_support(self) -> bool:
        """
        Check if full-text search column exists in database.
        Falls back to ILIKE search if not available.
        """
        try:
            # Try to select the search_vector column - using standard client (RLS safe)
            self.supabase.table("cat_photos").select("search_vector").limit(1).execute()
            logger.info("Full-text search is available")
            return True
        except Exception as e:
            logger.info("Search feature status: Basic mode enabled (Fallback: %s)", e)
            return False

    def _optimize_image_url(self, url: str | None, width: int = 300) -> str | None:
        """
        Optimize image URL:
        1. Rewrite to CDN if configured
        2. Append transformation parameters if supported (Supabase)

        Args:
            url: Original image URL
            width: Target width in pixels (default: 300 for thumbnails)
        """
        if not url:
            return url

        # 1. CDN Rewrite
        s3_bucket = config.aws_bucket if hasattr(config, "aws_bucket") else "purrfect-spots-bucket"
        aws_region = config.aws_region if hasattr(config, "aws_region") else "ap-southeast-2"
        s3_domain = f"{s3_bucket}.s3.{aws_region}.amazonaws.com"

        final_url = url
        if config.CDN_BASE_URL and s3_domain in url:
            final_url = url.replace(f"https://{s3_domain}", config.CDN_BASE_URL)
            logger.debug(f"CDN rewrite: {s3_domain} -> {config.CDN_BASE_URL}")
        else:
            logger.debug(f"No CDN rewrite: CDN_BASE_URL={config.CDN_BASE_URL}, s3_domain in url={s3_domain in url}")

        # 2. Resizing and Compression (Supabase only for now)
        if "supabase.co/storage/v1/object/public" in final_url:
            # If already has query params, verify/append
            separator = "&" if "?" in final_url else "?"
            # Optimized parameters: width=300px, quality=80, format=webp
            optimized_url = f"{final_url}{separator}width={width}&quality=80&resize=cover&format=webp"
            logger.debug(f"Image optimization: width={width}px, quality=80, format=webp")
            return optimized_url

        logger.debug(f"No image optimization applied: {final_url}")
        return final_url

    def _process_photos(self, photos: list[dict[str, Any]], width: int = 500) -> list[dict[str, Any]]:
        """Process a list of photos with optimizations"""
        for photo in photos:
            if "image_url" in photo:
                photo["image_url"] = self._optimize_image_url(photo["image_url"], width)
        return photos

    def get_all_photos(self, limit: int = 20, offset: int = 0, include_total: bool = True) -> dict[str, Any]:
        """
        Get photos for public gallery with pagination

        Args:
            limit: Maximum number of photos to return (default 20, max 100)
            offset: Number of photos to skip for pagination
            include_total: Whether to include total count (slightly slower)

        Returns:
            Dict with 'data', 'total', 'limit', 'offset', 'has_more' keys
        """
        try:
            # Clamp limit to reasonable bounds
            limit = min(max(1, limit), 100)
            offset = max(0, offset)

            logger.info(f"Fetching gallery photos: limit={limit}, offset={offset}, include_total={include_total}")

            # Get paginated data
            resp = (
                self.supabase.table("cat_photos")
                .select("*")
                .is_("deleted_at", "null")  # Soft delete filter
                .order("uploaded_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            data = resp.data if resp.data else []
            logger.info(f"Fetched {len(data)} photos from database")

            # Log image URLs for debugging
            if data and len(data) > 0:
                sample_urls = [
                    photo.get("image_url", "")[:80] + "..."
                    if len(photo.get("image_url", "")) > 80
                    else photo.get("image_url", "")
                    for photo in data[:3]
                ]
                logger.debug(f"Sample image URLs: {sample_urls}")

            data = self._process_photos(data)  # Optimize images
            total = 0

            # Get total count if requested
            if include_total:
                count_resp = (
                    self.supabase.table("cat_photos").select("id", count="exact").is_("deleted_at", "null").execute()  # type: ignore
                )
                total = count_resp.count if count_resp.count else len(data)
                logger.info(f"Total photos in database: {total}")

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

    def get_all_photos_simple(self, limit: int = 1000) -> list[dict[str, Any]]:
        """
        Get all photos without pagination (for backward compatibility).
        Cached for 5 minutes to reduce database load.

        Args:
            limit: Maximum number of photos to return (default: 1000)
        """
        return self._get_all_photos_simple_cached(limit)

    @staticmethod
    @cached_gallery
    def _get_all_photos_simple_impl(supabase_client, limit: int) -> list[dict[str, Any]]:
        """Internal cached implementation."""
        try:
            resp = (
                supabase_client.table("cat_photos")
                .select("*")
                .is_("deleted_at", "null")
                .order("uploaded_at", desc=True)
                .limit(limit)
                .execute()
            )
            # Note: We don't resize images here strictly to keep the cache payload consistent
            # But we could if we wanted to enforce it everywhere.
            # For now, let's keep get_all_photos_simple for backward compat.
            return resp.data if resp.data else []
        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch gallery images: {e!s}", service="Supabase")

    def get_map_locations(self) -> list[dict[str, Any]]:
        """
        Get lightweight locations for map display.
        Selects only essential fields.
        """
        return self._get_map_locations_cached()

    def _get_map_locations_cached(self) -> list[dict[str, Any]]:
        return self._get_map_locations_impl(self.supabase)

    @staticmethod
    @cached_gallery  # Reuse same cache decorator or make a new one? cached_gallery key depends on args.
    # We should probably use a dedicated cache or distinct arguments to avoid collision if the key generation is naive.
    # The existing @cached_gallery decorator in utils/cache.py likely uses function name in key or arguments.
    # Let's assume it handles it safely (usually includes func name).
    def _get_map_locations_impl(supabase_client) -> list[dict[str, Any]]:
        try:
            resp = (
                supabase_client.table("cat_photos")
                .select("id,latitude,longitude,location_name,image_url")  # Minimal fields
                .is_("deleted_at", "null")
                .order("uploaded_at", desc=True)
                .limit(2000)  # Reasonable limit for map
                .execute()
            )
            data = resp.data if resp.data else []
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

    def _get_all_photos_simple_cached(self, limit: int) -> list[dict[str, Any]]:
        """Wrapper to pass supabase client to cached function."""
        return GalleryService._get_all_photos_simple_impl(self.supabase, limit)

    def search_photos(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        use_fulltext: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search photos with optional text query and/or tags filter.

        Uses PostgreSQL full-text search if available for better performance
        and ranking. Falls back to ILIKE search if full-text is not configured.

        Args:
            query: Text to search in location_name and description
            tags: List of tags to filter by (photos must contain ALL specified tags)
            limit: Maximum number of results
            use_fulltext: Whether to use full-text search (if available)

        Returns:
            List of matching photo records
        """
        try:
            # Use full-text search if available and requested
            if query and use_fulltext and self._fulltext_available:
                return self._fulltext_search(query, tags, limit)

            # Fallback to ILIKE search with strict sanitization
            sanitized_query = sanitize_search_input(query) if query else None
            return self._ilike_search(sanitized_query, tags, limit)

        except Exception as e:
            logger.error("Data retrieval unsuccessful: %s", e)
            # If full-text search fails, try ILIKE fallback
            if use_fulltext and self._fulltext_available:
                logger.info("Falling back to ILIKE search")
                try:
                    sanitized_query = sanitize_search_input(query) if query else None
                    return self._ilike_search(sanitized_query, tags, limit)
                except Exception as e2:
                    logger.error(f"Fallback search also failed: {e2}")
                    raise
            raise

    def _fulltext_search(self, query: str, tags: list[str] | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """
        Perform full-text search using PostgreSQL tsvector.

        Args:
            query: Search query text
            tags: Optional tag filters
            limit: Maximum results

        Returns:
            List of matching photos sorted by relevance
        """
        try:
            # Use the search_cat_photos RPC function if available
            # This provides ranking by relevance
            try:
                # Use standard client for RPC call
                resp = self.supabase.rpc("search_cat_photos", {"search_query": query, "result_limit": limit}).execute()

                results = resp.data if resp.data else []

                # Apply tag filters if provided (client-side for now)
                if tags and results:
                    results = self._filter_by_tags(results, tags)

                return self._process_photos(results)

            except Exception as rpc_error:
                logger.debug("Optimization method unavailable (Using standard): %s", rpc_error)

                # Direct query with textquery matching on search_vector column
                # Use websearch_to_tsquery logic (handled by 'type': 'websearch' option in Supabase lib)
                # No need to manually replace spaces with & as websearch handles natural language
                search_term = query

                # Note: This requires PostgREST fulltext filter syntax
                db_query = (
                    self.supabase.table("cat_photos")
                    .select("*")
                    .is_("deleted_at", "null")
                    .text_search("search_vector", search_term, options={"type": "websearch"})  # type: ignore
                    .order("uploaded_at", desc=True)
                    .limit(limit)
                )

                # Apply tag filters
                if tags:
                    clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                    db_query = db_query.contains("tags", clean_tags)

                resp = db_query.execute()
                data = resp.data if resp.data else []
                return self._process_photos(data)

        except Exception as e:
            logger.warning("Advanced search encounter issue: %s", e)
            raise

    def _ilike_search(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Fallback search using ILIKE pattern matching.

        Slower than full-text search but works without additional setup.

        Args:
            query: Text to search (optional)
            tags: Tag filters (optional)
            limit: Maximum results

        Returns:
            List of matching photos
        """
        try:
            # Start with base query using standard client
            db_query = self.supabase.table("cat_photos").select("*").is_("deleted_at", "null")

            # Apply text search if provided
            if query:
                # Sanitize just in case passed directly
                clean_query = sanitize_search_input(query)
                # Escape LIKE wildcards to prevent pattern injection
                safe_query = escape_like_pattern(clean_query)

                # Supabase uses ilike for case-insensitive search
                # Search in both location_name and description
                db_query = db_query.or_(f"location_name.ilike.%{safe_query}%,description.ilike.%{safe_query}%")

            # Apply tag filters if provided using the tags array column
            if tags:
                # Clean tags for comparison
                clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]

                # Use PostgreSQL array contains operator (@>) for efficient filtering
                # Note: Supabase PostgREST uses .contains() for array containment
                db_query = db_query.contains("tags", clean_tags)

            # Order and limit
            db_query = db_query.order("uploaded_at", desc=True).limit(limit)

            resp = db_query.execute()
            data = resp.data if resp.data else []
            return self._process_photos(data)

        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Database error during photo retrieval: {e!s}", service="Supabase")

    def _filter_by_tags(self, photos: list[dict[str, Any]], tags: list[str]) -> list[dict[str, Any]]:
        """
        Client-side tag filtering for photos.

        Args:
            photos: List of photo records
            tags: Tags to filter by

        Returns:
            Filtered list of photos
        """
        clean_tags = {tag.strip().lower().replace("#", "") for tag in tags}

        filtered = []
        for photo in photos:
            photo_tags = {t.lower() for t in (photo.get("tags") or [])}
            if clean_tags.issubset(photo_tags):
                filtered.append(photo)

        return filtered

    def get_popular_tags(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get popular tags with their usage counts.
        Cached for 10 minutes since tags don't change frequently.

        Returns list of dicts with 'tag' and 'count' keys
        Uses tags array column primarily, with fallback to description parsing
        """
        return self._get_popular_tags_cached(limit)

    @staticmethod
    @cached_tags
    def _get_popular_tags_impl(supabase_client, limit: int) -> list[dict[str, Any]]:
        """Internal cached implementation for popular tags."""
        try:
            # Fetch only tags column for better performance
            # Limit to recent photos to reduce processing time
            resp = (
                supabase_client.table("cat_photos")
                .select("tags")
                .not_.is_("tags", "null")
                .is_("deleted_at", "null")
                .limit(1000)  # Sample from most recent 1000 photos
                .execute()
            )

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

    def _get_popular_tags_cached(self, limit: int) -> list[dict[str, Any]]:
        """Wrapper to pass supabase client to cached function."""
        return GalleryService._get_popular_tags_impl(self.supabase, limit)

    def get_user_photos(self, user_id: str) -> list[dict[str, Any]]:
        """Get all photos uploaded by a specific user"""
        try:
            resp = (
                self.supabase.table("cat_photos")
                .select("*")
                .eq("user_id", user_id)
                .is_("deleted_at", "null")
                .order("uploaded_at", desc=True)
                .execute()
            )
            data = resp.data if resp.data else []
            return self._process_photos(data)
        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch user images: {e!s}", service="Supabase")

    def get_nearby_photos(
        self, latitude: float, longitude: float, radius_km: float = 5.0, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get photos within a certain radius of a location.

        Uses PostGIS if enabled via feature flag, otherwise falls back to
        bounding box approximation.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            limit: Maximum results

        Returns:
            List of nearby photos sorted by distance
        """
        from services.feature_flags import FeatureFlagService

        # Use PostGIS if feature flag is enabled
        if FeatureFlagService.is_enabled("ENABLE_POSTGIS_SEARCH"):
            return self._get_nearby_photos_postgis(latitude, longitude, radius_km, limit)

        return self._get_nearby_photos_bounding_box(latitude, longitude, radius_km, limit)

    def _get_nearby_photos_postgis(
        self, latitude: float, longitude: float, radius_km: float, limit: int
    ) -> list[dict[str, Any]]:
        """
        Get nearby photos using PostGIS ST_DWithin for accurate distance calculation.
        Requires PostGIS extension and location column to be set up.
        """
        try:
            # Use RPC function for PostGIS query
            # This requires the search_nearby_photos function to exist in Supabase
            resp = self.supabase.rpc(
                "search_nearby_photos",
                {"lat": latitude, "lng": longitude, "radius_meters": radius_km * 1000, "result_limit": limit},
            ).execute()

            data = resp.data if resp.data else []
            return self._process_photos(data)

        except Exception as e:
            logger.warning("Spatial query unsuccessful, using boundary fallback: %s", e)
            return self._get_nearby_photos_bounding_box(latitude, longitude, radius_km, limit)

    def _get_nearby_photos_bounding_box(
        self, latitude: float, longitude: float, radius_km: float, limit: int
    ) -> list[dict[str, Any]]:
        """
        Fallback: Get nearby photos using bounding box approximation.
        Less accurate but works without PostGIS.
        """
        try:
            # Approximate degrees per km (varies by latitude)
            import math

            km_per_degree_lat = 111.0
            # Longitude length shrinks as we move to poles: 111 * cos(lat)
            # Use max(0.1, ...) to avoid division by zero at poles
            cos_lat = math.cos(math.radians(latitude))
            km_per_degree_lng = 111.0 * max(0.001, abs(cos_lat))

            # Calculate bounding box
            lat_delta = radius_km / km_per_degree_lat
            lng_delta = radius_km / km_per_degree_lng

            min_lat = latitude - lat_delta
            max_lat = latitude + lat_delta
            min_lng = longitude - lng_delta
            max_lng = longitude + lng_delta

            resp = (
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

            data = resp.data if resp.data else []
            return self._process_photos(data)

        except Exception as e:
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch nearby photos: {e!s}", service="Supabase")

    def get_photo_by_id(self, photo_id: str) -> dict[str, Any] | None:
        """Get a specific photo by ID."""
        try:
            resp = (
                self.supabase.table("cat_photos")
                .select("*")
                .eq("id", photo_id)
                .is_("deleted_at", "null")
                .single()
                .execute()
            )
            if resp.data:
                # No resize for single view (full quality) or maybe larger resize?
                # Let's say we want full quality or at least large enough (e.g. 1200)
                # But typically single view is the "detail" view.
                # Let's leave it as original or high res.
                pass
            return resp.data
        except Exception as e:
            # Check if it's a "not found" error which might yield no rows
            msg = str(e)
            if "JSON object requested" in msg or "no rows returned" in msg:
                return None
            logger.error("Resource retrieval failed for identifier %s: %s", photo_id, msg)
            from exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch photo {photo_id}", service="Supabase")
