from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from typing import Annotated, Any, List
from postgrest.types import CountMethod
from dependencies import get_async_supabase_admin_client, get_notification_service
from services.notification_service import NotificationService
from middleware.auth_middleware import require_permission
from schemas.user import User
from logger import logger
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

class BulkCommentAction(BaseModel):
    comment_ids: List[str]

@router.get("/")
async def list_all_comments(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=1000)] = 20,
    search: Annotated[str | None, Query()] = None,
    reported_only: Annotated[bool, Query()] = False,
    current_admin: Annotated[User, Depends(require_permission("comments:manage"))] = None,
):
    """List all comments across the platform with pagination, search and counts."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        offset = (page - 1) * page_size
        
        # Base query for data using the view admin_comment_list
        query = admin_client.table("admin_comment_list").select("*", count=CountMethod.exact).order("created_at", desc=True).range(offset, offset + page_size - 1)
        
        if search:
            query = query.or_(f"content.ilike.%{search}%,user_display_name.ilike.%{search}%,user_username.ilike.%{search}%")
            
        if reported_only:
            query = query.gt("report_count", 0)
            
        result = await query.execute()
        
        items = result.data
        user_ids = list(set(item["user_id"] for item in items))
        
        # Fetch violation history counts for these users
        violation_counts = {}
        if user_ids:
            # Fetch user status
            users_status = await admin_client.table("users").select("id, banned_at").in_("id", user_ids).execute()
            status_map = {u["id"]: u["banned_at"] for u in users_status.data}
            
            # Fetch violation history counts (resolved reports on their comments)
            # We fetch all resolved reports for comments owned by these users
            v_res = await admin_client.table("photo_comments") \
                .select("user_id, reports!inner(id)") \
                .eq("reports.status", "resolved") \
                .in_("user_id", user_ids) \
                .execute()
            
            v_counts = {}
            for row in v_res.data:
                uid = row["user_id"]
                v_counts[uid] = v_counts.get(uid, 0) + 1
            
            for item in items:
                uid = item["user_id"]
                item["is_user_banned"] = status_map.get(uid) is not None
                item["violation_count"] = v_counts.get(uid, 0)
        
        total_count = result.count or 0
        pages = (total_count + page_size - 1) // page_size
        
        reported_query = admin_client.table("reports").select("comment_id", count=CountMethod.exact).eq("status", "pending").not_.is_("comment_id", "null")
        reported_result = await reported_query.execute()
        reported_count = reported_result.count or 0
        
        return {
            "items": items, 
            "total": total_count,
            "reported_count": reported_count,
            "page": page,
            "pages": pages
        }
    except Exception as e:
        logger.error("Failed to list comments: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch comments")


@router.get("/{comment_id}/reports")
async def get_comment_report_details(
    comment_id: str,
    current_admin: Annotated[User, Depends(require_permission("comments:manage"))] = None,
):
    """Get detailed report reasons for a specific comment."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("reports").select("reason, reporter_id, created_at, reporter:users!reporter_id(email, username)").eq("comment_id", comment_id).eq("status", "pending").execute()
        return result.data
    except Exception as e:
        logger.error("Failed to fetch report details: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch report details")


