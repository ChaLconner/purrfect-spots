from datetime import datetime
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, Request
from postgrest.types import CountMethod

from dependencies import (
    get_async_supabase_admin_client,
    get_email_service,
)
from limiter import limiter
from logger import logger, sanitize_log_value
from middleware.auth_middleware import invalidate_user_auth_cache, require_permission
from schemas.admin_schemas import BulkUserAction, RoleUpdateAdmin, UserBan, UserUpdateAdmin
from schemas.user import User
from services.email_service import EmailService
from services.redis_service import redis_service
from services.token_service import get_token_service
from utils.security_alerts import track_bulk_operation

router = APIRouter()

UserIdPath = Annotated[UUID, Path(title="The ID of the user", description="Must be a valid UUID")]
RoleIdPath = Annotated[UUID, Path(title="The ID of the role", description="Must be a valid UUID")]


async def _invalidate_user_list_cache() -> None:
    """Invalidate all admin user list cache pages after any mutation."""
    await redis_service.delete_pattern("admin_users:*")


async def _invalidate_auth_cache_for_users(user_ids: list[str]) -> None:
    for user_id in user_ids:
        await invalidate_user_auth_cache(user_id)


async def _invalidate_banned_user_auth_state(user_ids: list[str], reason: str) -> None:
    unique_user_ids = list(dict.fromkeys(user_ids))
    token_service = await get_token_service()

    for user_id in unique_user_ids:
        await invalidate_user_auth_cache(user_id)
        await token_service.blacklist_all_user_tokens(user_id, reason=reason)


@router.get("/users", response_model=dict[str, Any])
@limiter.limit("60/minute")
async def list_users(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=1000)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query()] = None,
    sort_by: Annotated[str, Query(alias="sort")] = "created_at",
    order: Annotated[str, Query()] = "desc",
    current_admin: Annotated[User | None, Depends(require_permission("users:read"))] = None,
) -> dict[str, Any]:
    """
    List all users with pagination, search, and sorting.
    """
    # Skip cache for search queries — results must be accurate and fresh.
    # Cache paginated list views for 60s to reduce DB load on the common case.
    cache_key = f"admin_users:{offset}:{limit}:{sort_by}:{order}" if not search else None
    if cache_key:
        cached = await redis_service.get(cache_key)
        if cached:
            return cast(dict[str, Any], cached)
    try:
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("users")
            .select(
                "id, email, name, picture, treat_balance, is_pro, created_at, banned_at, roles(name)",
                count=CountMethod.exact,
            )
            .range(offset, offset + limit - 1)
        )

        allowed_sort_fields = ["created_at", "email", "name", "treat_balance", "role"]
        db_sort_field = sort_by
        if sort_by not in allowed_sort_fields:
            db_sort_field = "created_at"
        elif sort_by == "role":
            db_sort_field = "roles(name)"  # Correct syntax for join sorting in some psql versions

        query = query.order(db_sort_field, desc=(order.lower() == "desc"))

        if search:
            # OPTIMIZATION: Using Full Text Search (FTS) index
            # Ensure index idx_users_search_vector remains sync'd
            query = cast(Any, query.text_search("search_vector", f"'{search}'"))

        result = await query.execute()
        users_data = result.data
        total_count = result.count if result.count is not None else 0

        processed_data = []
        for user in users_data:
            user_copy = user.copy()
            role_info = user_copy.pop("roles", None)

            role_name = "user"
            if isinstance(role_info, dict):
                role_name = role_info.get("name", "user")
            elif isinstance(role_info, list) and len(role_info) > 0:
                role_name = role_info[0].get("name", "user")

            user_copy["role"] = role_name
            processed_data.append(user_copy)

        result_data = {"data": processed_data, "total": total_count}
        if cache_key:
            await redis_service.set(cache_key, result_data, expire=60)  # 60-second TTL
        return result_data
    except Exception as e:
        logger.error("Failed to list users: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.post("/users/bulk-ban")
@limiter.limit("5/minute")
async def bulk_ban_users(
    request: Request,
    action: BulkUserAction,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission("users:update"))],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> dict[str, Any]:
    """
    Ban multiple users at once.
    """
    try:
        admin_client = await get_async_supabase_admin_client()
        user_ids_str = [str(uid) for uid in action.user_ids]

        # Robust check to protect admins
        roles_check = (
            await admin_client.table("users").select("id, email, roles(name)").in_("id", user_ids_str).execute()
        )

        target_uids = []
        target_emails = []
        skipped_admins = 0

        for u in roles_check.data:
            role_name = (u.get("roles") or {}).get("name") or "user"
            if role_name.lower() in ("admin", "super_admin"):
                skipped_admins += 1
            else:
                target_uids.append(u["id"])
                if u.get("email"):
                    target_emails.append(u["email"])

        if not target_uids:
            return {"message": "No valid users found to ban.", "skipped": skipped_admins}

        # SECURITY: Track bulk operations for alerting
        ip_address = request.client.host if request.client else "unknown"
        track_bulk_operation(
            user_id=current_admin.id,
            operation="bulk_ban",
            record_count=len(target_uids),
            ip_address=ip_address,
        )

        # Perform bulk update
        await (
            admin_client.table("users")
            .update({"banned_at": datetime.now().isoformat()})
            .in_("id", target_uids)
            .execute()
        )
        await _invalidate_banned_user_auth_state(target_uids, reason="bulk_admin_ban")

        # Background task for emails
        for email in target_emails:
            background_tasks.add_task(
                email_service.send_ban_notification, to_email=email, reason=action.reason or "Bulk Administrative Ban"
            )

        # Log Audit
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "BULK_BAN",
                    "resource": "users",
                    "changes": {"target_user_ids": target_uids, "reason": action.reason},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        await _invalidate_user_list_cache()
        return {"message": f"Successfully banned {len(target_uids)} users.", "skipped": skipped_admins}
    except Exception as e:
        logger.error("Bulk ban failed: %s", e)
        raise HTTPException(status_code=500, detail="Bulk action failed")


