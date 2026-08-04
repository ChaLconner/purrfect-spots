from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.compat import structlog
from app.utils.supabase_client import AClient

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class GalleryBaseMixin:
    """Base mixin for GalleryService with common properties"""

    supabase: AClient
    db: AsyncSession | None
    _admin_client_lazy: AClient | None

    PHOTO_COLUMNS = "id, image_url, latitude, longitude, description, location_name, uploaded_at, tags, likes_count, comments_count, user_id"
    USER_COLUMNS = "id, name, username, picture, total_treats_received, role_id"
    APPROVED_STATUS = "approved"

    async def get_supabase_admin(self) -> AClient | None:
        """Lazy load admin client only when absolutely necessary"""
        if self._admin_client_lazy is None:
            from app.utils.supabase_client import get_async_supabase_admin_client

            client = await get_async_supabase_admin_client()
            # Verify we actually got a client with a service role key
            if client and hasattr(client, "supabase_key") and not client.supabase_key:
                logger.warning("Supabase admin client initialized without service role key; features will be limited")

            self._admin_client_lazy = client

        return self._admin_client_lazy

    def _apply_visibility_filter(self, query: Any, include_unapproved: bool = False) -> Any:
        """Apply visibility filters to a Supabase query builder."""
        # CatLocation requires a complete coordinate pair. Legacy rows with
        # no location remain stored, but must not enter map/gallery responses.
        filtered_query = query.is_("deleted_at", "null").not_.is_("latitude", "null").not_.is_("longitude", "null")
        if not include_unapproved:
            filtered_query = filtered_query.eq("status", self.APPROVED_STATUS)
        return filtered_query

    def _process_photos(self, photos: list[dict[str, Any]], width: int = 500) -> list[dict[str, Any]]:
        """Process a list of photos with optimizations (delegates to ImageService)"""
        from app.services.image_service import ImageService

        return ImageService.process_photos(photos, width)

    async def enrich_with_user_data(
        self, photos: list[dict[str, Any]], user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Provide the enrichment contract implemented by the read mixin."""
        raise NotImplementedError
