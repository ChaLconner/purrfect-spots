from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from logger import logger
from utils.db_security import escape_like_pattern, sanitize_search_input


class SearchService:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        self._fulltext_available: bool | None = None

    @property
    async def fulltext_available(self) -> bool:
        """Check if full-text search column exists in database (lazy)."""
        if self._fulltext_available is None:
            self._fulltext_available = await self._check_fulltext_support()
        return self._fulltext_available

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

    async def _fulltext_search(
        self, query: str, tags: list[str] | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Perform full-text search."""
        try:
            if self.db:
                # Try optimized websearch using SQLAlchemy
                from sqlalchemy import text

                # PostgreSQL websearch_to_tsquery example
                sql = """
                    SELECT * FROM cat_photos
                    WHERE deleted_at IS NULL
                    AND search_vector @@ websearch_to_tsquery('english', :query)
                """
                params: dict[str, Any] = {"query": query}

                if tags:
                    clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                    sql += " AND tags @> :tags"
                    params["tags"] = clean_tags

                sql += " ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                params["limit"] = limit
                params["offset"] = offset

                result = await self.db.execute(text(sql), params)
                return [dict(row._mapping) for row in result.fetchall()]

            # Try optimized RPC first
            try:
                resp = await self.supabase.rpc(
                    "search_cat_photos", {"search_query": query, "result_limit": limit, "result_offset": offset}
                ).execute()
                results = resp.data if resp.data else []
                if tags and results:
                    results = self._filter_by_tags(results, tags)
                return results
            except Exception:
                db_query = (
                    self.supabase.table("cat_photos")
                    .select("*")
                    .is_("deleted_at", "null")
                    .text_search("search_vector", query, options={"type": "websearch"})
                    .order("uploaded_at", desc=True)  # type: ignore
                    .range(offset, offset + limit - 1)
                )
                if tags:
                    clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                    db_query = db_query.contains("tags", clean_tags)

                resp = await db_query.execute()
                return resp.data if resp.data else []
        except Exception as e:
            logger.warning("Advanced search failed: %s", e)
            raise

    async def _ilike_search(
        self, query: str | None = None, tags: list[str] | None = None, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fallback search using ILIKE."""
        if self.db:
            sql = "SELECT * FROM cat_photos WHERE deleted_at IS NULL"
            params: dict[str, Any] = {}

            if query:
                safe_query = f"%{escape_like_pattern(query)}%"
                sql += " AND (location_name ILIKE :query OR description ILIKE :query)"
                params["query"] = safe_query

            if tags:
                clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                sql += " AND tags @> :tags"
                params["tags"] = clean_tags

            sql += " ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await self.db.execute(text(sql), params)
            return [dict(row._mapping) for row in result.fetchall()]

        db_query = self.supabase.table("cat_photos").select("*").is_("deleted_at", "null")

        if query:
            safe_query = escape_like_pattern(query)
            # Use or_ for multi-column search
            db_query = db_query.or_(f"location_name.ilike.%{safe_query}%,description.ilike.%{safe_query}%")

        if tags:
            clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
            db_query = db_query.contains("tags", clean_tags)

        resp = await db_query.order("uploaded_at", desc=True).range(offset, offset + limit - 1).execute()
        return resp.data if resp.data else []

    def _filter_by_tags(self, photos: list[dict[str, Any]], tags: list[str]) -> list[dict[str, Any]]:
        """Client-side tag filtering fallback."""
        clean_tags = {tag.strip().lower().replace("#", "") for tag in tags}
        filtered = []
        for photo in photos:
            photo_tags = {t.lower() for t in (photo.get("tags") or [])}
            if clean_tags.issubset(photo_tags):
                filtered.append(photo)
        return filtered
