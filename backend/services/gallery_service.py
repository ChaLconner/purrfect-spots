from typing import TYPE_CHECKING

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from services.gallery.location_mixin import GalleryLocationMixin
from services.gallery.read_mixin import GalleryReadMixin
from services.gallery.search_mixin import GallerySearchMixin
from services.gallery.write_mixin import GalleryWriteMixin
from services.search_service import SearchService
from utils.supabase_client import AClient

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class GalleryService(GalleryReadMixin, GalleryWriteMixin, GallerySearchMixin, GalleryLocationMixin):
    """
    Service for gallery and photo management with full-text search support.
    Refactored to several mixins for better maintainability.
    """

    _fulltext_supported_cache: bool | None = None

    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        self.search_service = SearchService(supabase_client)
        self._admin_client_lazy: AClient | None = None

    # Note: methods are now provided by mixins:
    # - GalleryReadMixin: get_all_photos, get_map_locations, get_photo_by_id, enrich_with_user_data, etc.
    # - GalleryWriteMixin: save_photo, process_photo_deletion, verify_photo_ownership.
    # - GallerySearchMixin: search_photos, get_popular_tags, get_user_photos.
    # - GalleryLocationMixin: get_nearby_photos.
