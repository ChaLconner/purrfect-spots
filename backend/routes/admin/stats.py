from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request
from postgrest.types import CountMethod

from dependencies import get_async_supabase_admin_client
from limiter import limiter
from logger import logger
from middleware.auth_middleware import require_permission
from user_models.user import User

router = APIRouter()

# Simple in-memory cache: (data, expiration_timestamp)
_stats_cache: dict[str, tuple[dict[str, Any], datetime]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


@router.get("/stats")
@limiter.limit("20/minute")
async def get_system_stats(
    request: Request, current_admin: User = Depends(require_permission("users:read"))
) -> dict[str, Any]:
    """
    Get basic system statistics.
    Optimized to use estimated counts for large tables.
    Cached for 5 minutes.
    """
    # Check cache
    cache_key = "admin_stats"
    if cache_key in _stats_cache:
        data, expires_at = _stats_cache[cache_key]
        if datetime.now() < expires_at:
            return data

    try:
        admin_client = await get_async_supabase_admin_client()

        # User count - Use estimated for performance
        user_count_res = await admin_client.table("users").select("id", count=CountMethod.estimated).limit(1).execute()
        user_count = user_count_res.count

        # Photo count - Use estimated for performance
        photo_count_res = (
            await admin_client.table("cat_photos").select("id", count=CountMethod.estimated).limit(1).execute()
        )
        photo_count = photo_count_res.count

        # Reports - Pending count is important to be exact
        pending_reports_res = (
            await admin_client.table("reports").select("id", count=CountMethod.exact).eq("status", "pending").execute()
        )
        pending_reports = pending_reports_res.count

        total_reports_res = (
            await admin_client.table("reports").select("id", count=CountMethod.estimated).limit(1).execute()
        )
        total_reports = total_reports_res.count

        result = {
            "total_users": user_count,
            "total_photos": photo_count,
            "pending_reports": pending_reports,
            "total_reports": total_reports,
            "generated_at": datetime.now().isoformat(),
        }

        # Update cache
        _stats_cache[cache_key] = (result, datetime.now() + timedelta(seconds=CACHE_TTL_SECONDS))

        return result
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        # Return fallback stats rather than 500ing the whole dashboard
        return {"total_users": 0, "total_photos": 0, "pending_reports": 0, "total_reports": 0, "error": str(e)}
