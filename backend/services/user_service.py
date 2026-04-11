try:
    import structlog  # type: ignore[import-untyped, unused-ignore]
except ImportError:
    import logging
    from typing import Any

    class DummyStructlog:
        def get_logger(self, *args: Any, **kwargs: Any) -> Any:
            return logging.getLogger("purrfect_spots.fallback")

    structlog = DummyStructlog()  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession

from services.user.auth_mixin import UserAuthMixin
from services.user.deletion_mixin import UserDeletionMixin
from services.user.profile_mixin import UserProfileMixin
from services.user.read_mixin import UserReadMixin
from supabase import AClient

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

    # Note: methods are now provided by mixins:
    # - UserReadMixin: get_user_by_id, get_user_by_email, get_user_by_username, etc.
    # - UserAuthMixin: create_unverified_user, authenticate_user.
    # - UserProfileMixin: create_or_get_user, update_user_profile.
    # - UserDeletionMixin: request_account_deletion, cancel_account_deletion, execute_hard_delete.