@router.post("/users/bulk-unban")
@limiter.limit("5/minute")
async def bulk_unban_users(
    request: Request,
    action: BulkUserAction,
    current_admin: Annotated[User, Depends(require_permission("users:update"))],
) -> dict[str, Any]:
    """
    Unban multiple users at once.
    """
    try:
        admin_client = await get_async_supabase_admin_client()
        user_ids_str = [str(uid) for uid in action.user_ids]

        await admin_client.table("users").update({"banned_at": None}).in_("id", user_ids_str).execute()
        await _invalidate_auth_cache_for_users(user_ids_str)

        # Log Audit
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "BULK_UNBAN",
                    "resource": "users",
                    "changes": {"target_user_ids": user_ids_str},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        await _invalidate_user_list_cache()
        return {"message": f"Successfully unbanned {len(user_ids_str)} users."}
    except Exception as e:
        logger.error("Bulk unban failed: %s", e)
        raise HTTPException(status_code=500, detail="Bulk action failed")


@router.delete("/users/{user_id}")
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: UserIdPath,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission("users:delete"))],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> dict[str, str]:
    """
    Permanently delete a user and their data.
    """
    user_id_str = str(user_id)
    try:
        admin_client = await get_async_supabase_admin_client()

        check = await admin_client.table("users").select("email, roles(name)").eq("id", user_id_str).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = check.data[0]
        role_info = user_data.get("roles")
        role_name = (role_info.get("name") if role_info else "user").lower()

        if role_name == "admin" or role_name == "super_admin":
            raise HTTPException(status_code=400, detail="Cannot delete an admin user")

        if user_data.get("email"):
            background_tasks.add_task(
                email_service.send_account_deletion_notification,
                to_email=user_data["email"],
                reason="Administrative Action",
            )

        anonymized_data = {
            "name": "[Deleted User]",
            "email": f"deleted_{user_id_str}@example.com",
            "picture": None,
            "bio": None,
            "stripe_customer_id": None,
        }

        await admin_client.table("users").update(anonymized_data).eq("id", user_id_str).execute()
        await _invalidate_banned_user_auth_state([user_id_str], reason="admin_delete")

        # Log action
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "SOFT_DELETE_USER",
                    "resource": "users",
                    "changes": {"target_user_id": user_id_str, "original_email": user_data.get("email")},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        await _invalidate_user_list_cache()
        return {"message": f"User {user_id_str} data anonymized"}
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to delete user %s", sanitize_log_value(user_id_str))
        raise HTTPException(status_code=500, detail="Failed to delete user")


