from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.compat import structlog
from app.services.gallery.location_mixin import GalleryLocationMixin
from app.services.gallery.read_mixin import GalleryReadMixin
from app.services.gallery.search_mixin import GallerySearchMixin
from app.services.gallery.write_mixin import GalleryWriteMixin
from app.services.search_service import SearchService

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
        self.search_service = SearchService(supabase_client, db=db)
        self._admin_client_lazy: AClient | None = None
