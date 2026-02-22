from datetime import datetime
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
from schemas.admin_schemas import BulkReportUpdate
from services.email_service import EmailService
from services.gallery_service import GalleryService
from services.notification_service import NotificationService
from services.storage_service import storage_service
from user_models.user import User

router = APIRouter()

# Helper to validate UUID (duplicated for now, could move to shared utils)
import re

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


def _validate_uuid(value: str, label: str = "ID") -> None:
    if not _UUID_RE.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label} format: expected UUID")


@router.get("/reports", response_model=dict[str, Any])
@limiter.limit("60/minute")
async def list_reports(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    reason: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    reporter_id: str | None = None,
    current_admin: User = Depends(require_permission("content:read")),
) -> dict[str, Any]:
    """List submitted reports."""
    try:
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("reports")
            .select(
                "*, reporter:users!reporter_id(email), photo:cat_photos(image_url, location_name)",
                count=CountMethod.exact,
            )
            .range(offset, offset + limit - 1)
            .order("created_at", desc=True)
        )

        if status:
            query = query.eq("status", status)
        if reason:
            query = query.eq("reason", reason)
        if start_date:
            query = query.gte("created_at", start_date)
        if end_date:
            query = query.lte("created_at", end_date)
        if reporter_id:
            query = query.eq("reporter_id", reporter_id)

        result = await query.execute()
        return {"data": result.data, "total": result.count}
    except Exception as e:
        logger.error(f"Failed to list reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {e}")


