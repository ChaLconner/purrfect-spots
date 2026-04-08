from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from utils.supabase_client import AClient

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class GalleryBaseMixin:
    """Base mixin for GalleryService with common properties"""

    supabase: AClient
    db: AsyncSession | None
    _admin_client_lazy: AClient | None

    # Standard column selections to avoid select(*)
    PHOTO_COLUMNS = "id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, likes_count, comments_count, user_id"
    PHOTO_SELECT_SQL = (
        "SELECT id, image_url, latitude, longitude, description, location_name, "
        "uploaded_at, tags, likes_count, comments_count, user_id FROM cat_photos"
    )
    MAP_LOCATION_SELECT_SQL = "SELECT id, latitude, longitude, location_name, image_url, user_id FROM cat_photos"
    PHOTO_RETURNING_COLUMNS = (
        "id, image_url, latitude, longitude, description, location_name, "
        "uploaded_at, tags, likes_count, comments_count, user_id"
    )
    USER_COLUMNS = "id, name, username, picture, total_treats_received, role_id"
    APPROVED_STATUS = "approved"

    @property
    async def supabase_admin(self) -> AClient:
        """Lazy load admin client only when absolutely necessary"""
        if self._admin_client_lazy is None:
            from utils.supabase_client import get_async_supabase_admin_client

            self._admin_client_lazy = await get_async_supabase_admin_client()
        return self._admin_client_lazy

    def _sql_visibility_clause(self, include_unapproved: bool = False) -> str:
        """Return the SQL visibility clause for public or owner/admin reads."""
        clause = "deleted_at IS NULL"
        if not include_unapproved:
            clause += " AND status = :approved_status"
        return clause

    def _sql_visibility_params(self, include_unapproved: bool = False) -> dict[str, Any]:
        """Return bind parameters required by the SQL visibility clause."""
        if include_unapproved:
            return {}
        return {"approved_status": self.APPROVED_STATUS}

    def _apply_visibility_filter(self, query: Any, include_unapproved: bool = False) -> Any:
        """Apply visibility filters to a Supabase query builder."""
        filtered_query = query.is_("deleted_at", "null")
        if not include_unapproved:
            filtered_query = filtered_query.eq("status", self.APPROVED_STATUS)
        return filtered_query

    def _process_photos(self, photos: list[dict[str, Any]], width: int = 500) -> list[dict[str, Any]]:
        """Process a list of photos with optimizations (delegates to ImageService)"""
        from services.image_service import ImageService

        return ImageService.process_photos(photos, width)
