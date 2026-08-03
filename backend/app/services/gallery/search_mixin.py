from collections import Counter
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import text

from app.compat import structlog
from app.services.gallery.base_mixin import GalleryBaseMixin
from app.utils.cache import cache, cached_tags
from app.utils.supabase_client import AClient

logger = structlog.get_logger(__name__)


class SearchResultList(list[dict[str, Any]]):
    """List-compatible search result carrying an optional exact total."""

    def __init__(self, values: list[dict[str, Any]], total: int | None = None) -> None:
        super().__init__(values)
        self.total = total


if TYPE_CHECKING:
    from app.services.search_service import SearchService


class GallerySearchMixin(GalleryBaseMixin):
    """SEARCH and TAG operations for GalleryService"""

    # These are provided by the main GalleryService or other mixins
    search_service: "SearchService"

    async def enrich_with_user_data(
        self, photos: list[dict[str, Any]], user_id: str | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @property
    async def _fulltext_available(self) -> bool:
        return await self.search_service.fulltext_available

    async def search_photos(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
        use_fulltext: bool = True,
        user_id: str | None = None,
        include_total: bool = False,
    ) -> list[dict[str, Any]]:
        try:
            results = await self.search_service.search_photos(query, tags, limit, offset, use_fulltext)
            total = await self.search_service.count_photos(query, tags, use_fulltext) if include_total else None
            results = self._process_photos(results)
            if user_id and results:
                results = await self.enrich_with_user_data(results, user_id)
            if include_total:
                if total is None:
                    total = offset + len(results) + (1 if len(results) >= limit else 0)
                return SearchResultList(results, total=total)
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            from app.utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Database error during photo retrieval: {e!s}", service="Supabase")

    @cached_tags
    async def get_popular_tags(self, limit: int = 20) -> list[dict[str, Any]]:
        if self.db:
            result = await self.db.execute(
                text(
                    """
                    SELECT lower(tag) AS tag, count(*)::int AS count
                    FROM cat_photos, unnest(tags) AS tag
                    WHERE deleted_at IS NULL AND status = :approved_status
                    GROUP BY lower(tag)
                    ORDER BY count DESC, tag
                    LIMIT :limit
                    """
                ),
                {"approved_status": self.APPROVED_STATUS, "limit": max(1, min(limit, 100))},
            )
            return [dict(row._mapping) for row in result]

        return await GallerySearchMixin._get_popular_tags_impl(self.supabase, limit)

    @staticmethod
    async def _get_popular_tags_impl(supabase_client: AClient, limit: int) -> list[dict[str, Any]]:
        try:
            res = await supabase_client.rpc("get_popular_tags", {"result_limit": max(1, min(limit, 100))}).execute()
            rows = cast(list[dict[str, Any]], res.data or [])
            if all("tag" in row and "count" in row for row in rows):
                return rows

            # Compatibility fallback for older RPC responses that return photos.
            counts: Counter[str] = Counter()
            for row in rows:
                for tag in row.get("tags") or []:
                    if isinstance(tag, str) and tag.strip():
                        counts[tag.strip().lower().lstrip("#")] += 1
            return [{"tag": tag, "count": count} for tag, count in counts.most_common(max(1, min(limit, 100)))]
        except Exception as e:
            from app.utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to get popular tags: {e!s}", service="Supabase")

    @cache(expire=300, key_prefix="user_photos", skip_args=1)
    async def get_user_photos(
        self, user_id: str, include_unapproved: bool = False, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        try:
            if self.db:
                try:
                    if include_unapproved:
                        query = text(
                            "SELECT id, image_url, latitude, longitude, description, location_name, uploaded_at, "
                            "tags, likes_count, comments_count, user_id "
                            "FROM cat_photos WHERE user_id = :user_id AND deleted_at IS NULL "
                            "AND latitude IS NOT NULL AND longitude IS NOT NULL "
                            "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                        )
                    else:
                        query = text(
                            "SELECT id, image_url, latitude, longitude, description, location_name, uploaded_at, "
                            "tags, likes_count, comments_count, user_id "
                            "FROM cat_photos WHERE user_id = :user_id AND deleted_at IS NULL "
                            "AND latitude IS NOT NULL AND longitude IS NOT NULL "
                            "AND status = :approved_status "
                            "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                        )
                    params: dict[str, Any] = {
                        "user_id": user_id,
                        "limit": min(max(limit, 1), 100),
                        "offset": max(offset, 0),
                    }
                    if not include_unapproved:
                        params["approved_status"] = self.APPROVED_STATUS
                    result = await self.db.execute(query, params)
                    return self._process_photos([dict(row._mapping) for row in result.fetchall()])
                except Exception as e:
                    logger.warning("SQL user photo fetch failed, falling back to Supabase: %s", e)

            data: list[dict[str, Any]]
            res = (
                await self._apply_visibility_filter(
                    self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS),
                    include_unapproved=include_unapproved,
                )
                .eq("user_id", user_id)
                .order("uploaded_at", desc=True)
                .range(max(0, offset), max(0, offset) + min(max(1, limit), 100) - 1)
                .execute()
            )
            data = cast(list[dict[str, Any]], res.data or [])
            return self._process_photos(data)
        except Exception as e:
            from app.utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch user images: {e!s}", service="Supabase")
