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

from logger import logger
from utils.cache import cached_gallery, cached_tags


class GalleryService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        # Use admin client for reading public data (simplified for this app structure)
        from dependencies import get_supabase_admin_client

        self.supabase_admin = get_supabase_admin_client()

        # Check if full-text search is available
        self._fulltext_available = self._check_fulltext_support()

    def _check_fulltext_support(self) -> bool:
        """
        Check if full-text search column exists in database.
        Falls back to ILIKE search if not available.
        """
        try:
            # Try to select the search_vector column - using standard client (RLS safe)
            resp = self.supabase.table("cat_photos").select("search_vector").limit(1).execute()
            logger.info("Full-text search is available")
            return True
        except Exception as e:
            logger.info(f"Full-text search not available, using ILIKE fallback: {e}")
            return False

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

            # Get paginated data
            resp = (
                self.supabase.table("cat_photos")
                .select("*")
                .order("uploaded_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )

            data = resp.data if resp.data else []
            total = 0

            # Get total count if requested
            if include_total:
                count_resp = self.supabase.table("cat_photos").select("id", count="exact").execute()
                total = count_resp.count if count_resp.count else len(data)

            return {
                "data": data,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(data) < total if include_total else len(data) == limit,
            }
        except Exception as e:
            raise Exception(f"Failed to fetch gallery images: {e!s}")

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
                supabase_client.table("cat_photos").select("*").order("uploaded_at", desc=True).limit(limit).execute()
            )
            return resp.data if resp.data else []
        except Exception as e:
            raise Exception(f"Failed to fetch gallery images: {e!s}")

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

            # Fallback to ILIKE search
            return self._ilike_search(query, tags, limit)

        except Exception as e:
            logger.error(f"Search failed: {e}")
            # If full-text search fails, try ILIKE fallback
            if use_fulltext and self._fulltext_available:
                logger.info("Falling back to ILIKE search")
                try:
                    return self._ilike_search(query, tags, limit)
                except Exception as e2:
                    raise Exception(f"Failed to search photos: {e2!s}")
            raise Exception(f"Failed to search photos: {e!s}")

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

                return results

            except Exception as rpc_error:
                logger.debug(f"RPC search not available: {rpc_error}, using direct query")

                # Direct query with textquery matching on search_vector column
                # Convert query to tsquery format
                search_term = query.replace(" ", " & ")  # AND operator between words

                # Note: This requires PostgREST fulltext filter syntax
                db_query = (
                    self.supabase.table("cat_photos")
                    .select("*")
                    .text_search("search_vector", search_term, options={"type": "websearch"})  # type: ignore
                    .order("uploaded_at", desc=True)
                    .limit(limit)
                )

                # Apply tag filters
                if tags:
                    clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                    db_query = db_query.contains("tags", clean_tags)

                resp = db_query.execute()
                return resp.data if resp.data else []

        except Exception as e:
            logger.warning(f"Full-text search error: {e}")
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
            db_query = self.supabase.table("cat_photos").select("*")

            # Apply text search if provided
            if query:
                # Supabase uses ilike for case-insensitive search
                # Search in both location_name and description
                db_query = db_query.or_(f"location_name.ilike.%{query}%,description.ilike.%{query}%")

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
            return resp.data if resp.data else []

        except Exception as e:
            raise Exception(f"Failed to search photos: {e!s}")

    def _filter_by_tags(self, photos: list[dict[str, Any]], tags: list[str]) -> list[dict[str, Any]]:
        """
        Client-side tag filtering for photos.

        Args:
            photos: List of photo records
            tags: Tags to filter by

        Returns:
            Filtered list of photos
        """
        clean_tags = set(tag.strip().lower().replace("#", "") for tag in tags)

        filtered = []
        for photo in photos:
            photo_tags = set(t.lower() for t in (photo.get("tags") or []))
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
            raise Exception(f"Failed to get popular tags: {e!s}")

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
                .order("uploaded_at", desc=True)
                .execute()
            )
            return resp.data if resp.data else []
        except Exception as e:
            raise Exception(f"Failed to fetch user images: {e!s}")

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

            return resp.data if resp.data else []

        except Exception as e:
            logger.warning(f"PostGIS search failed, falling back to bounding box: {e}")
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

            return resp.data if resp.data else []

        except Exception as e:
            raise Exception(f"Failed to fetch nearby photos: {e!s}")

    def get_photo_by_id(self, photo_id: str) -> dict[str, Any] | None:
        """Get a specific photo by ID."""
        try:
            resp = self.supabase.table("cat_photos").select("*").eq("id", photo_id).single().execute()
            return resp.data
        except Exception as e:
            # Check if it's a "not found" error which might yield no rows
            # converting to string to be safe
            msg = str(e)
            if "JSON object requested" in msg or "no rows returned" in msg:
                return None
            logger.error(f"Failed to fetch photo {photo_id}: {msg}")
            raise Exception(f"Failed to fetch photo {photo_id}")
