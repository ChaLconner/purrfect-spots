from datetime import datetime
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Request
from postgrest.types import CountMethod

from dependencies import (
    get_async_supabase_admin_client,
    get_email_service,
)
from limiter import limiter
from logger import logger, sanitize_log_value
from middleware.auth_middleware import require_permission
from schemas.admin_schemas import RoleUpdateAdmin, UserBan, UserUpdateAdmin
from services.email_service import EmailService
from user_models.user import User

router = APIRouter()

UserIdPath = Annotated[UUID, Path(title="The ID of the user", description="Must be a valid UUID")]
RoleIdPath = Annotated[UUID, Path(title="The ID of the role", description="Must be a valid UUID")]


@router.get("/users", response_model=dict[str, Any])
@limiter.limit("60/minute")
async def list_users(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
    current_admin: User = Depends(require_permission("users:read")),
) -> dict[str, Any]:
    """
    List all users with pagination, search, and sorting.
    Only accessible by admins with users:read permission.
    """
    try:
        admin_client = await get_async_supabase_admin_client()
        # Join with roles table to get the current role name reliably
        # NOTE: count="exact" is NOT passed here because the async Supabase client
        # internally uses a HEAD request for count which is unsupported in this version.
        # We run a separate lightweight count query below instead.
        query = admin_client.table("users").select("*, roles(name)").range(offset, offset + limit - 1)

        # Validate sort_by to prevent injection or errors
        allowed_sort_fields = ["created_at", "email", "name", "treat_balance", "last_sign_in_at"]
        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        # Apply sorting
        query = query.order(sort_by, desc=(order.lower() == "desc"))

        if search:
            # Use ilike for case-insensitive search
            # Optimize: trailing wildcard only would be faster if indexed properly, but user expects full search
            # For strict performance, we'd use Full Text Search, but this is a quick win.
            query = query.or_(f"email.ilike.%{search}%,name.ilike.%{search}%")

        result = await query.execute()

        # Map the results to ensure 'role' field contains the role name from the join
        processed_data = []
        for user in result.data:
            user_copy = user.copy()
            roles_data = user_copy.pop("roles", None)
            if roles_data and isinstance(roles_data, dict):
                user_copy["role"] = roles_data.get("name", user_copy.get("role", "user"))
            elif not user_copy.get("role"):
                user_copy["role"] = "user"
            processed_data.append(user_copy)

        # Get total count via a separate lightweight query
        # (count="exact" on a select("id") does NOT trigger the broken HEAD path)
        try:
            count_query = admin_client.table("users").select("id", count=CountMethod.exact)
            if search:
                count_query = count_query.or_(f"email.ilike.%{search}%,name.ilike.%{search}%")
            count_result = await count_query.execute()
            total_count = count_result.count or len(processed_data)
        except Exception as count_err:
            logger.warning("Count query failed, using data length: %s", count_err)
            total_count = len(processed_data)

        return {"data": processed_data, "total": total_count}
    except Exception:
        logger.error("Failed to list users")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@router.delete("/users/{user_id}")
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: UserIdPath,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(require_permission("users:delete")),
    email_service: EmailService = Depends(get_email_service),
) -> dict[str, str]:
    """
    Permanently delete a user and their data.
    """
    user_id_str = str(user_id)
    try:
        admin_client = await get_async_supabase_admin_client()

        # Check if user exists and get role
        check = await admin_client.table("users").select("email, roles(name)").eq("id", user_id_str).single().execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = check.data
        # Get role name safely
        role_info = user_data.get("roles")
        role_name = (role_info.get("name") if role_info else "user").lower()

        if role_name == "admin" or role_name == "super_admin":
            # Prevent deleting other admins via API
            raise HTTPException(status_code=400, detail="Cannot delete an admin user")

        # Send email before deletion
        if user_data.get("email"):
            background_tasks.add_task(
                email_service.send_account_deletion_notification,
                to_email=user_data["email"],
                reason="Administrative Action",
            )

        await admin_client.auth.admin.delete_user(user_id_str)

        # Log action
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "DELETE_USER",
                    "resource": "users",
                    "changes": {"target_user_id": user_id_str, "email": user_data.get("email")},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        return {"message": f"User {user_id_str} deleted successfully"}

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
    current_admin: User = Depends(require_permission("users:write")),
) -> dict[str, Any]:
    """
    Update a user's profile as an admin.
    """
    user_id_str = str(user_id)
    try:
        admin_client = await get_async_supabase_admin_client()

        filtered_data = update_data.model_dump(exclude_unset=True)

        if not filtered_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update")

        result = await admin_client.table("users").update(filtered_data).eq("id", user_id_str).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        return cast(dict[str, Any], result.data[0])
    except Exception as e:
        logger.error("Failed to update user profile %s: %s", sanitize_log_value(user_id_str), e)
        raise HTTPException(status_code=500, detail="Failed to update user profile")


