from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import AClient

    from app.services.auth_service import AuthService
    from app.services.cat_detection_service import CatDetectionService
    from app.services.email_service import EmailService
    from app.services.gallery_service import GalleryService
    from app.services.google_vision import GoogleVisionService
    from app.services.notification_service import NotificationService
    from app.services.otp_service import OTPService
    from app.services.quota_service import QuotaService
    from app.services.report_service import ReportService
    from app.services.seo_service import SeoService
    from app.services.social_service import SocialService
    from app.services.storage_service import StorageService
    from app.services.subscription_service import SubscriptionService
    from app.services.token_service import TokenService
    from app.services.treats_service import TreatsService

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.admin_permissions import has_admin_access
from app.database import get_db
from app.logger import logger
from app.middleware.auth_middleware import get_current_user
from app.schemas.user import User
from app.utils.auth_utils import extract_bearer_token
from app.utils.supabase_client import (
    get_async_supabase_admin_client,
    get_async_supabase_client,
)

__all__ = [
    "get_async_supabase_client",
    "get_async_supabase_admin_client",
    "get_current_admin_user",
    "get_current_token",
    "get_current_user",
    "get_auth_service",
    "get_gallery_service",
    "get_admin_gallery_service",
    "get_notification_service",
    "get_email_service",
    "get_quota_service",
    "get_social_service",
    "get_subscription_service",
    "get_treats_service",
    "get_report_service",
    "get_seo_service",
    "get_token_service",
    "get_otp_service",
    "get_db",
    "get_storage_service",
    "get_vision_service",
    "get_cat_detection_service",
]


def get_storage_service() -> StorageService:
    from app.services.storage_service import StorageService

    return StorageService()


def get_vision_service() -> GoogleVisionService:
    from app.services.google_vision import GoogleVisionService

    return GoogleVisionService()


def get_cat_detection_service(vision_service: GoogleVisionService = Depends(get_vision_service)) -> CatDetectionService:
    from app.services.cat_detection_service import CatDetectionService

    return CatDetectionService(vision_service=vision_service)


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    supabase_client: AClient = Depends(get_async_supabase_client),
    supabase_admin: AClient = Depends(get_async_supabase_admin_client),
) -> AuthService:
    from app.services.auth_service import AuthService

    return AuthService(
        supabase_client=supabase_client,
        supabase_admin=supabase_admin,
        db=db,
    )


async def get_gallery_service(
    db: AsyncSession = Depends(get_db),
    supabase_client: AClient = Depends(get_async_supabase_client),
) -> GalleryService:
    from app.services.gallery_service import GalleryService

    return GalleryService(supabase_client, db=db)


async def get_admin_gallery_service(
    db: AsyncSession = Depends(get_db),
    supabase_admin: AClient = Depends(get_async_supabase_admin_client),
) -> GalleryService:
    from app.services.gallery_service import GalleryService

    return GalleryService(supabase_admin, db=db)


def get_current_token(authorization: str | None = Header(None)) -> str | None:
    """
    Extract the JWT token string from the Authorization header.
    Returns None if header is missing or invalid scheme.
    """
    return extract_bearer_token(authorization)


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Dependency to check if current user is an admin.
    Now correctly uses the validated User object which checks for bans.
    """
    if has_admin_access(user.role, user.permissions):
        return user

    logger.warning("Admin access denied for user: %s", user.id)
    raise HTTPException(status_code=403, detail="Admin privileges required")


async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    from app.services.notification_service import NotificationService

    return NotificationService(await get_async_supabase_admin_client(), db=db)


def get_email_service() -> EmailService:
    from app.services.email_service import email_service

    return email_service


async def get_quota_service(db: AsyncSession = Depends(get_db)) -> QuotaService:
    from app.services.quota_service import QuotaService

    return QuotaService(await get_async_supabase_admin_client(), db=db)


async def get_social_service(
    db: AsyncSession = Depends(get_db),
    supabase_admin: AClient = Depends(get_async_supabase_admin_client),
) -> SocialService:
    from app.services.social_service import SocialService

    return SocialService(supabase_admin, db=db)


async def get_subscription_service(
    db: AsyncSession = Depends(get_db),
    supabase_client: AClient = Depends(get_async_supabase_admin_client),
) -> SubscriptionService:
    from app.services.subscription_service import SubscriptionService

    return SubscriptionService(supabase_client, db=db)


async def get_treats_service(db: AsyncSession = Depends(get_db)) -> TreatsService:
    from app.services.treats_service import TreatsService

    return TreatsService(await get_async_supabase_admin_client(), db=db)


async def get_report_service(
    db: AsyncSession = Depends(get_db),
    supabase_admin: AClient = Depends(get_async_supabase_admin_client),
) -> ReportService:
    from app.services.report_service import ReportService

    return ReportService(supabase_admin, db=db)


async def get_seo_service(
    db: AsyncSession = Depends(get_db),
    supabase_client: AClient = Depends(get_async_supabase_client),
) -> SeoService:
    from app.services.seo_service import SeoService

    return SeoService(supabase_client, db=db)


async def get_token_service(db: AsyncSession = Depends(get_db)) -> TokenService:
    from app.services.token_service import get_token_service as _get_token_service

    return await _get_token_service(db=db)


async def get_otp_service(db: AsyncSession = Depends(get_db)) -> OTPService:
    """Dependency: Get OTPService instance"""
    from app.services.otp_service import OTPService

    # CRITICAL: If db is still a 'Depends' object, it means it wasn't resolved by FastAPI.
    # This shouldn't normally happen but was reported in Sentry.
    if hasattr(db, "__class__") and db.__class__.__name__ == "Depends":
        logger.error("Dependency Resolution Error: get_otp_service received unsolved 'Depends' object as 'db'!")
        # Fallback to manual session if possible, though this is a last resort
        from app.database import AsyncSessionLocal

        if AsyncSessionLocal is not None:
            async with AsyncSessionLocal() as session:
                return OTPService(await get_async_supabase_admin_client(), db=session)
        else:
            logger.error("AsyncSessionLocal is None, cannot fallback to manual session")
            return OTPService(await get_async_supabase_admin_client(), db=None)

    return OTPService(await get_async_supabase_admin_client(), db=db)
