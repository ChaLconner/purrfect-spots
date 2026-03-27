from collections import Counter
from typing import Any, cast

import structlog
from sqlalchemy import text

from services.gallery.base_mixin import GalleryBaseMixin
from utils.cache import cache, cached_tags
from utils.supabase_client import AClient

logger = structlog.get_logger(__name__)


class GallerySearchMixin(GalleryBaseMixin):
    """SEARCH and TAG operations for GalleryService"""

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
                "SELECT tag, count(*) FROM (SELECT unnest(tags) as tag FROM cat_photos WHERE deleted_at IS NULL) as t GROUP BY tag ORDER BY count(*) DESC LIMIT :limit"
            )
            result = await self.db.execute(query, {"limit": limit})
            return [{"tag": row[0], "count": row[1]} for row in result.fetchall()]
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
                .limit(1000)
                .execute()
            )
            data = res.data or []
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
    async def get_user_photos(self, user_id: str) -> list[dict[str, Any]]:
        try:
            data = []
            if self.db:
                result = await self.db.execute(
                    text(
                        f"SELECT {self.PHOTO_COLUMNS} FROM cat_photos WHERE user_id = :u_id AND deleted_at IS NULL ORDER BY uploaded_at DESC"
                    ),
                    {"u_id": user_id},
                )
                data = [dict(row._asdict()) for row in result.fetchall()]
            if not data:
                res = await (
                    self.supabase.table("cat_photos")
                    .select(self.PHOTO_COLUMNS)
                    .eq("user_id", user_id)
                    .is_("deleted_at", "null")
                    .order("uploaded_at", desc=True)
                    .execute()
                )
                data = res.data or []
            return self._process_photos(data)
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch user images: {e!s}", service="Supabase")
