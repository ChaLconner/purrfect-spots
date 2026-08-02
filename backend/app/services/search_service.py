from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.logger import logger
from app.utils.db_security import escape_like_pattern, sanitize_search_input

_fulltext_available_cache: bool | None = None


class SearchService:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        # Explicit column selection to avoid over-fetching
        self.PHOTO_COLUMNS = "id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, likes_count, comments_count, user_id"
        self.SQL_PHOTO_SELECT = f"SELECT {self.PHOTO_COLUMNS} FROM cat_photos"  # noqa: S608
        self.APPROVED_STATUS = "approved"

    @property
    async def fulltext_available(self) -> bool:
        """Check if full-text search column exists in database (lazy)."""
        global _fulltext_available_cache
        if _fulltext_available_cache is None:
            _fulltext_available_cache = await self._check_fulltext_support()
        return _fulltext_available_cache

    async def _check_fulltext_support(self) -> bool:
        """Check if full-text search column exists in database."""
        try:
            if self.db:
                query = text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name = 'cat_photos' AND column_name = 'search_vector'"
                )
                result = await self.db.execute(query)
                return result.fetchone() is not None

            await self.supabase.table("cat_photos").select("search_vector").limit(1).execute()
            return True
        except Exception:
            return False

    async def search_photos(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
        use_fulltext: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search photos with optional text query and/or tags filter.
        """
        try:
            if query and use_fulltext and await self.fulltext_available:
                try:
                    return await self._fulltext_search(query, tags, limit, offset)
                except Exception as e:
                    logger.info("Full-text search failed, falling back to ILIKE: %s", e)

            sanitized_query = sanitize_search_input(query) if query else None
            return await self._ilike_search(sanitized_query, tags, limit, offset)

        except Exception as e:
            logger.error("Search failed: %s", e)
            raise

    @staticmethod
    def _clean_tags(tags: list[str]) -> list[str]:
        """Normalize tag strings."""
        return [tag.strip().lower().replace("#", "") for tag in tags]

    async def _fulltext_search(
        self, query: str, tags: list[str] | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Perform full-text search with SQL fallback to Supabase client."""
        # Try SQL approach first
        if self.db:
            try:
                params: dict[str, Any] = {"query": query, "approved_status": self.APPROVED_STATUS}
                tag_clause = ""
                if tags:
                    params["tags"] = self._clean_tags(tags)
                    tag_clause = "AND tags @> :tags "

                sql_str = (
                    f"{self.SQL_PHOTO_SELECT} "
                    "WHERE deleted_at IS NULL AND status = :approved_status "
                    "AND search_vector @@ websearch_to_tsquery('english', :query) "
                    f"{tag_clause}"
                    "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                )
                return await self._execute_sql_query_dict_list(text(sql_str), params, limit, offset)
            except Exception as e:
                logger.warning("SQL full-text search failed, falling back to Supabase client: %s", e)

        # Fallback to Supabase client
        try:
            db_query = (
                self.supabase.table("cat_photos")
                .select(self.PHOTO_COLUMNS)
                .is_("deleted_at", "null")
                .eq("status", self.APPROVED_STATUS)
                .text_search("search_vector", query, options={"type": "websearch"})
                .order("uploaded_at", desc=True)  # type: ignore
                .range(offset, offset + limit - 1)
            )
            if tags:
                db_query = db_query.contains("tags", self._clean_tags(tags))

            resp = await db_query.execute()
            return cast(list[dict[str, Any]], resp.data or [])
        except Exception as e:
            logger.error("Supabase full-text search failed as well: %s", e)
            raise

    async def _ilike_search(
        self, query: str | None = None, tags: list[str] | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fallback search using ILIKE with SQL fallback to Supabase client."""
        # Try SQL approach first
        if self.db:
            try:
                params: dict[str, Any] = {"approved_status": self.APPROVED_STATUS}
                where_clauses = ["deleted_at IS NULL", "status = :approved_status"]

                if query:
                    params["query"] = f"%{escape_like_pattern(query)}%"
                    where_clauses.append("(location_name ILIKE :query OR description ILIKE :query)")

                if tags:
                    params["tags"] = self._clean_tags(tags)
                    where_clauses.append("tags @> :tags")

                sql_str = (
                    f"{self.SQL_PHOTO_SELECT} WHERE "
                    + " AND ".join(where_clauses)
                    + " ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                )
                return await self._execute_sql_query_dict_list(text(sql_str), params, limit, offset)
            except Exception as e:
                logger.warning("SQL ILIKE search failed, falling back to Supabase client: %s", e)

        # Fallback to Supabase client
        try:
            db_query = (
                self.supabase.table("cat_photos")
                .select(self.PHOTO_COLUMNS)
                .is_("deleted_at", "null")
                .eq("status", self.APPROVED_STATUS)
            )

            if query:
                safe_query = escape_like_pattern(query)
                # Use or_ for multi-column search
                db_query = db_query.or_(f"location_name.ilike.%{safe_query}%,description.ilike.%{safe_query}%")

            if tags:
                db_query = db_query.contains("tags", self._clean_tags(tags))

            resp = await db_query.order("uploaded_at", desc=True).range(offset, offset + limit - 1).execute()
            return cast(list[dict[str, Any]], resp.data or [])
        except Exception as e:
            logger.error("Supabase ILIKE search failed as well: %s", e)
            raise

    def _filter_by_tags(self, photos: list[dict[str, Any]], tags: list[str]) -> list[dict[str, Any]]:
        """Client-side tag filtering fallback."""
        clean_tags = set(self._clean_tags(tags))
        filtered = []
        for photo in photos:
            photo_tags = {t.lower() for t in (photo.get("tags") or [])}
            if clean_tags.issubset(photo_tags):
                filtered.append(photo)
        return filtered

    async def _execute_sql_query_dict_list(
        self, sql_query: Any, params: dict[str, Any], limit: int, offset: int
    ) -> list[dict[str, Any]]:
        """Helper to set limit/offset and fetch mapping dicts from SQL query."""
        db = self.db
        if db is None:
            raise RuntimeError("SQL search requires a database session")
        params["limit"] = min(max(limit, 1), 100)
        params["offset"] = max(offset, 0)
        result = await db.execute(sql_query, params)
        return [dict(row._mapping) for row in result.fetchall()]
