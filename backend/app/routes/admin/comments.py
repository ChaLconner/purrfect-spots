import asyncio
from datetime import datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from postgrest.types import CountMethod
from pydantic import BaseModel

from app.constants.admin_permissions import COMMENTS_MANAGE
from app.dependencies import get_async_supabase_admin_client, get_notification_service
from app.logger import logger
from app.middleware.auth_middleware import invalidate_user_auth_cache, require_permission
from app.routes.admin.helpers import create_admin_audit_log
from app.schemas.user import User
from app.services.notification_service import NotificationService
from app.services.token_service import get_token_service
from app.utils.audit_logger import log_admin_action
from app.utils.db_security import escape_like_pattern, sanitize_search_input

router = APIRouter()
MAX_COMMENTS_PAGE_SIZE = 100
ADMIN_COMMENT_COLUMNS = (
    "id, content, user_id, photo_id, created_at, user_display_name, user_username, user_avatar, report_count"
)
ADMIN_COMMENT_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"description": "Invalid moderation request"},
    404: {"description": "Comment or user not found"},
    500: {"description": "Internal server error"},
}


class BulkCommentAction(BaseModel):
    comment_ids: list[str]


def _build_comment_query(
    admin_client: Any,
    offset: int,
    page_size: int,
    search: str | None,
    reported_only: bool,
) -> Any:
    query = (
        admin_client.table("admin_comment_list")
        .select(ADMIN_COMMENT_COLUMNS, count=CountMethod.exact)
        .order("created_at", desc=True)
        .range(offset, offset + page_size - 1)
    )
    if search:
        clean_search = sanitize_search_input(search)
        if clean_search:
            safe_search = escape_like_pattern(clean_search)
            query = query.or_(
                f"content.ilike.%{safe_search}%,"
                f"user_display_name.ilike.%{safe_search}%,"
                f"user_username.ilike.%{safe_search}%"
            )
    if reported_only:
        query = query.gt("report_count", 0)
    return query


async def _fetch_comment_user_map(admin_client: Any, user_ids: list[str]) -> dict[str, Any]:
    if not user_ids:
        return {}
    chunks = [user_ids[i : i + 50] for i in range(0, len(user_ids), 50)]
    tasks = [admin_client.table("users").select("id, email, banned_at").in_("id", chunk).execute() for chunk in chunks]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    user_map: dict[str, Any] = {}
    for result in responses:
        if isinstance(result, BaseException) or not hasattr(result, "data"):
            continue
        for user in cast(list[dict[str, Any]], result.data):
            user_map[user["id"]] = user
    return user_map


def _enrich_comments(items: list[dict[str, Any]], user_map: dict[str, Any]) -> None:
    for item in items:
        user = user_map.get(item["user_id"], {})
        item["user_email"] = user.get("email")
        item["is_user_banned"] = user.get("banned_at") is not None
        item["violation_count"] = 0


async def _invalidate_banned_user_auth_state(user_id: str) -> None:
    await invalidate_user_auth_cache(user_id)
    token_service = await get_token_service()
    await token_service.blacklist_all_user_tokens(user_id, reason="comment_moderation_ban")


@router.get("", responses=ADMIN_COMMENT_RESPONSES)
async def list_all_comments(
    current_admin: Annotated[User, Depends(require_permission(COMMENTS_MANAGE))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int | None, Query(ge=1, le=MAX_COMMENTS_PAGE_SIZE)] = None,
    limit: Annotated[int | None, Query(ge=1, le=MAX_COMMENTS_PAGE_SIZE)] = None,
    search: Annotated[str | None, Query()] = None,
    reported_only: Annotated[bool, Query()] = False,
) -> dict[str, Any]:
    """List all comments across the platform with pagination, search and counts."""
    try:
        admin_client = await get_async_supabase_admin_client()
        effective_page_size = page_size or limit or 20

        offset = (page - 1) * effective_page_size

        result = await _build_comment_query(admin_client, offset, effective_page_size, search, reported_only).execute()
        items = cast(list[dict[str, Any]], result.data)
        total_count = result.count or 0
        pages = (total_count + effective_page_size - 1) // effective_page_size

        user_ids = list({item["user_id"] for item in items if item.get("user_id")})
        _enrich_comments(items, await _fetch_comment_user_map(admin_client, user_ids))

        return {"items": items, "total": total_count, "page": page, "pages": pages}
    except Exception as e:
        logger.error("Failed to list comments: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch comments")