@router.get("/roles")
@limiter.limit("60/minute")
async def list_roles(
    request: Request, current_admin: User = Depends(require_permission("roles:read"))
) -> list[dict[str, Any]]:
    """
    List all available roles.
    """
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("roles").select("*").order("name").execute()
        return result.data
    except Exception:
        logger.error("Failed to list roles")
        raise HTTPException(status_code=500, detail="Failed to fetch roles")


@router.put("/users/{user_id}/role")
@limiter.limit("20/minute")
async def update_user_role(
    request: Request,
    user_id: UserIdPath,
    role_data: RoleUpdateAdmin,
    current_admin: User = Depends(require_permission("users:update")),
) -> dict[str, Any]:
    """
    Update a user's role.
    """
    user_id_str = str(user_id)
    # The actual schema validation handles role_id format if we set it as UUID,
    # but here we cast assuming it's provided via the body model.
    role_id_str = str(role_data.role_id) if role_data.role_id else None
    if not role_id_str:
        raise HTTPException(status_code=400, detail="role_id is required")

    try:
        admin_client = await get_async_supabase_admin_client()

        # Verify role exists
        role_check = await admin_client.table("roles").select("name").eq("id", role_id_str).single().execute()
        if not role_check.data:
            raise HTTPException(status_code=404, detail="Role not found")

        role_name = role_check.data.get("name")

        # Update role_id
        result = await admin_client.table("users").update({"role_id": role_id_str}).eq("id", user_id_str).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")

        # Log action
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "UPDATE_ROLE",
                    "resource": "users",
                    "changes": {"target_user_id": user_id_str, "new_role": role_name, "new_role_id": role_id_str},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        return cast(dict[str, Any], result.data[0])

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to update user role %s", sanitize_log_value(user_id_str))
        raise HTTPException(status_code=500, detail="Failed to update user role")


@router.post("/users/{user_id}/ban")
@limiter.limit("5/minute")
async def ban_user(
    request: Request,
    user_id: UserIdPath,
    ban_data: UserBan,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(require_permission("users:update")),
    email_service: EmailService = Depends(get_email_service),
) -> dict[str, str]:
    """
    Ban a user.
    """
    user_id_str = str(user_id)

    try:
        admin_client = await get_async_supabase_admin_client()

        # Check user exists & not admin
        check = await admin_client.table("users").select("email, roles(name)").eq("id", user_id_str).single().execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="User not found")

        user_data = check.data
        role_info = user_data.get("roles")
        role_name = (role_info.get("name") if role_info else "user").lower()

        if role_name in ("admin", "super_admin"):
            raise HTTPException(status_code=400, detail="Cannot ban an admin user")

        # Update banned_at
        await (
            admin_client.table("users")
            .update({"banned_at": datetime.now().isoformat()})
            .eq("id", user_id_str)
            .execute()
        )

        # Send email
        if user_data.get("email"):
            background_tasks.add_task(
                email_service.send_ban_notification, to_email=user_data["email"], reason=ban_data.reason
            )

        # Log Audit
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "BAN_USER",
                    "resource": "users",
                    "changes": {"target_user_id": user_id_str, "reason": ban_data.reason},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        return {"message": f"User {user_id_str} banned successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to ban user %s", sanitize_log_value(user_id_str))
        raise HTTPException(status_code=500, detail="Failed to ban user")


@router.post("/users/{user_id}/unban")
@limiter.limit("5/minute")
async def unban_user(
    request: Request,
    user_id: UserIdPath,
    background_tasks: BackgroundTasks,
    current_admin: User = Depends(require_permission("users:update")),
    email_service: EmailService = Depends(get_email_service),
) -> dict[str, str]:
    """
    Unban a user.
    """
    user_id_str = str(user_id)

    try:
        admin_client = await get_async_supabase_admin_client()

        # Check user exists
        check = await admin_client.table("users").select("email").eq("id", user_id_str).single().execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="User not found")

        # Update banned_at to NULL
        await admin_client.table("users").update({"banned_at": None}).eq("id", user_id_str).execute()

        # Log Audit
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "UNBAN_USER",
                    "resource": "users",
                    "changes": {"target_user_id": user_id_str},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        # Optional: Send email notification for unban? (Not implemented in EmailService currently, skipping)

        return {"message": f"User {user_id_str} unbanned successfully"}
    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to unban user %s", sanitize_log_value(user_id_str))
        raise HTTPException(status_code=500, detail="Failed to unban user")