@router.put("/reports/{report_id}", response_model=dict)
@limiter.limit("20/minute")
async def update_report(
    report_id: str,
    update_data: dict[str, Any],
    background_tasks: BackgroundTasks,
    request: Request,
    current_admin: User = Depends(require_permission("content:delete")),
    notification_service: NotificationService = Depends(get_notification_service),
    gallery_service: GalleryService = Depends(get_admin_gallery_service),
    email_service: EmailService = Depends(get_email_service),
) -> dict[str, Any]:
    """Resolve or dismiss a report."""
    _validate_uuid(report_id, "report_id")
    try:
        admin_client = await get_async_supabase_admin_client()

        # Handle 'delete_content' action
        if update_data.get("delete_content") is True:
            # Fetch report to get photo_id
            report_check = await admin_client.table("reports").select("photo_id").eq("id", report_id).single().execute()
            if not report_check.data:
                raise HTTPException(status_code=404, detail="Report not found")

            photo_id = report_check.data.get("photo_id")

            if photo_id:
                photo_check = (
                    await admin_client.table("cat_photos")
                    .select("id, image_url, user_id")
                    .eq("id", photo_id)
                    .single()
                    .execute()
                )

                if photo_check.data:
                    photo_data = photo_check.data

                    # Schedule deletion
                    background_tasks.add_task(
                        gallery_service.process_photo_deletion,
                        photo_id=photo_id,
                        image_url=photo_data.get("image_url") or "",
                        user_id=photo_data.get("user_id"),
                        storage_service=storage_service,
                    )

                    # Notify Owner
                    if photo_data.get("user_id"):
                        background_tasks.add_task(
                            notification_service.create_notification,
                            user_id=photo_data.get("user_id"),
                            type="system",
                            title="Content Removed",
                            message="Your photo has been removed by a moderator due to a violation of our community guidelines.",
                            resource_id=photo_id,
                            resource_type="photo",
                        )

                        user_check = (
                            await admin_client.table("users")
                            .select("email")
                            .eq("id", photo_data.get("user_id"))
                            .single()
                            .execute()
                        )
                        if user_check.data and user_check.data.get("email"):
                            background_tasks.add_task(
                                email_service.send_content_removal_notification,
                                to_email=user_check.data["email"],
                                content_type="photo",
                                reason="Violation of Community Guidelines",
                            )

                    await (
                        admin_client.table("audit_logs")
                        .insert(
                            {
                                "user_id": current_admin.id,
                                "action": "DELETE_PHOTO_VIA_REPORT",
                                "resource": "photos",
                                "changes": {"photo_id": photo_id, "report_id": report_id},
                                "ip_address": request.client.host if request.client else "unknown",
                                "user_agent": "system",
                            }
                        )
                        .execute()
                    )

        # Update report status
        result = (
            await admin_client.table("reports")
            .update(
                {
                    "status": update_data.get("status"),
                    "resolution_notes": update_data.get("resolution_notes"),
                    "resolved_by": current_admin.id,
                    "resolved_at": datetime.now().isoformat(),
                }
            )
            .eq("id", report_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")

        report = result.data[0]

        # Notify reporter
        new_status = update_data.get("status")
        if new_status in ["resolved", "dismissed"] and report.get("reporter_id"):
            status_desc = "resolved" if new_status == "resolved" else "dismissed"
            message = f"Your report has been {status_desc}."
            if update_data.get("resolution_notes"):
                message += f" Note: {update_data.get('resolution_notes')}"

            background_tasks.add_task(
                notification_service.create_notification,
                user_id=report.get("reporter_id"),
                type="system",
                title="Report Update",
                message=message,
                resource_id=report_id,
                resource_type="report",
            )

        return cast(dict[str, Any], report)
    except Exception as e:
        logger.error(f"Failed to update report: {e}")
        raise HTTPException(status_code=500, detail="Failed to update report")


@router.post("/reports/bulk", response_model=dict[str, Any])
@limiter.limit("10/minute")
async def bulk_update_reports(
    bulk_data: BulkReportUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_admin: User = Depends(require_permission("content:delete")),
    notification_service: NotificationService = Depends(get_notification_service),
    gallery_service: GalleryService = Depends(get_admin_gallery_service),
    email_service: EmailService = Depends(get_email_service),
) -> dict[str, Any]:
    """Bulk resolve or dismiss reports."""
    try:
        admin_client = await get_async_supabase_admin_client()
        report_ids_str = [str(uid) for uid in bulk_data.report_ids]

        if bulk_data.delete_content:
            reports_data = (
                await admin_client.table("reports")
                .select("id, photo_id, reporter_id, photo:cat_photos(id, image_url, user_id)")
                .in_("id", report_ids_str)
                .execute()
            )

            processed_photos = set()

            for report in reports_data.data:
                photo = report.get("photo")
                if photo and photo.get("id") and photo.get("id") not in processed_photos:
                    photo_id = photo.get("id")
                    processed_photos.add(photo_id)

                    background_tasks.add_task(
                        gallery_service.process_photo_deletion,
                        photo_id=photo_id,
                        image_url=photo.get("image_url") or "",
                        user_id=photo.get("user_id"),
                        storage_service=storage_service,
                    )

                    if photo.get("user_id"):
                        background_tasks.add_task(
                            notification_service.create_notification,
                            user_id=photo.get("user_id"),
                            type="system",
                            title="Content Removed",
                            message="Your photo has been removed by a moderator due to a violation of our community guidelines.",
                            resource_id=photo_id,
                            resource_type="photo",
                        )

                    await (
                        admin_client.table("audit_logs")
                        .insert(
                            {
                                "user_id": current_admin.id,
                                "action": "DELETE_PHOTO_VIA_BULK_REPORT",
                                "resource": "photos",
                                "changes": {"photo_id": photo_id, "report_id": report.get("id")},
                                "ip_address": request.client.host if request.client else "unknown",
                                "user_agent": "system",
                            }
                        )
                        .execute()
                    )

        result = (
            await admin_client.table("reports")
            .update(
                {
                    "status": bulk_data.status,
                    "resolution_notes": bulk_data.resolution_notes,
                    "resolved_by": current_admin.id,
                    "resolved_at": datetime.now().isoformat(),
                }
            )
            .in_("id", report_ids_str)
            .execute()
        )

        updated_reports = result.data if result.data else []

        reporters_processed = set()
        for report in updated_reports:
            reporter_id = report.get("reporter_id")
            if reporter_id and reporter_id not in reporters_processed:
                reporters_processed.add(reporter_id)
                status_desc = "resolved" if bulk_data.status == "resolved" else "dismissed"
                background_tasks.add_task(
                    notification_service.create_notification,
                    user_id=reporter_id,
                    type="system",
                    title="Report Update (Bulk Action)",
                    message=f"Your report has been {status_desc} (Processed in bulk)",
                    resource_id=report.get("id"),
                    resource_type="report",
                )

        return {"message": f"Successfully updated {len(updated_reports)} reports", "count": len(updated_reports)}
    except Exception as e:
        logger.error(f"Failed to bulk update reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to bulk update reports")
