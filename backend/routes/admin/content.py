import re
from typing import Any, cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from postgrest.types import CountMethod

from dependencies import (
    get_admin_gallery_service,
    get_async_supabase_admin_client,
    get_email_service,
    get_notification_service,
)
from limiter import limiter
from logger import logger
from middleware.auth_middleware import require_permission
from schemas.admin_schemas import PhotoUpdateAdmin
from services.email_service import EmailService
from services.gallery_service import GalleryService
from services.notification_service import NotificationService
from services.storage_service import storage_service
from user_models.user import User

router = APIRouter()

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _validate_uuid(value: str, label: str = "ID") -> None:
    if not _UUID_RE.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label} format: expected UUID")


@router.get("/photos", response_model=dict[str, Any])
@limiter.limit("60/minute")
async def list_photos(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
    reported: bool = False,
    current_admin: User = Depends(require_permission("content:read")),
) -> dict[str, Any]:
    """
    List all photos with pagination and optional search.
    Only accessible by admins with content:read permission.
    """
    try:
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("cat_photos")
            .select("*, users!cat_photos_user_id_fkey(email, name)", count=CountMethod.exact)
            .range(offset, offset + limit - 1)
            .order("uploaded_at", desc=True)
        )

        if search:
            query = query.or_(f"description.ilike.%{search}%,location_name.ilike.%{search}%")

        # Future: Filter by reported status

        result = await query.execute()
        return {"data": result.data, "total": result.count}
    except Exception as e:
        error_details = getattr(e, "details", "No details")
        error_hint = getattr(e, "hint", "No hint")
        logger.error(f"Failed to list photos: {e} | Details: {error_details} | Hint: {error_hint}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch photos: {e}")


@router.delete("/photos/{photo_id}")
@limiter.limit("20/minute")
async def delete_photo_admin(
    photo_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(require_permission("content:delete")),
    gallery_service: GalleryService = Depends(get_admin_gallery_service),
    notification_service: NotificationService = Depends(get_notification_service),
    email_service: EmailService = Depends(get_email_service),
) -> dict[str, str]:
    """
    Delete a photo as an admin (Content Moderation).
    No ownership check required.
    """
    _validate_uuid(photo_id, "photo_id")
    try:
        admin_client = await get_async_supabase_admin_client()

        # 1. Get photo details
        photo_check = (
            await admin_client.table("cat_photos")
            .select("id, image_url, user_id")
            .eq("id", photo_id)
            .single()
            .execute()
        )

        if not photo_check.data:
            raise HTTPException(status_code=404, detail="Photo not found")

        photo_data = photo_check.data

        # 2. Schedule background deletion
        background_tasks.add_task(
            gallery_service.process_photo_deletion,
            photo_id=photo_id,
            image_url=photo_data.get("image_url") or "",
            user_id=photo_data.get("user_id"),
            storage_service=storage_service,
        )

        # Notify owner
        if photo_data.get("user_id"):
            # System Notification
            background_tasks.add_task(
                notification_service.create_notification,
                user_id=photo_data.get("user_id"),
                type="system",
                title="Content Removed",
                message="Your photo has been removed by a moderator due to a violation of our community guidelines.",
                resource_id=photo_id,
                resource_type="photo",
            )

            # Email Notification
            user_check = (
                await admin_client.table("users").select("email").eq("id", photo_data.get("user_id")).single().execute()
            )
            if user_check.data and user_check.data.get("email"):
                background_tasks.add_task(
                    email_service.send_content_removal_notification,
                    to_email=user_check.data["email"],
                    content_type="photo",
                    reason="Violation of Community Guidelines",
                )

        # 3. Log Audit Log
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "DELETE_PHOTO",
                    "resource": "photos",
                    "changes": {"photo_id": photo_id, "owner_id": photo_data.get("user_id")},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        return {"message": f"Photo {photo_id} deletion scheduled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete photo {photo_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {e}")


@router.patch("/photos/{photo_id}", response_model=dict[str, Any])
@limiter.limit("20/minute")
async def update_photo_admin(
    request: Request,
    photo_id: str,
    update_data: PhotoUpdateAdmin,
    current_admin: User = Depends(require_permission("content:write")),
) -> dict[str, Any]:
    """
    Update photo details as an admin.
    """
    _validate_uuid(photo_id, "photo_id")
    try:
        admin_client = await get_async_supabase_admin_client()

        filtered_data = update_data.model_dump(exclude_unset=True)
        if not filtered_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")

        result = await admin_client.table("cat_photos").update(filtered_data).eq("id", photo_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Photo not found")

        return cast(dict[str, Any], result.data[0])
    except Exception as e:
        logger.error(f"Failed to update photo {photo_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update photo")