@router.get("/{comment_id}/reports", responses=ADMIN_COMMENT_RESPONSES)
async def get_comment_report_details(
    comment_id: str,
    current_admin: Annotated[User, Depends(require_permission(COMMENTS_MANAGE))],
) -> list[dict[str, Any]]:
    """Get detailed report reasons for a specific comment."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = (
            await admin_client.table("reports")
            .select("reason, reporter_id, created_at, reporter:users!reporter_id(email, username)")
            .eq("comment_id", comment_id)
            .eq("status", "pending")
            .execute()
        )
        return cast(list[dict[str, Any]], result.data)
    except Exception as e:
        logger.error("Failed to fetch report details: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch report details")


@router.put("/{comment_id}/resolve", responses=ADMIN_COMMENT_RESPONSES)
async def resolve_comment_reports(
    comment_id: str,
    request: Request,
    current_admin: Annotated[User, Depends(require_permission(COMMENTS_MANAGE))],
) -> dict[str, str]:
    """Dismiss all pending reports for a comment (Mark as Safe)."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # Update reports status
        await (
            admin_client.table("reports")
            .update(
                {
                    "status": "dismissed",
                    "resolved_by": current_admin.id,
                    "resolved_at": datetime.now().isoformat(),
                    "resolution_notes": "Dismissed by admin via moderation dashboard",
                }
            )
            .eq("comment_id", comment_id)
            .eq("status", "pending")
            .execute()
        )

        # Log Audit
        await log_admin_action(
            admin_client=admin_client,
            admin_id=current_admin.id,
            action="RESOLVE_COMMENT_REPORTS",
            target_type="photo_comments",
            target_id=comment_id,
            details={"action": "dismissed_reports", "ip": request.client.host if request.client else "unknown"},
        )

        return {"message": "Reports dismissed successfully"}
    except Exception as e:
        logger.error("Failed to resolve comment reports: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve reports")


