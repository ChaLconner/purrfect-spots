import hashlib

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AClient

from utils.supabase_client import get_async_supabase_admin_client

logger = structlog.get_logger(__name__)


class AuthBaseMixin:
    """Base mixin for auth service containing shared state and helpers."""

    @property
    def supabase_client(self) -> AClient:
        raise NotImplementedError

    @property
    def supabase_admin(self) -> AClient | None:
        raise NotImplementedError

    @property
    def db(self) -> AsyncSession | None:
        raise NotImplementedError

    # Will be assigned in the main class
    jwt_secret: str
    jwt_algorithm: str

    async def _get_admin_client(self) -> AClient:
        if self.supabase_admin:
            return self.supabase_admin
        return await get_async_supabase_admin_client()

    def _generate_fingerprint(self, ip: str, user_agent: str) -> str:
        """Generate SHA256 fingerprint from full IP address and User-Agent."""
        if not user_agent:
            user_agent = "unknown"
        ip_segment = ip.strip() if ip else "unknown"
        raw = f"{user_agent}|{ip_segment}"
        return hashlib.sha256(raw.encode()).hexdigest()
