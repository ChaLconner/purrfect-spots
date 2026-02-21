from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from services.auth_service import AuthService
    from services.email_service import EmailService
    from services.gallery_service import GalleryService
    from services.notification_service import NotificationService
    from services.quota_service import QuotaService
    from services.report_service import ReportService
    from services.seo_service import SeoService
    from services.social_service import SocialService
    from services.subscription_service import SubscriptionService
    from services.treats_service import TreatsService
    from services.user_service import UserService

from fastapi import Depends, Header, HTTPException

from logger import logger
from middleware.auth_middleware import get_current_user
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
    "get_user_service",
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
]


async def get_user_service() -> UserService:
    from services.user_service import UserService

    return UserService(
        supabase_client=await get_async_supabase_client(), supabase_admin=await get_async_supabase_admin_client()
    )


async def get_auth_service() -> AuthService:
    from services.auth_service import AuthService

    return AuthService(
        supabase_client=await get_async_supabase_client(), supabase_admin=await get_async_supabase_admin_client()
    )


async def get_gallery_service() -> GalleryService:
    from services.gallery_service import GalleryService

    return GalleryService(await get_async_supabase_client())


async def get_admin_gallery_service() -> GalleryService:
    from services.gallery_service import GalleryService

    return GalleryService(await get_async_supabase_admin_client())


def get_current_user_from_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Extract and verify user from JWT token in Authorization header.
    Always verifies the JWT signature using JWT_SECRET.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Parse the Authorization header
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    token = parts[1]

    try:
        return decode_token(token)
    except ValueError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected token validation error: {type(e).__name__}")
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Extract the JWT token string from the Authorization header.
    Returns None if header is missing or invalid scheme.
    """
    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None


async def get_current_admin_user(user: dict = Depends(get_current_user_from_token)) -> dict:
    """
    Dependency to check if current user is an admin.
    """
    # Optimization: Check JWT claim first
    if user.get("role") == "admin":
        return user

    # Fallback: Check role in DB (for older tokens or Supabase tokens without claim)
    user_id = user.get("user_id") or user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")

    try:
        # Check role in DB asynchronously
        from utils.supabase_client import get_async_supabase_admin_client

        client = await get_async_supabase_admin_client()
        res = await client.table("users").select("role").eq("id", user_id).single().execute()

        if not res.data or res.data.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin privileges required")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin check failed: {e}")
        raise HTTPException(status_code=403, detail="Admin privileges required")


async def get_notification_service() -> NotificationService:
    from services.notification_service import NotificationService

    return NotificationService(await get_async_supabase_admin_client())


async def get_email_service() -> EmailService:
    from services.email_service import email_service

    return email_service


async def get_quota_service() -> QuotaService:
    from services.quota_service import QuotaService

    return QuotaService(await get_async_supabase_admin_client())


async def get_social_service() -> SocialService:
    from services.social_service import SocialService

    return SocialService(await get_async_supabase_admin_client())


async def get_subscription_service() -> SubscriptionService:
    from services.subscription_service import SubscriptionService

    return SubscriptionService(await get_async_supabase_client())


async def get_treats_service() -> TreatsService:
    from services.treats_service import TreatsService

    return TreatsService(await get_async_supabase_admin_client())


async def get_report_service() -> ReportService:
    from services.report_service import ReportService

    return ReportService(await get_async_supabase_admin_client())


async def get_seo_service() -> SeoService:
    from services.seo_service import SeoService

    return SeoService(await get_async_supabase_client())