@router.put("/{comment_id}/resolve")
async def resolve_comment_reports(
    comment_id: str,
    request: Request,
    current_admin: Annotated[User, Depends(require_permission("comments:manage"))] = None,
):
    """Dismiss all pending reports for a comment (Mark as Safe)."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        # Update reports status
        await admin_client.table("reports").update({
            "status": "dismissed",
            "resolved_by": current_admin.id,
            "resolved_at": datetime.now().isoformat(),
            "resolution_notes": "Dismissed by admin via moderation dashboard"
        }).eq("comment_id", comment_id).eq("status", "pending").execute()
        
        # Log Audit
        await admin_client.table("audit_logs").insert({
            "user_id": current_admin.id,
            "action": "RESOLVE_COMMENT_REPORTS",
            "resource": "photo_comments",
            "changes": {"comment_id": comment_id, "action": "dismissed_reports"},
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }).execute()
        
        return {"message": "Reports dismissed successfully"}
    except Exception as e:
        logger.error("Failed to resolve comment reports: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve reports")


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission("comments:manage"))] = None,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Delete a comment (Moderation)."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        comment_res = await admin_client.table("photo_comments").select("*").eq("id", comment_id).single().execute()
        if not comment_res.data:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        # Resolve any pending reports for this comment first
        await admin_client.table("reports").update({
            "status": "resolved",
            "resolved_by": current_admin.id,
            "resolved_at": datetime.now().isoformat(),
            "resolution_notes": "Resolved via comment deletion"
        }).eq("comment_id", comment_id).eq("status", "pending").execute()
        
        # Delete the comment
        await admin_client.table("photo_comments").delete().eq("id", comment_id).execute()
        
        # Log Audit
        await admin_client.table("audit_logs").insert({
            "user_id": current_admin.id,
            "action": "DELETE_COMMENT",
            "resource": "photo_comments",
            "changes": {"comment_id": comment_id, "deleted_content": comment_res.data["content"], "author_id": comment_res.data["user_id"]},
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }).execute()

        # Notify User
        background_tasks.add_task(
            notification_service.create_notification,
            user_id=comment_res.data["user_id"],
            type="comment_removed",
            title="Comment Removed",
            message="One of your comments was removed by a moderator for violating community guidelines.",
            actor_id=current_admin.id
        )
        
        return {"message": "Comment deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logger.error("Failed to delete comment: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete comment")


@router.post("/{comment_id}/ban-user")
async def ban_user_by_comment(
    comment_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission("comments:manage"))] = None,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Ban the author of a specific comment."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        # Find user ID from comment
        comment_res = await admin_client.table("photo_comments").select("user_id").eq("id", comment_id).single().execute()
        if not comment_res.data:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        user_id = comment_res.data["user_id"]
        
        # Ban user
        await admin_client.table("users").update({
            "banned_at": datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        # Log Audit
        await admin_client.table("audit_logs").insert({
            "user_id": current_admin.id,
            "action": "BAN_USER",
            "resource": "users",
            "changes": {"user_id": user_id, "reason": "Banned via comment moderation", "comment_id": comment_id},
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }).execute()

        # Notify User (System notification might not be visible if they can't login, but good for records)
        background_tasks.add_task(
            notification_service.create_notification,
            user_id=user_id,
            type="account_banned",
            title="Account Suspended",
            message="Your account has been permanently suspended for multiple violations of our community guidelines.",
            actor_id=current_admin.id
        )
        
        return {"message": "User banned successfully"}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logger.error("Failed to ban user: %s", e)
        raise HTTPException(status_code=500, detail="Failed to ban user")


@router.post("/bulk-delete")
async def bulk_delete_comments(
    action_data: BulkCommentAction,
    request: Request,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission("comments:manage"))] = None,
    notification_service: NotificationService = Depends(get_notification_service)
):
    """Delete multiple comments in a single action."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        # Resolve reports
        await admin_client.table("reports").update({
            "status": "resolved",
            "resolved_by": current_admin.id,
            "resolved_at": datetime.now().isoformat(),
            "resolution_notes": "Bulk resolved via deletion"
        }).in_("comment_id", action_data.comment_ids).eq("status", "pending").execute()
        
        # Delete comments
        await admin_client.table("photo_comments").delete().in_("id", action_data.comment_ids).execute()
        
        # Log Audit
        await admin_client.table("audit_logs").insert({
            "user_id": current_admin.id,
            "action": "BULK_DELETE_COMMENTS",
            "resource": "photo_comments",
            "changes": {"comment_ids": action_data.comment_ids},
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }).execute()

        # Fetch authors for notification
        comments_res = await admin_client.table("photo_comments").select("user_id").in_("id", action_data.comment_ids).execute()
        author_ids = list(set(c["user_id"] for c in comments_res.data))
        
        for author_id in author_ids:
            background_tasks.add_task(
                notification_service.create_notification,
                user_id=author_id,
                type="comment_removed",
                title="Content Removed",
                message="One or more of your comments were removed by a moderator for violation of guidelines.",
                actor_id=current_admin.id
            )
        
        return {"message": f"Successfully deleted {len(action_data.comment_ids)} comments"}
    except Exception as e:
        logger.error("Failed bulk delete: %s", e)
        raise HTTPException(status_code=500, detail="Bulk delete failed")


@router.post("/bulk-resolve")
async def bulk_resolve_comments(
    action_data: BulkCommentAction,
    request: Request,
    current_admin: Annotated[User, Depends(require_permission("comments:manage"))] = None,
):
    """Dismiss reports for multiple comments in a single action."""
    try:
        admin_client = await get_async_supabase_admin_client()
        
        # Resolve reports
        await admin_client.table("reports").update({
            "status": "dismissed",
            "resolved_by": current_admin.id,
            "resolved_at": datetime.now().isoformat(),
            "resolution_notes": "Bulk dismissed via dashboard"
        }).in_("comment_id", action_data.comment_ids).eq("status", "pending").execute()
        
        # Log Audit
        await admin_client.table("audit_logs").insert({
            "user_id": current_admin.id,
            "action": "BULK_RESOLVE_COMMENT_REPORTS",
            "resource": "photo_comments",
            "changes": {"comment_ids": action_data.comment_ids},
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }).execute()
        
        return {"message": f"Successfully dismissed reports for {len(action_data.comment_ids)} comments"}
    except Exception as e:
        logger.error("Failed bulk resolve: %s", e)
        raise HTTPException(status_code=500, detail="Bulk resolve failed")

