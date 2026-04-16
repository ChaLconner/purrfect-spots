from collections import Counter
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import text

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
        db_tags = await self._get_popular_tags_db(limit)
        if db_tags is not None:
            return db_tags
        return cast(list[dict[str, Any]], await GallerySearchMixin._get_popular_tags_impl(self.supabase, limit))

    async def _get_popular_tags_db(self, limit: int) -> list[dict[str, Any]] | None:
        if not self.db:
            return None
        try:
            query = text(
                "SELECT tag, count(*) "
                "FROM ("
                "SELECT unnest(tags) as tag FROM cat_photos "
                "WHERE deleted_at IS NULL AND status = :approved_status"
                ") as t "
                "GROUP BY tag "
                "ORDER BY count(*) DESC "
                "LIMIT :limit"
            )
            result = await self.db.execute(query, {"approved_status": self.APPROVED_STATUS, "limit": limit})
            return cast(list[dict[str, Any]], [{"tag": row[0], "count": row[1]} for row in result.fetchall()])
        except Exception as e:
            logger.warning("SQLAlchemy popular tags failed: %s", e)
            return None

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
            data = []
            if self.db:
                try:
                    sql = self.PHOTO_SELECT_SQL + " WHERE user_id = :u_id AND deleted_at IS NULL"
                    params: dict[str, Any] = {"u_id": user_id}
                    if not include_unapproved:
                        sql += " AND status = :approved_status"
                        params["approved_status"] = self.APPROVED_STATUS
                    sql += " ORDER BY uploaded_at DESC"
                    result = await self.db.execute(text(sql), params)
                    data = [dict(row._mapping) for row in result.fetchall()]
                except Exception as e:
                    logger.warning("SQL get_user_photos failed, falling back to Supabase client: %s", e)

            if not data:
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
