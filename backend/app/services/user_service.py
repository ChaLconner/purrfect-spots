from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from app.compat import structlog
from app.services.user.auth_mixin import UserAuthMixin
from app.services.user.deletion_mixin import UserDeletionMixin
from app.services.user.profile_mixin import UserProfileMixin
from app.services.user.read_mixin import UserReadMixin

logger = structlog.get_logger(__name__)


class UserService(UserReadMixin, UserAuthMixin, UserProfileMixin, UserDeletionMixin):
    """
    Service for user-related operations using Async Supabase Client.
    Refactored to several mixins for better maintainability.
    """

    def __init__(
        self, supabase_client: AClient, supabase_admin: AClient | None = None, db: AsyncSession | None = None
    ) -> None:
        self._supabase = supabase_client
        self._supabase_admin = supabase_admin
        self._db = db

    @property
    def supabase(self) -> AClient:
        return self._supabase

    @property
    def supabase_admin(self) -> AClient | None:
        return self._supabase_admin

    @property
    def db(self) -> AsyncSession | None:
        return self._db