@router.delete("/{comment_id}", responses=ADMIN_COMMENT_RESPONSES)
async def delete_comment(
    comment_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission(COMMENTS_MANAGE))],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> dict[str, str]:
    """Delete a comment (Moderation)."""
    try:
        admin_client = await get_async_supabase_admin_client()

        comment_res = await admin_client.table("photo_comments").select("*").eq("id", comment_id).single().execute()
        if not comment_res.data:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Resolve any pending reports for this comment first
        await (
            admin_client.table("reports")
            .update(
                {
                    "status": "resolved",
                    "resolved_by": current_admin.id,
                    "resolved_at": datetime.now().isoformat(),
                    "resolution_notes": "Resolved via comment deletion",
                }
            )
            .eq("comment_id", comment_id)
            .eq("status", "pending")
            .execute()
        )

        # Delete the comment
        await admin_client.table("photo_comments").delete().eq("id", comment_id).execute()

        # Log Audit
        await log_admin_action(
            admin_client=admin_client,
            admin_id=current_admin.id,
            action="DELETE_COMMENT",
            target_type="photo_comments",
            target_id=str(comment_id),
            details={
                "deleted_content": cast(dict[str, Any], comment_res.data)["content"],
                "author_id": str(cast(dict[str, Any], comment_res.data)["user_id"]),
                "ip": request.client.host if request.client else "unknown",
            },
        )

        # Notify User
        background_tasks.add_task(
            notification_service.create_notification,
            user_id=str(cast(dict[str, Any], comment_res.data)["user_id"]),
            type="comment_removed",
            title="Comment Removed",
            message="One of your comments was removed by a moderator for violating community guidelines.",
            actor_id=current_admin.id,
        )

        return {"message": "Comment deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error("Failed to delete comment: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete comment")


@router.post("/{comment_id}/ban-user", responses=ADMIN_COMMENT_RESPONSES)
async def ban_user_by_comment(
    comment_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission(COMMENTS_MANAGE))],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> dict[str, str]:
    """Ban the author of a specific comment."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # Find user ID from comment
        comment_res = (
            await admin_client.table("photo_comments").select("user_id").eq("id", comment_id).single().execute()
        )
        if not comment_res.data:
            raise HTTPException(status_code=404, detail="Comment not found")

        comment_data = cast(dict[str, Any], comment_res.data)
        user_id = str(comment_data["user_id"])

        user_check = await admin_client.table("users").select("email, roles(name)").eq("id", user_id).single().execute()
        if not user_check.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = cast(dict[str, Any], user_check.data)
        role_info = user_data.get("roles")
        role_name = (role_info.get("name") if isinstance(role_info, dict) else "user") or "user"
        if role_name.lower() in ("admin", "super_admin"):
            raise HTTPException(status_code=400, detail="Cannot ban an admin user")

        # Ban user
        await admin_client.table("users").update({"banned_at": datetime.now().isoformat()}).eq("id", user_id).execute()
        await _invalidate_banned_user_auth_state(user_id)

        # Log Audit
        await log_admin_action(
            admin_client=admin_client,
            admin_id=current_admin.id,
            action="BAN_USER",
            target_type="users",
            target_id=user_id,
            details={
                "reason": "Banned via comment moderation",
                "comment_id": comment_id,
                "ip": request.client.host if request.client else "unknown",
            },
        )

        # Notify User (System notification might not be visible if they can't login, but good for records)
        background_tasks.add_task(
            notification_service.create_notification,
            user_id=str(user_id),
            type="account_banned",
            title="Account Suspended",
            message="Your account has been permanently suspended for multiple violations of our community guidelines.",
            actor_id=current_admin.id,
        )

        return {"message": "User banned successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error("Failed to ban user: %s", e)
        raise HTTPException(status_code=500, detail="Failed to ban user")


@router.post("/bulk-delete", responses=ADMIN_COMMENT_RESPONSES)
async def bulk_delete_comments(
    action_data: BulkCommentAction,
    request: Request,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission(COMMENTS_MANAGE))],
    notification_service: Annotated[NotificationService, Depends(get_notification_service)],
) -> dict[str, str]:
    """Delete multiple comments in a single action."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # Resolve reports
        await (
            admin_client.table("reports")
            .update(
                {
                    "status": "resolved",
                    "resolved_by": current_admin.id,
                    "resolved_at": datetime.now().isoformat(),
                    "resolution_notes": "Bulk resolved via deletion",
                }
            )
            .in_("comment_id", action_data.comment_ids)
            .eq("status", "pending")
            .execute()
        )

        # Fetch authors before the comments are removed.
        comments_res = await (
            admin_client.table("photo_comments").select("user_id").in_("id", action_data.comment_ids).execute()
        )
        comments_data = cast(list[dict[str, Any]], comments_res.data)
        author_ids = list({str(c["user_id"]) for c in comments_data})

        # Delete comments
        await admin_client.table("photo_comments").delete().in_("id", action_data.comment_ids).execute()

        # Log Audit
        await create_admin_audit_log(
            admin_client,
            current_admin.id,
            "BULK_DELETE_COMMENTS",
            "photo_comments",
            {"comment_ids": action_data.comment_ids},
        )

        for author_id in author_ids:
            background_tasks.add_task(
                notification_service.create_notification,
                user_id=str(author_id),
                type="comment_removed",
                title="Content Removed",
                message="One or more of your comments were removed by a moderator for violation of guidelines.",
                actor_id=current_admin.id,
            )

        return {"message": f"Successfully deleted {len(action_data.comment_ids)} comments"}
    except Exception as e:
        logger.error("Failed bulk delete: %s", e)
        raise HTTPException(status_code=500, detail="Bulk delete failed")


@router.post("/bulk-resolve", responses=ADMIN_COMMENT_RESPONSES)
async def bulk_resolve_comments(
    action_data: BulkCommentAction,
    request: Request,
    current_admin: Annotated[User, Depends(require_permission(COMMENTS_MANAGE))],
) -> dict[str, str]:
    """Dismiss reports for multiple comments in a single action."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # Resolve reports
        await (
            admin_client.table("reports")
            .update(
                {
                    "status": "dismissed",
                    "resolved_by": current_admin.id,
                    "resolved_at": datetime.now().isoformat(),
                    "resolution_notes": "Bulk dismissed via dashboard",
                }
            )
            .in_("comment_id", action_data.comment_ids)
            .eq("status", "pending")
            .execute()
        )

        # Log Audit
        await create_admin_audit_log(
            admin_client,
            current_admin.id,
            "BULK_RESOLVE_COMMENT_REPORTS",
            "photo_comments",
            {"comment_ids": action_data.comment_ids},
        )

        return {"message": f"Successfully dismissed reports for {len(action_data.comment_ids)} comments"}
    except Exception as e:
        logger.error("Failed bulk resolve: %s", e)
        raise HTTPException(status_code=500, detail="Bulk resolve failed")
