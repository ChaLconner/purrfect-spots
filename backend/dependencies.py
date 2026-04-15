from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth_service import AuthService
    from services.cat_detection_service import CatDetectionService
    from services.email_service import EmailService
    from services.gallery_service import GalleryService
    from services.google_vision import GoogleVisionService
    from services.notification_service import NotificationService
    from services.otp_service import OTPService
    from services.quota_service import QuotaService
    from services.report_service import ReportService
    from services.seo_service import SeoService
    from services.social_service import SocialService
    from services.storage_service import StorageService
    from services.subscription_service import SubscriptionService
    from services.token_service import TokenService
    from services.treats_service import TreatsService

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from logger import logger
from middleware.auth_middleware import get_current_user
from schemas.user import User
from utils.auth_utils import decode_token
from utils.supabase_client import (
    get_async_supabase_admin_client,
    get_async_supabase_client,
)

__all__ = [
    "get_async_supabase_client",
    "get_async_supabase_admin_client",
    "get_current_user_from_token",
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
    from services.storage_service import StorageService

    return StorageService()


def get_vision_service() -> GoogleVisionService:
    from services.google_vision import GoogleVisionService

    return GoogleVisionService()


def get_cat_detection_service(vision_service: GoogleVisionService = Depends(get_vision_service)) -> CatDetectionService:
    from services.cat_detection_service import CatDetectionService

    return CatDetectionService(vision_service=vision_service)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    from services.auth_service import AuthService

    return AuthService(
        supabase_client=await get_async_supabase_client(),
        supabase_admin=await get_async_supabase_admin_client(),
        db=db,
    )


async def get_gallery_service(db: AsyncSession = Depends(get_db)) -> GalleryService:
    from services.gallery_service import GalleryService

    return GalleryService(await get_async_supabase_client(), db=db)


async def get_admin_gallery_service(db: AsyncSession = Depends(get_db)) -> GalleryService:
    from services.gallery_service import GalleryService

    return GalleryService(await get_async_supabase_admin_client(), db=db)


def get_current_user_from_token(authorization: str | None = Header(None)) -> dict:
    """
    DEPRECATED: Use get_current_user instead.
    Extract and verify user from JWT payload ONLY. Does NOT check for bans or DB state.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    token = parts[1]
    try:
        return decode_token(token)
    except Exception as e:
        logger.warning("Token validation failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_token(authorization: str | None = Header(None)) -> str | None:
    """
    Extract the JWT token string from the Authorization header.
    Returns None if header is missing or invalid scheme.
    """
    if not authorization:
        return None

    try:
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        return parts[1]
    except (ValueError, IndexError):
        return None


async def get_current_admin_user(user: User = Depends(get_current_user)) -> User:
    """
    Dependency to check if current user is an admin.
    Now correctly uses the validated User object which checks for bans.
    """
    if user.role.lower() in ("admin", "super_admin") or {"admin_access", "access:admin"}.intersection(
        user.permissions
    ):
        return user

    logger.warning("Admin access denied for user: %s", user.id)
    raise HTTPException(status_code=403, detail="Admin privileges required")


async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    from services.notification_service import NotificationService

    return NotificationService(await get_async_supabase_admin_client(), db=db)


def get_email_service() -> EmailService:
    from services.email_service import email_service

    return email_service


async def get_quota_service(db: AsyncSession = Depends(get_db)) -> QuotaService:
    from services.quota_service import QuotaService

    return QuotaService(await get_async_supabase_admin_client(), db=db)


async def get_social_service(db: AsyncSession = Depends(get_db)) -> SocialService:
    from services.social_service import SocialService

    return SocialService(await get_async_supabase_admin_client(), db=db)


async def get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    from services.subscription_service import SubscriptionService

    return SubscriptionService(await get_async_supabase_client(), db=db)


async def get_treats_service(db: AsyncSession = Depends(get_db)) -> TreatsService:
    from services.treats_service import TreatsService

    return TreatsService(await get_async_supabase_admin_client(), db=db)


async def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    from services.report_service import ReportService

    return ReportService(await get_async_supabase_admin_client(), db=db)


async def get_seo_service(db: AsyncSession = Depends(get_db)) -> SeoService:
    from services.seo_service import SeoService

    return SeoService(await get_async_supabase_client(), db=db)


async def get_token_service(db: AsyncSession = Depends(get_db)) -> TokenService:
    from services.token_service import get_token_service as _get_token_service

    return await _get_token_service(db=db)


async def get_otp_service(db: AsyncSession = Depends(get_db)) -> OTPService:
    """Dependency: Get OTPService instance"""
    from services.otp_service import OTPService

    # CRITICAL: If db is still a 'Depends' object, it means it wasn't resolved by FastAPI.
    # This shouldn't normally happen but was reported in Sentry.
    if hasattr(db, "__class__") and db.__class__.__name__ == "Depends":
        logger.error("Dependency Resolution Error: get_otp_service received unsolved 'Depends' object as 'db'!")
        # Fallback to manual session if possible, though this is a last resort
        from database import AsyncSessionLocal

        if AsyncSessionLocal is not None:
            async with AsyncSessionLocal() as session:
                return OTPService(await get_async_supabase_admin_client(), db=session)
        else:
            logger.error("AsyncSessionLocal is None, cannot fallback to manual session")
            return OTPService(await get_async_supabase_admin_client(), db=None)

    return OTPService(await get_async_supabase_admin_client(), db=db)
