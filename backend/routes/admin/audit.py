from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from postgrest.types import CountMethod

from dependencies import get_async_supabase_admin_client
from limiter import limiter
from logger import logger
from middleware.auth_middleware import require_permission
from user_models.user import User

router = APIRouter()


@router.get("/audit-logs", response_model=dict[str, Any])
@limiter.limit("60/minute")
async def list_audit_logs(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    user_id: str | None = None,
    action: str | None = None,
    current_admin: User = Depends(require_permission("system:audit_logs")),
) -> dict[str, Any]:
    """
    List audit logs.
    """
    try:
        admin_client = await get_async_supabase_admin_client()
        query = (
            admin_client.table("audit_logs")
            .select("*, users(email, name)", count=CountMethod.exact)
            .range(offset, offset + limit - 1)
            .order("created_at", desc=True)
        )

        if user_id:
            query = query.eq("user_id", user_id)

        if action:
            query = query.eq("action", action)

        result = await query.execute()
        return {"data": result.data, "total": result.count}
    except Exception as e:
        logger.error(f"Failed to list audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")
