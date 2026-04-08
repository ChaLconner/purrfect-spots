from typing import Any, cast

import structlog
from postgrest.types import CountMethod
from sqlalchemy import text

from services.gallery.base_mixin import GalleryBaseMixin
from utils.cache import cached_gallery, cached_user_likes

logger = structlog.get_logger(__name__)


class GalleryReadMixin(GalleryBaseMixin):
    """READ operations for GalleryService"""

    # _process_photos moved to GalleryBaseMixin

    @cached_gallery
    async def get_all_photos(
        self,
        limit: int = 20,
        offset: int = 0,
        include_total: bool = True,
        user_id: str | None = None,
        jwt_token: str | None = None,
    ) -> dict[str, Any]:
        """Get photos for public gallery with pagination."""
        try:
            limit = min(max(1, limit), 100)
            offset = max(0, offset)
            logger.info(f"Fetching gallery photos: limit={limit}, offset={offset}, user_id={user_id}")

            data = await self._fetch_photos(limit, offset, user_id)
            if data and user_id:
                data = await self.enrich_with_user_data(data, user_id)
            data = self._process_photos(data)

            total = 0
            if include_total:
                total = await self._fetch_total_count(data)

            return {
                "data": data,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(data) < total if include_total else len(data) == limit,
            }
        except Exception as e:
            logger.error(f"Failed to fetch gallery images: {e!s}", exc_info=True)
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch gallery images: {e!s}", service="Supabase")

    async def get_all_photos_simple(self) -> list[dict[str, Any]]:
        """Simple get all photos wrapper returning only the data list."""
        res = await self.get_all_photos(include_total=False)
        return res["data"]

    async def _fetch_photos(self, limit: int, offset: int, user_id: str | None) -> list[dict[str, Any]]:
        """Fetch photos with hydrated user details where possible."""
        if self.db:
            return await self._fetch_photos_sql(limit, offset, user_id)
        return await self._fetch_photos_supabase(limit, offset, user_id)

    async def _fetch_photos_sql(self, limit: int, offset: int, user_id: str | None) -> list[dict[str, Any]]:
        if not self.db:
            return []
        query = text(
            self.PHOTO_SELECT_SQL
            + " WHERE deleted_at IS NULL AND status = :approved_status ORDER BY uploaded_at DESC LIMIT :limit OFFSET :offset"
        )
        result = await self.db.execute(
            query,
            {"approved_status": self.APPROVED_STATUS, "limit": limit, "offset": offset},
        )
        return [dict(row._asdict()) for row in result.fetchall()]

    async def _fetch_photos_supabase(self, limit: int, offset: int, user_id: str | None) -> list[dict[str, Any]]:
        query = self._apply_visibility_filter(self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS))
        res = await query.order("uploaded_at", desc=True).range(offset, offset + limit - 1).execute()
        return cast(list[dict[str, Any]], res.data or [])

    async def _fetch_total_count(self, data: list[dict[str, Any]]) -> int:
        try:
            if self.db:
                total_res = await self.db.execute(
                    text("SELECT count(*) FROM cat_photos WHERE deleted_at IS NULL AND status = :approved_status"),
                    {"approved_status": self.APPROVED_STATUS},
                )
                return total_res.scalar() or 0
            res_count = await self._apply_visibility_filter(
                self.supabase.table("cat_photos").select("id", count=CountMethod.exact)
            ).execute()
            return res_count.count or 0
        except Exception as e:
            logger.error(f"Count fetch failed: {e}")
            return len(data)

    @cached_gallery
    async def get_map_locations(self) -> list[dict[str, Any]]:
        try:
            if self.db:
                result = await self.db.execute(
                    text(
                        self.MAP_LOCATION_SELECT_SQL
                        + " WHERE deleted_at IS NULL AND status = :approved_status ORDER BY uploaded_at DESC LIMIT 2000"
                    ),
                    {"approved_status": self.APPROVED_STATUS},
                )
                data = [dict(row._asdict()) for row in result.fetchall()]
            else:
                res = (
                    await self._apply_visibility_filter(
                        self.supabase.table("cat_photos").select(
                            "id,latitude,longitude,location_name,image_url,user_id"
                        )
                    )
                    .order("uploaded_at", desc=True)
                    .limit(2000)
                    .execute()
                )
                data = cast(list[dict[str, Any]], res.data or [])

            for photo in data:
                if (
                    "image_url" in photo
                    and photo["image_url"]
                    and "supabase.co/storage/v1/object/public" in photo["image_url"]
                ):
                    sep = "&" if "?" in photo["image_url"] else "?"
                    photo["image_url"] = f"{photo['image_url']}{sep}width=100&resize=cover&format=webp"
            return data
        except Exception as e:
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch map locations: {e!s}", service="Supabase")

    async def get_photo_by_id(self, photo_id: str, include_unapproved: bool = False) -> dict[str, Any] | None:
        try:
            data = None
            if self.db:
                sql = self.PHOTO_SELECT_SQL + " WHERE id = :id AND deleted_at IS NULL"
                params: dict[str, Any] = {"id": photo_id}
                if not include_unapproved:
                    sql += " AND status = :approved_status"
                    params["approved_status"] = self.APPROVED_STATUS
                sql += " LIMIT 1"
                result = await self.db.execute(text(sql), params)
                row = result.fetchone()
                if row:
                    data = [dict(row._asdict())]
            if not data:
                res = (
                    await self._apply_visibility_filter(
                        self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS),
                        include_unapproved=include_unapproved,
                    )
                    .eq("id", photo_id)
                    .limit(1)
                    .execute()
                )
                data = cast(list[dict[str, Any]], res.data or [])
            if data:
                return self._process_photos(data, width=1200)[0]
            return None
        except Exception as e:
            logger.error(f"Failed to fetch photo {photo_id}: {e}")
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch photo {photo_id}", service="Supabase")

    async def enrich_with_user_data(self, photos: list[dict[str, Any]], user_id: str) -> list[dict[str, Any]]:
        if not photos:
            return []
        try:
            liked_ids = await self._get_user_liked_photo_ids(user_id)
            for photo in photos:
                photo["liked"] = photo["id"] in liked_ids
            return photos
        except Exception as e:
            logger.error(f"Failed to enrich photos with user data: {e!s}")
            return list(photos)

    @cached_user_likes
    async def _get_user_liked_photo_ids(self, user_id: str) -> set[str]:
        try:
            admin_client = await self.supabase_admin
            res = await admin_client.table("photo_likes").select("photo_id").eq("user_id", user_id).execute()
            data_list = cast(list[dict[str, Any]], res.data or [])
            return {cast(str, item["photo_id"]) for item in data_list}
        except Exception as e:
            logger.error(f"Failed to fetch user liked photo IDs: {e!s}")
            return set()

    async def get_all_photos_cursor(
        self,
        limit: int = 20,
        after_id: str | None = None,
        sort_field: str = "uploaded_at",
        sort_order: str = "desc",
        user_id: str | None = None,
        jwt_token: str | None = None,
    ) -> dict[str, Any]:
        """
        Get photos with cursor-based pagination.

        Uses the photo_id as a cursor anchor. Fetches records after the given
        cursor photo based on the sort field ordering.

        Args:
            limit: Number of records to fetch (fetches +1 internally for has_more).
            after_id: Cursor — fetch records after this photo_id.
            sort_field: Field to sort by (uploaded_at, likes_count, comments_count).
            sort_order: asc or desc.
            user_id: Optional user ID for enrichment.
            jwt_token: Optional JWT token.

        Returns:
            dict with 'data' list and 'has_more' flag.
        """
        limit = min(max(1, limit), 200)
        is_desc = sort_order.lower() == "desc"
        sort_column = self._resolve_cursor_sort_field(sort_field)
        tie_breaker = "<" if is_desc else ">"
        order_dir = "DESC" if is_desc else "ASC"

        try:
            # Get the anchor record's sort value if cursor is provided
            anchor_value = None
            if after_id:
                anchor = await self.get_photo_by_id(after_id)
                if anchor:
                    anchor_value = anchor.get(sort_field)

            if self.db:
                # SQL-based cursor pagination
                sql = self.PHOTO_SELECT_SQL + " WHERE deleted_at IS NULL AND status = :approved_status"
                params: dict[str, Any] = {"approved_status": self.APPROVED_STATUS, "limit": limit}

                if anchor_value is not None:
                    sql += (
                        f" AND ({sort_column} {tie_breaker} :anchor_value "
                        f"OR ({sort_column} = :anchor_value AND id {tie_breaker} :after_id))"
                    )
                    params["anchor_value"] = anchor_value
                    params["after_id"] = after_id
                elif after_id:
                    # Fallback: use id ordering if sort field value is missing
                    sql += " AND id > :after_id" if not is_desc else " AND id < :after_id"
                    params["after_id"] = after_id

                sql += f" ORDER BY {sort_column} {order_dir}, id {order_dir} LIMIT :limit"

                result = await self.db.execute(text(sql), params)
                data = [dict(row._asdict()) for row in result.fetchall()]
            else:
                # Supabase client cursor pagination
                query = self._apply_visibility_filter(self.supabase.table("cat_photos").select(self.PHOTO_COLUMNS))

                if anchor_value is not None:
                    query = query.order(sort_column, desc=is_desc).order("id", desc=is_desc)
                    query = query.lt(sort_column, anchor_value) if is_desc else query.gt(sort_column, anchor_value)
                elif after_id:
                    query = query.order("id", desc=is_desc)
                    query = query.lt("id", after_id) if is_desc else query.gt("id", after_id)
                else:
                    query = query.order(sort_column, desc=is_desc).order("id", desc=is_desc)

                res = await query.limit(limit).execute()
                data = cast(list[dict[str, Any]], res.data or [])

            # Enrich with user data if applicable
            if data and user_id:
                data = await self.enrich_with_user_data(data, user_id)

            data = self._process_photos(data)

            return {
                "data": data,
                "has_more": len(data) >= limit,
            }
        except Exception as e:
            logger.error(f"Cursor pagination fetch failed: {e!s}", exc_info=True)
            from utils.exceptions import ExternalServiceError

            raise ExternalServiceError(f"Failed to fetch gallery images: {e!s}", service="Supabase")
