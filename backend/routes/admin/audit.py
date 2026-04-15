from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from postgrest.types import CountMethod

from dependencies import get_async_supabase_admin_client
from limiter import limiter
from logger import logger
from middleware.auth_middleware import require_permission
from schemas.user import User
from services.redis_service import redis_service

router = APIRouter()


def _audit_logs_cache_key(limit: int, offset: int, user_id: str | None, action: str | None) -> str:
    return f"admin_audit_logs:{limit}:{offset}:{user_id or '_'}:{action or '_'}"


@router.get("/audit-logs", response_model=dict[str, Any])
@limiter.limit("60/minute")
async def list_audit_logs(
    request: Request,
    limit: int = 50,
    offset: int = 0,
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
        cache_key = _audit_logs_cache_key(limit, offset, user_id, action)
        if not cache_bust:
            cached = await redis_service.get(cache_key)
            if cached is not None:
                return cached

        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("audit_logs")
            .select(
                "id, user_id, action, resource, changes, ip_address, user_agent, created_at, users(email, name)",
                count=CountMethod.exact,
            )
            .range(offset, offset + limit - 1)
            .order("created_at", desc=True)
        )

        if user_id:
            query = query.eq("user_id", user_id)

        if action:
            query = query.eq("action", action)

        result = await query.execute()
        response = {"data": result.data, "total": result.count}
        # Keep TTL short because audit logs are append-heavy and updated from many routes.
        if not cache_bust:
            await redis_service.set(cache_key, response, expire=30)
        return response
    except Exception as e:
        logger.error("Failed to list audit logs: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")
