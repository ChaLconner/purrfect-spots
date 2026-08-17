import asyncio
from datetime import UTC, date, datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from postgrest.types import CountMethod

from app.dependencies import (
    get_admin_gallery_service,
    get_async_supabase_admin_client,
    get_email_service,
    get_notification_service,
)
from app.limiter import limiter
from app.logger import logger
from app.middleware.auth_middleware import require_permission
from app.routes.admin.helpers import ADMIN_ERROR_RESPONSES, CommonPagination, fetch_cached_admin_list, fetch_photo_by_id
from app.schemas.admin_schemas import BulkReportUpdate, ReportResolutionUpdate
from app.schemas.user import User
from app.services.email_service import EmailService
from app.services.gallery_service import GalleryService
from app.services.notification_service import NotificationService
from app.services.redis_service import redis_service
from app.services.storage_service import storage_service
from app.utils.audit_logger import log_admin_action

router = APIRouter()

from app.utils.db_security import validate_or_raise_uuid as _validate_uuid


def _schedule_photo_deletion_and_notification(
    background_tasks: BackgroundTasks,
    photo_id: str,
    image_url: str,
    user_id: str,
    gallery_service: GalleryService,
    notification_service: NotificationService,
) -> None:
    background_tasks.add_task(
        gallery_service.process_photo_deletion,
        photo_id=photo_id,
        image_url=image_url,
        user_id=user_id,
        storage_service=storage_service,
    )
    if user_id:
        background_tasks.add_task(
            notification_service.create_notification,
            user_id=user_id,
            type="system",
            title="Content Removed",
            message="Your photo has been removed by a moderator due to a violation of our community guidelines.",
            resource_id=photo_id,
            resource_type="photo",
        )


def _reports_cache_key(
    limit: int,
    offset: int,
    status: str | None,
    reason: str | None,
    start_date: date | None,
    end_date: date | None,
    reporter_id: str | None,
) -> str:
    return (
        "admin_reports:"
        f"{limit}:{offset}:{status or '_'}:{reason or '_'}:{start_date or '_'}:{end_date or '_'}:{reporter_id or '_'}"
    )


async def _invalidate_reports_cache() -> None:
    await redis_service.delete_pattern("admin_reports:*")


async def _delete_report_photo(
    admin_client: Any,
    report_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    current_admin: User,
    gallery_service: GalleryService,
    notification_service: NotificationService,
    email_service: EmailService,
) -> None:
    report_check = await admin_client.table("reports").select("photo_id").eq("id", report_id).single().execute()
    if not report_check.data:
        raise HTTPException(status_code=404, detail="Report not found")
    photo_id = report_check.data.get("photo_id")
    if not photo_id:
        return

    photo_data = await fetch_photo_by_id(admin_client, str(photo_id))
    if not photo_data:
        return
    _schedule_photo_deletion_and_notification(
        background_tasks,
        photo_id=str(photo_id),
        image_url=str(photo_data.get("image_url") or ""),
        user_id=str(photo_data.get("user_id") or ""),
        gallery_service=gallery_service,
        notification_service=notification_service,
    )
    user_id = photo_data.get("user_id")
    if user_id:
        user_check = await admin_client.table("users").select("email").eq("id", str(user_id)).single().execute()
        email = user_check.data.get("email") if user_check.data else None
        if email:
            background_tasks.add_task(
                email_service.send_content_removal_notification,
                to_email=str(email),
                content_type="photo",
                reason="Violation of Community Guidelines",
            )
    await log_admin_action(
        admin_client=admin_client,
        admin_id=current_admin.id,
        action="DELETE_PHOTO_VIA_REPORT",
        target_type="photos",
        target_id=photo_id,
        details={"report_id": report_id, "ip": request.client.host if request.client else "unknown"},
    )


def _queue_reporter_notification(
    background_tasks: BackgroundTasks,
    notification_service: NotificationService,
    report_id: str,
    report: dict[str, Any],
    resolution_notes: str | None,
) -> None:
    reporter_id = report.get("reporter_id")
    if not reporter_id:
        return
    status_desc = "resolved" if report.get("status") == "resolved" else "dismissed"
    message = f"Your report has been {status_desc}."
    if resolution_notes:
        message += f" Note: {resolution_notes}"
    background_tasks.add_task(
        notification_service.create_notification,
        user_id=str(reporter_id),
        type="system",
        title="Report Update",
        message=message,
        resource_id=report_id,
        resource_type="report",
    )


async def _delete_bulk_report_photos(
    admin_client: Any,
    report_ids: list[str],
    background_tasks: BackgroundTasks,
    request: Request,
    current_admin: User,
    gallery_service: GalleryService,
    notification_service: NotificationService,
) -> None:
    reports_data = await (
        admin_client.table("reports")
        .select("id, photo_id, reporter_id, photo:cat_photos(id, image_url, user_id)")
        .in_("id", report_ids)
        .execute()
    )
    processed_photos: set[str] = set()
    audit_tasks: list[Any] = []
    for item in reports_data.data:
        report = cast(dict[str, Any], item)
        photo = cast(dict[str, Any], report.get("photo")) if isinstance(report.get("photo"), dict) else {}
        photo_id = photo.get("id")
        if not photo or not photo_id or photo_id in processed_photos:
            continue
        processed_photos.add(photo_id)
        _schedule_photo_deletion_and_notification(
            background_tasks,
            photo_id=str(photo_id),
            image_url=str(photo.get("image_url") or ""),
            user_id=str(photo.get("user_id") or ""),
            gallery_service=gallery_service,
            notification_service=notification_service,
        )
        audit_tasks.append(
            log_admin_action(
                admin_client=admin_client,
                admin_id=current_admin.id,
                action="DELETE_PHOTO_VIA_BULK_REPORT",
                target_type="photos",
                target_id=str(photo_id),
                details={"report_id": report.get("id"), "ip": request.client.host if request.client else "unknown"},
            )
        )
    if audit_tasks:
        await asyncio.gather(*audit_tasks)


