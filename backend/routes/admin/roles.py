import asyncio
from collections import Counter
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from constants.admin_permissions import ALL_PERMISSION_CODES, normalize_permission_code
from dependencies import get_async_supabase_admin_client
from logger import logger
from middleware.auth_middleware import invalidate_user_auth_cache, require_permission
from schemas.user import User
from services.redis_service import redis_service

router = APIRouter()
ROLES_CACHE_KEY = "admin_roles_list_v2"
PERMISSIONS_CACHE_KEY = "admin_permissions_list"


def _role_permissions_cache_key(role_id: str) -> str:
    return f"admin_role_permissions:{role_id}"


async def _invalidate_role_user_auth_caches(admin_client: Any, role_id: str) -> None:
    """Clear cached auth snapshots for users assigned to a role after permission changes."""
    try:
        users_res = await admin_client.table("users").select("id").eq("role_id", role_id).execute()
        user_ids = [row["id"] for row in cast(list[dict[str, Any]], users_res.data or []) if row.get("id")]
        if not user_ids:
            return

        await asyncio.gather(*(invalidate_user_auth_cache(cast(str, user_id)) for user_id in user_ids))
    except Exception:
        logger.warning("Failed to invalidate auth cache for users assigned to a role")


class RolePermissionUpdate(BaseModel):
    role_id: str
    permission_ids: list[str]


@router.get("")
async def list_roles(
    current_admin: Annotated[User, Depends(require_permission("roles:read"))],
) -> list[dict[str, Any]]:
    """List all available roles."""
    cached = await redis_service.get(ROLES_CACHE_KEY)
    if cached:
        return cast(list[dict[str, Any]], cached)
    try:
        admin_client = await get_async_supabase_admin_client()
        roles_query = admin_client.table("roles").select("id, name, description, created_at").execute()
        permissions_query = admin_client.table("role_permissions").select("role_id").execute()
        roles_res, permissions_res = await asyncio.gather(roles_query, permissions_query)

        permission_counts = Counter(
            row["role_id"] for row in cast(list[dict[str, Any]], permissions_res.data or []) if row.get("role_id")
        )
        roles = []
        for row in cast(list[dict[str, Any]], roles_res.data or []):
            role = dict(row)
            role["permission_count"] = permission_counts.get(role["id"], 0)
            roles.append(role)

        await redis_service.set(ROLES_CACHE_KEY, roles, expire=600)  # 10 minutes
        return roles
    except Exception as e:
        logger.error("Failed to list roles: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch roles")


@router.get("/permissions")
async def list_permissions(
    current_admin: Annotated[User, Depends(require_permission("roles:manage"))],
) -> list[dict[str, Any]]:
    """List all available permissions."""
    cached = await redis_service.get(PERMISSIONS_CACHE_KEY)
    if cached:
        return cast(list[dict[str, Any]], cached)
    try:
        admin_client = await get_async_supabase_admin_client()
        res = await admin_client.table("permissions").select("id,code,description,group").execute()
        normalized_permissions: dict[str, dict[str, Any]] = {}
        for row in cast(list[dict[str, Any]], res.data or []):
            original_code = cast(str, row["code"])
            normalized_code = normalize_permission_code(original_code) or original_code
            normalized_row = {
                "id": row["id"],
                "code": normalized_code,
                "description": row.get("description"),
                "group": row.get("group"),
            }

            existing = normalized_permissions.get(normalized_code)
            if existing is None or original_code == normalized_code:
                normalized_permissions[normalized_code] = normalized_row

        ordered_codes = [code for code in ALL_PERMISSION_CODES if code in normalized_permissions]
        remaining_codes = sorted(code for code in normalized_permissions if code not in ordered_codes)
        permissions = [normalized_permissions[code] for code in [*ordered_codes, *remaining_codes]]
        await redis_service.set(PERMISSIONS_CACHE_KEY, permissions, expire=600)  # 10 minutes
        return permissions
    except Exception as e:
        logger.error("Failed to list permissions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch permissions")


@router.get("/{role_id}/permissions")
async def get_role_permissions(
    role_id: str,
    current_admin: Annotated[User, Depends(require_permission("roles:read"))],
) -> list[str]:
    """Get permissions assigned to a specific role."""
    cache_key = _role_permissions_cache_key(role_id)
    cached = await redis_service.get(cache_key)
    if cached:
        return cast(list[str], cached)
    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.table("role_permissions").select("permission_id").eq("role_id", role_id).execute()
        permissions = [r["permission_id"] for r in cast(list[dict[str, Any]], result.data or [])]
        await redis_service.set(cache_key, permissions, expire=600)
        return permissions
    except Exception as e:
        logger.error("Failed to fetch role permissions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch role permissions")


@router.post("/{role_id}/permissions")
async def update_role_permissions(
    role_id: str,
    request: Request,
    data: RolePermissionUpdate,
    current_admin: Annotated[User, Depends(require_permission("roles:manage"))],
) -> dict[str, str]:
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

        # Invalidate role/permission caches so next request gets fresh data
        await redis_service.delete(ROLES_CACHE_KEY)
        await redis_service.delete(PERMISSIONS_CACHE_KEY)
        await redis_service.delete(_role_permissions_cache_key(role_id))
        await _invalidate_role_user_auth_caches(admin_client, role_id)

        return {"message": "Role permissions updated successfully"}
    except Exception as e:
        logger.error("Failed to update role permissions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update role permissions")
