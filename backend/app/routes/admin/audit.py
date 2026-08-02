from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from postgrest.types import CountMethod

from app.dependencies import get_async_supabase_admin_client
from app.limiter import limiter
from app.logger import logger
from app.middleware.auth_middleware import require_permission
from app.routes.admin.helpers import CommonPagination, fetch_cached_admin_list
from app.schemas.user import User

router = APIRouter()


def _audit_logs_cache_key(limit: int, offset: int, user_id: str | None, action: str | None) -> str:
    return f"admin_audit_logs:{limit}:{offset}:{user_id or '_'}:{action or '_'}"


@router.get("/audit-logs", response_model=dict[str, Any])
@limiter.limit("60/minute")
async def list_audit_logs(
    request: Request,
    pagination: Annotated[CommonPagination, Depends()],
    user_id: str | None = None,
    action: str | None = None,
    cache_bust: Annotated[str | None, Query()] = None,
    current_admin: Annotated[User | None, Depends(require_permission("audit:read"))] = None,
) -> dict[str, Any]:
    """
    List audit logs.

    Raises:
        HTTPException: 500 - If fetching audit logs fails.
    """
    try:
        cache_key = _audit_logs_cache_key(pagination.limit, pagination.offset, user_id, action)
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("audit_logs")
            .select(
                "id, user_id, action, resource, changes, ip_address, user_agent, created_at, users(email, name)",
                count=CountMethod.exact,
            )
            .range(pagination.offset, pagination.offset + pagination.limit - 1)
            .order("created_at", desc=True)
        )

        if user_id:
            query = query.eq("user_id", user_id)

        if action:
            query = query.eq("action", action)

        return await fetch_cached_admin_list(cache_key, bool(cache_bust), 30, query)
    except Exception as e:
        logger.error("Failed to list audit logs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")