def _queue_bulk_reporter_notifications(
    background_tasks: BackgroundTasks,
    notification_service: NotificationService,
    reports: list[dict[str, Any]],
    status: str,
) -> None:
    status_desc = "resolved" if status == "resolved" else "dismissed"
    processed_reporters: set[str] = set()
    for report in reports:
        reporter_id = report.get("reporter_id")
        if not reporter_id or reporter_id in processed_reporters:
            continue
        processed_reporters.add(reporter_id)
        background_tasks.add_task(
            notification_service.create_notification,
            user_id=str(reporter_id),
            type="system",
            title="Report Update (Bulk Action)",
            message=f"Your report has been {status_desc} (Processed in bulk)",
            resource_id=str(report.get("id")),
            resource_type="report",
        )


@router.get("/reports", responses=ADMIN_ERROR_RESPONSES)
@limiter.limit("60/minute")
async def list_reports(
    request: Request,
    pagination: Annotated[CommonPagination, Depends()],
    status: Annotated[str | None, Query()] = None,
    reason: Annotated[str | None, Query()] = None,
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
    reporter_id: Annotated[str | None, Query()] = None,
    cache_bust: Annotated[str | None, Query()] = None,
    current_admin: Annotated[User | None, Depends(require_permission("reports:read"))] = None,
) -> dict[str, Any]:
    """
    List submitted reports.

    Raises:
        HTTPException: 500 - If fetching reports fails.
    """
    try:
        cache_key = _reports_cache_key(
            pagination.limit, pagination.offset, status, reason, start_date, end_date, reporter_id
        )
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("reports")
            .select(
                "*, reporter:users!reporter_id(email), photo:cat_photos(image_url, location_name)",
                count=CountMethod.exact,
            )
            .range(pagination.offset, pagination.offset + pagination.limit - 1)
            .order("created_at", desc=True)
        )

        if status:
            query = query.eq("status", status)
        if reason:
            query = query.eq("reason", reason)
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        if reporter_id:
            query = query.eq("reporter_id", reporter_id)

        return await fetch_cached_admin_list(cache_key, bool(cache_bust), 60, query)
    except Exception as e:
        logger.error("Failed to list reports: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {e}")


@router.put("/reports/{report_id}", responses=ADMIN_ERROR_RESPONSES)
@limiter.limit("20/minute")
async def update_report(
    report_id: str,
    update_data: ReportResolutionUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_admin: Annotated[User, Depends(require_permission("reports:update"))],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    gallery_service: Annotated[GalleryService, Depends(get_admin_gallery_service)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> dict[str, Any]:
    """
    Resolve or dismiss a report.

    Raises:
        HTTPException: 400 - If report_id format is invalid.
        HTTPException: 404 - If report is not found.
        HTTPException: 500 - If update fails.
    """
    _validate_uuid(report_id, "report_id")
    try:
        admin_client = await get_async_supabase_admin_client()
        update_payload = update_data.model_dump()

        if update_payload["delete_content"] is True:
            await _delete_report_photo(
                admin_client,
                report_id,
                background_tasks,
                request,
                current_admin,
                gallery_service,
                notification_service,
                email_service,
            )

        # Update report status
        result = (
            await admin_client.table("reports")
            .update(
                {
                    "status": update_payload["status"],
                    "resolution_notes": update_payload["resolution_notes"],
                    "resolved_by": current_admin.id,
                    "resolved_at": datetime.now(UTC).isoformat(),
                }
            )
            .eq("id", report_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")

        report = cast(dict[str, Any], result.data[0])

        if update_payload["status"] in {"resolved", "dismissed"}:
            _queue_reporter_notification(
                background_tasks,
                notification_service,
                report_id,
                report,
                update_payload["resolution_notes"],
            )

        await _invalidate_reports_cache()
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update report: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update report")


@router.post("/reports/bulk", responses=ADMIN_ERROR_RESPONSES)
@limiter.limit("10/minute")
async def bulk_update_reports(
    bulk_data: BulkReportUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    current_admin: Annotated[User, Depends(require_permission("reports:update"))],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
    gallery_service: Annotated[GalleryService, Depends(get_admin_gallery_service)],
) -> dict[str, Any]:
    """
    Bulk resolve or dismiss reports.

    Raises:
        HTTPException: 500 - If bulk update fails.
    """
    try:
        admin_client = await get_async_supabase_admin_client()
        report_ids_str = [str(uid) for uid in bulk_data.report_ids]

        if bulk_data.delete_content:
            await _delete_bulk_report_photos(
                admin_client,
                report_ids_str,
                background_tasks,
                request,
                current_admin,
                gallery_service,
                notification_service,
            )

        result = (
            await admin_client.table("reports")
            .update(
                {
                    "status": bulk_data.status,
                    "resolution_notes": bulk_data.resolution_notes,
                    "resolved_by": current_admin.id,
                    "resolved_at": datetime.now(UTC).isoformat(),
                }
            )
            .in_("id", report_ids_str)
            .execute()
        )

        updated_reports = cast(list[dict[str, Any]], result.data if result.data else [])
        _queue_bulk_reporter_notifications(
            background_tasks,
            notification_service,
            updated_reports,
            bulk_data.status,
        )

        await _invalidate_reports_cache()
        return {"message": f"Successfully updated {len(updated_reports)} reports", "count": len(updated_reports)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to bulk update reports: %s", e)
        raise HTTPException(status_code=500, detail="Failed to bulk update reports")
