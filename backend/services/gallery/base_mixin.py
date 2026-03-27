from typing import TYPE_CHECKING

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
    USER_COLUMNS = "id, name, username, picture, total_treats_received, role_id"

    @property
    async def supabase_admin(self) -> AClient:
        """Lazy load admin client only when absolutely necessary"""
        if self._admin_client_lazy is None:
            from utils.supabase_client import get_async_supabase_admin_client

            self._admin_client_lazy = await get_async_supabase_admin_client()
        return self._admin_client_lazy
