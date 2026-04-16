from collections import Counter
from typing import TYPE_CHECKING, Any, cast

import structlog  # type: ignore[import-untyped, unused-ignore]
from services.gallery.base_mixin import GalleryBaseMixin
from utils.cache import cache, cached_tags
from utils.supabase_client import AClient

logger = structlog.get_logger(__name__)


if TYPE_CHECKING:
    from services.search_service import SearchService


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
    ) -> list[dict[str, Any]]:
        try:
            results = await self.search_service.search_photos(query, tags, limit, offset, use_fulltext)
            results = self._process_photos(results)
            if user_id and results:
                results = await self.enrich_with_user_data(results, user_id)
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Database error during photo retrieval: {e!s}", service="Supabase")

    async def get_popular_tags(self, limit: int = 20) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], await GallerySearchMixin._get_popular_tags_impl(self.supabase, limit))

    @staticmethod
    @cached_tags
    async def _get_popular_tags_impl(supabase_client: AClient, limit: int) -> list[dict[str, Any]]:
        try:
            res = await (
                supabase_client.table("cat_photos")
                .select("tags")
                .not_.is_("tags", "null")
                .is_("deleted_at", "null")
                .eq("status", GallerySearchMixin.APPROVED_STATUS)
                .limit(limit)
                .execute()
            )
            data = cast(list[dict[str, Any]], res.data or [])
            tag_counter: Counter = Counter()
            for row in data:
                for tag in row.get("tags") or []:
                    if tag:
                        tag_counter[tag.lower()] += 1
            return [{"tag": tag, "count": count} for tag, count in tag_counter.most_common(limit)]
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to get popular tags: {e!s}", service="Supabase")

    @cache(expire=300, key_prefix="user_photos", skip_args=1)
    async def get_user_photos(self, user_id: str, include_unapproved: bool = False) -> list[dict[str, Any]]:
        try:
            data: list[dict[str, Any]]
            res = (
                await self._apply_visibility_filter(
                    self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS),
                    include_unapproved=include_unapproved,
                )
                .eq("user_id", user_id)
                .order("uploaded_at", desc=True)
                .execute()
            )
            data = cast(list[dict[str, Any]], res.data or [])
            return self._process_photos(data)
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch user images: {e!s}", service="Supabase")
