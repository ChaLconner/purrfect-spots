from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
from supabase import AClient
from utils.db_security import escape_like_pattern, sanitize_search_input


class SearchService:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        self._fulltext_available: bool | None = None
        # Explicit column selection to avoid over-fetching
        self.PHOTO_COLUMNS = "id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, likes_count, comments_count, user_id"
        self.APPROVED_STATUS = "approved"

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
        """Perform full-text search with SQL fallback to Supabase client."""
        # Try SQL approach first
        if self.db:
            try:
                params: dict[str, Any] = {"query": query, "approved_status": self.APPROVED_STATUS}

                if tags:
                    clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                    params["tags"] = clean_tags
                    sql_query = text(
                        "SELECT id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, "
                        "likes_count, comments_count, user_id "
                        "FROM cat_photos "
                        "WHERE deleted_at IS NULL AND status = :approved_status "
                        "AND search_vector @@ websearch_to_tsquery('english', :query) "
                        "AND tags @> :tags "
                        "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                    )
                else:
                    sql_query = text(
                        "SELECT id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, "
                        "likes_count, comments_count, user_id "
                        "FROM cat_photos "
                        "WHERE deleted_at IS NULL AND status = :approved_status "
                        "AND search_vector @@ websearch_to_tsquery('english', :query) "
                        "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                    )

                params["limit"] = limit
                params["offset"] = offset

                result = await self.db.execute(sql_query, params)
                return [dict(row._mapping) for row in result.fetchall()]
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
                clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                db_query = db_query.contains("tags", clean_tags)

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
                sql_query: Any

                if query:
                    safe_query = f"%{escape_like_pattern(query)}%"
                    params["query"] = safe_query

                if tags:
                    clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                    params["tags"] = clean_tags
                if query and tags:
                    sql_query = text(
                        "SELECT id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, "
                        "likes_count, comments_count, user_id "
                        "FROM cat_photos "
                        "WHERE deleted_at IS NULL AND status = :approved_status "
                        "AND (location_name ILIKE :query OR description ILIKE :query) "
                        "AND tags @> :tags "
                        "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                    )
                elif query:
                    sql_query = text(
                        "SELECT id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, "
                        "likes_count, comments_count, user_id "
                        "FROM cat_photos "
                        "WHERE deleted_at IS NULL AND status = :approved_status "
                        "AND (location_name ILIKE :query OR description ILIKE :query) "
                        "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                    )
                elif tags:
                    sql_query = text(
                        "SELECT id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, "
                        "likes_count, comments_count, user_id "
                        "FROM cat_photos "
                        "WHERE deleted_at IS NULL AND status = :approved_status "
                        "AND tags @> :tags "
                        "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                    )
                else:
                    sql_query = text(
                        "SELECT id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, "
                        "likes_count, comments_count, user_id "
                        "FROM cat_photos "
                        "WHERE deleted_at IS NULL AND status = :approved_status "
                        "ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
                    )
                params["limit"] = limit
                params["offset"] = offset

                result = await self.db.execute(sql_query, params)
                return [dict(row._mapping) for row in result.fetchall()]
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
                clean_tags = [tag.strip().lower().replace("#", "") for tag in tags]
                db_query = db_query.contains("tags", clean_tags)

            resp = await db_query.order("uploaded_at", desc=True).range(offset, offset + limit - 1).execute()
            return cast(list[dict[str, Any]], resp.data or [])
        except Exception as e:
            logger.error("Supabase ILIKE search failed as well: %s", e)
            raise

    def _filter_by_tags(self, photos: list[dict[str, Any]], tags: list[str]) -> list[dict[str, Any]]:
        """Client-side tag filtering fallback."""
        clean_tags = {tag.strip().lower().replace("#", "") for tag in tags}
        filtered = []
        for photo in photos:
            photo_tags = {t.lower() for t in (photo.get("tags") or [])}
            if clean_tags.issubset(photo_tags):
                filtered.append(photo)
        return filtered