@router.patch("/users/{user_id}/profile", response_model=dict[str, Any])
@limiter.limit("20/minute")
async def update_user_profile_admin(
    request: Request,
    user_id: UserIdPath,
    update_data: UserUpdateAdmin,
    current_admin: Annotated[User, Depends(require_permission("users:write"))],
) -> dict[str, Any]:
    """
    Update user profile as admin.
    """
    user_id_str = str(user_id)
    try:
        admin_client = await get_async_supabase_admin_client()
        filtered_data = update_data.model_dump(exclude_unset=True)

        if not filtered_data:
            raise HTTPException(status_code=400, detail="No valid fields provided")

        result = await admin_client.table("users").update(filtered_data).eq("id", user_id_str).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        await invalidate_user_auth_cache(user_id_str)
        await _invalidate_user_list_cache()

        return cast(dict[str, Any], result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user profile %s: %s", sanitize_log_value(user_id_str), e)
        raise HTTPException(status_code=500, detail="Failed to update user profile")


@router.put("/users/{user_id}/role")
@limiter.limit("20/minute")
async def update_user_role(
    request: Request,
    user_id: UserIdPath,
    role_data: RoleUpdateAdmin,
    current_admin: Annotated[User, Depends(require_permission("users:update"))],
) -> dict[str, Any]:
    """
    Update user role.
    """
    user_id_str = str(user_id)
    role_id_str = str(role_data.role_id) if role_data.role_id else None
    if not role_id_str:
        raise HTTPException(status_code=400, detail="role_id is required")

    try:
        admin_client = await get_async_supabase_admin_client()
        role_check = await admin_client.table("roles").select("name").eq("id", role_id_str).single().execute()
        if not role_check.data:
            raise HTTPException(status_code=404, detail="Role not found")

        role_name = role_check.data.get("name")
        result = await admin_client.table("users").update({"role_id": role_id_str}).eq("id", user_id_str).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        await invalidate_user_auth_cache(user_id_str)
        await _invalidate_user_list_cache()

        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "UPDATE_ROLE",
                    "resource": "users",
                    "changes": {"target_user_id": user_id_str, "new_role": role_name},
                    "ip_address": request.client.host if request.client else "unknown",
                }
            )
            .execute()
        )

        return cast(dict[str, Any], result.data[0])
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to update user role %s", sanitize_log_value(user_id_str))
        raise HTTPException(status_code=500, detail="Failed to update role")


@router.post("/users/{user_id}/ban")
@limiter.limit("5/minute")
async def ban_user(
    request: Request,
    user_id: UserIdPath,
    ban_data: UserBan,
    background_tasks: BackgroundTasks,
    current_admin: Annotated[User, Depends(require_permission("users:update"))],
    email_service: Annotated[EmailService, Depends(get_email_service)],
) -> dict[str, str]:
    """
    Ban a user.
    """
    user_id_str = str(user_id)
    try:
        admin_client = await get_async_supabase_admin_client()
        supa_res = (
            await admin_client.table("users")
            .select("id, email, name, username, picture, bio, created_at, banned_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
        user_data = cast(dict[str, Any], supa_res.data)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        role_name = (user_data.get("roles") or {}).get("name") or "user"
        if role_name.lower() in ("admin", "super_admin"):
            raise HTTPException(status_code=400, detail="Cannot ban an admin user")

        await (
            admin_client.table("users")
            .update({"banned_at": datetime.now().isoformat()})
            .eq("id", user_id_str)
            .execute()
        )
        await _invalidate_banned_user_auth_state([user_id_str], reason="admin_ban")

        if user_data.get("email"):
            background_tasks.add_task(
                email_service.send_ban_notification, to_email=user_data["email"], reason=ban_data.reason
            )

        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "BAN_USER",
                    "resource": "users",
                    "changes": {"target_user_id": user_id_str, "reason": ban_data.reason},
                    "ip_address": request.client.host if request.client else "unknown",
                }
            )
            .execute()
        )

        await _invalidate_user_list_cache()
        return {"message": "User banned"}
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to ban user")
        raise HTTPException(status_code=500, detail="Failed to ban user")


@router.post("/users/{user_id}/unban")
@limiter.limit("5/minute")
async def unban_user(
    request: Request,
    user_id: UserIdPath,
    current_admin: Annotated[User, Depends(require_permission("users:update"))],
) -> dict[str, str]:
    """
    Unban a user.
    """
    user_id_str = str(user_id)
    try:
        admin_client = await get_async_supabase_admin_client()
        await admin_client.table("users").update({"banned_at": None}).eq("id", user_id_str).execute()
        await invalidate_user_auth_cache(user_id_str)

        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "UNBAN_USER",
                    "resource": "users",
                    "changes": {"target_user_id": user_id_str},
                    "ip_address": request.client.host if request.client else "unknown",
                }
            )
            .execute()
        )

        await _invalidate_user_list_cache()
        return {"message": "User unbanned"}
    except Exception:
        logger.error("Failed to unban user")
        raise HTTPException(status_code=500, detail="Failed to unban user")
