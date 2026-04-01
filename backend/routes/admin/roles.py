from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from dependencies import get_async_supabase_admin_client
from logger import logger
from middleware.auth_middleware import require_permission
from schemas.user import User

router = APIRouter()


class RolePermissionUpdate(BaseModel):
    role_id: str
    permission_ids: list[str]


@router.get("")
async def list_roles(
    current_admin: Annotated[User, Depends(require_permission("roles:read"))] = None,
):
    """List all available roles."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("roles").select("*").execute()
        return result.data
    except Exception as e:
        logger.error("Failed to list roles: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch roles")


@router.get("/permissions")
async def list_permissions(
    current_admin: Annotated[User, Depends(require_permission("roles:manage"))] = None,
):
    """List all available permissions."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("permissions").select("*").order("group").execute()
        return result.data
    except Exception as e:
        logger.error("Failed to list permissions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch permissions")


@router.get("/{role_id}/permissions")
async def get_role_permissions(
    role_id: str,
    current_admin: Annotated[User, Depends(require_permission("roles:read"))] = None,
):
    """Get permissions assigned to a specific role."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("role_permissions").select("permission_id").eq("role_id", role_id).execute()
        return [r["permission_id"] for r in result.data]
    except Exception as e:
        logger.error("Failed to fetch role permissions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch role permissions")


@router.post("/{role_id}/permissions")
async def update_role_permissions(
    role_id: str,
    request: Request,
    data: RolePermissionUpdate,
    current_admin: Annotated[User, Depends(require_permission("roles:manage"))] = None,
):
    """Update permissions for a specific role (Sync)."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # 1. Delete existing
        await admin_client.table("role_permissions").delete().eq("role_id", role_id).execute()

        # 2. Insert new
        if data.permission_ids:
            inserts = [{"role_id": role_id, "permission_id": pid} for pid in data.permission_ids]
            await admin_client.table("role_permissions").insert(inserts).execute()

        # Log Audit
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "UPDATE_ROLE_PERMISSIONS",
                    "resource": "roles",
                    "changes": {"role_id": role_id, "new_permissions": data.permission_ids},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        return {"message": "Role permissions updated successfully"}
    except Exception as e:
        logger.error("Failed to update role permissions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update role permissions")
