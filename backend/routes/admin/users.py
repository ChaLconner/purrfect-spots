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
from services.token_service import get_token_service

router = APIRouter()

UserIdPath = Annotated[UUID, Path(title="The ID of the user", description="Must be a valid UUID")]
RoleIdPath = Annotated[UUID, Path(title="The ID of the role", description="Must be a valid UUID")]


def _invalidate_auth_cache_for_users(user_ids: list[str]) -> None:
    for user_id in user_ids:
        invalidate_user_auth_cache(user_id)


async def _invalidate_banned_user_auth_state(user_ids: list[str], reason: str) -> None:
    unique_user_ids = list(dict.fromkeys(user_ids))
    token_service = await get_token_service()

    for user_id in unique_user_ids:
        invalidate_user_auth_cache(user_id)
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
            query = query.text_search("search_vector", f"'{search}'")

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

        return {"data": processed_data, "total": total_count}
    except Exception as e:
        logger.error(f"Failed to list users: {str(e)}")
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

        return {"message": f"Successfully banned {len(target_uids)} users.", "skipped": skipped_admins}
    except Exception as e:
        logger.error(f"Bulk ban failed: {e}")
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
        _invalidate_auth_cache_for_users(user_ids_str)

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

        return {"message": f"Successfully unbanned {len(user_ids_str)} users."}
    except Exception as e:
        logger.error(f"Bulk unban failed: {e}")
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
        invalidate_user_auth_cache(user_id_str)

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
        invalidate_user_auth_cache(user_id_str)

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
        invalidate_user_auth_cache(user_id_str)

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
        check = await admin_client.table("users").select("email, roles(name)").eq("id", user_id_str).single().execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = check.data
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
        invalidate_user_auth_cache(user_id_str)

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

        return {"message": "User unbanned"}
    except Exception:
        logger.error("Failed to unban user")
        raise HTTPException(status_code=500, detail="Failed to unban user")


import csv
import io
import json

from fastapi.responses import StreamingResponse


@router.get("/export")
@limiter.limit("5/minute")
async def export_users(
    request: Request,
    format: str = "csv",
    current_admin: Annotated[User, Depends(require_permission("users:read"))] = None,
):
    """
    Export all user data to CSV or JSON.
    """

    async def user_generator():
        try:
            admin_client = await get_async_supabase_admin_client()
            batch_size = 1000
            offset = 0
            first_batch = True
            fieldnames = ["id", "email", "name", "treat_balance", "is_pro", "created_at", "banned_at"]

            if format.lower() == "json":
                yield "["
                while True:
                    result = (
                        await admin_client.table("users")
                        .select(", ".join(fieldnames))
                        .range(offset, offset + batch_size - 1)
                        .execute()
                    )
                    batch_data = result.data
                    if not batch_data:
                        break

                    for i, row in enumerate(batch_data):
                        # Simple manual JSON chunking for speed
                        sep = "" if first_batch and i == 0 else ","
                        yield sep + json.dumps(row, default=str)

                    first_batch = False
                    if len(batch_data) < batch_size:
                        break
                    offset += batch_size
                yield "]"
            else:
                # CSV Export
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames)

                while True:
                    result = (
                        await admin_client.table("users")
                        .select(", ".join(fieldnames))
                        .range(offset, offset + batch_size - 1)
                        .execute()
                    )
                    batch_data = result.data
                    if not batch_data:
                        break

                    if first_batch:
                        writer.writeheader()

                    for row in batch_data:
                        # Flatten for CSV consistent with utils
                        flat_row = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in row.items()}
                        writer.writerow(flat_row)

                    # Get value and clear buffer for next batch
                    yield output.getvalue()
                    output.seek(0)
                    output.truncate(0)

                    first_batch = False
                    if len(batch_data) < batch_size:
                        break
                    offset += batch_size
        except Exception as gen_err:
            logger.error("Error in user_generator: %s", gen_err)
            raise

    try:
        media_type = "application/json" if format.lower() == "json" else "text/csv"
        filename = f"users_export.{'json' if format.lower() == 'json' else 'csv'}"

        return StreamingResponse(
            user_generator(), media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error("Export failed: %s", e)
        raise HTTPException(status_code=500, detail="Export failed")
