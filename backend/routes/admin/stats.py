from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from postgrest.types import CountMethod

from dependencies import get_async_supabase_admin_client
from limiter import limiter
from logger import logger
from middleware.auth_middleware import require_permission
from schemas.user import User

router = APIRouter()

# Simple in-memory cache: (data, expiration_timestamp)
_stats_cache: dict[str, tuple[dict[str, Any], datetime]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


@router.get("/stats")
@limiter.limit("20/minute")
async def get_system_stats(
    request: Request,
    current_admin: Annotated[User | None, Depends(require_permission("system:stats"))] = None,
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
        logger.error("Failed to get stats", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch system statistics")

@router.get("/stats/trends")
@limiter.limit("5/minute")
async def get_system_trends(
    request: Request,
    current_admin: Annotated[User | None, Depends(require_permission("system:stats"))] = None,
) -> dict[str, Any]:
    """
    Get 30-day activity trends for users, photos, and reports.
    Queries the last 30 days of data and groups counts by date.
    """
    cache_key = "admin_trends"
    # Check cache
    if cache_key in _stats_cache:
        data, expires_at = _stats_cache[cache_key]
        if datetime.now() < expires_at:
            return data

    try:
        admin_client = await get_async_supabase_admin_client()
        
        # Call the optimized RPC function
        result = await admin_client.rpc("get_admin_trends", {"days_back": 30}).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to generate trends data")

        trends_data = result.data

        # Update cache (10 minutes)
        _stats_cache[cache_key] = (trends_data, datetime.now() + timedelta(minutes=10))
        
        return trends_data
        
    except Exception as e:
        logger.error(f"Failed to get trends: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Failed to fetch activity trends")

@router.get("/stats/monthly")
@limiter.limit("5/minute")
async def get_monthly_stats(
    request: Request,
    year: int | None = None,
    current_admin: Annotated[User | None, Depends(require_permission("system:stats"))] = None,
) -> dict[str, Any]:
    """
    Get monthly system performance report.
    """
    try:
        admin_client = await get_async_supabase_admin_client()
        params = {}
        if year:
            params["report_year"] = year
            
        result = await admin_client.rpc("get_monthly_report", params).execute()
        
        return {"data": result.data, "year": year or datetime.now().year}
    except Exception as e:
        logger.error(f"Failed to fetch monthly stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch monthly report")

