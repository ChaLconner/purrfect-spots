import asyncio
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from postgrest.types import CountMethod

from dependencies import get_async_supabase_admin_client
from limiter import limiter
from logger import logger
from middleware.auth_middleware import require_permission
from schemas.user import User

router = APIRouter()

from services.redis_service import redis_service

# Legacy stats cache removed


@router.get("/summary/")
@limiter.limit("10/minute")
async def get_dashboard_summary(
    request: Request,
    current_admin: Annotated[User | None, Depends(require_permission("system:stats"))] = None,
) -> dict[str, Any]:
    """
    Consolidated dashboard summary: stats, trends, and monthly data.
    Uses Redis for distributed caching.
    """
    cache_key = "admin_dashboard_summary_v1"
    cached = await redis_service.get(cache_key)
    if cached:
        return cached

    try:
        admin_client = await get_async_supabase_admin_client()

        # Parallel fetch for all dashboard components
        stats_tasks = [
            admin_client.table("users").select("id", count=CountMethod.estimated).limit(1).execute(),
            admin_client.table("cat_photos").select("id", count=CountMethod.estimated).limit(1).execute(),
            admin_client.table("reports").select("id", count=CountMethod.exact).eq("status", "pending").execute(),
            admin_client.table("reports").select("id", count=CountMethod.estimated).limit(1).execute(),
        ]
        trends_task = admin_client.rpc("get_admin_trends", {"days_back": 30}).execute()
        monthly_task = admin_client.rpc("get_monthly_report", {"report_year": datetime.now().year}).execute()

        all_res = await asyncio.gather(*stats_tasks, trends_task, monthly_task)
        user_res, photo_res, pending_res, total_res, trends_res, monthly_res = all_res

        result = {
            "stats": {
                "total_users": user_res.count or 0,
                "total_photos": photo_res.count or 0,
                "pending_reports": pending_res.count or 0,
                "total_reports": total_res.count or 0,
            },
            "trends": trends_res.data or {},
            "monthly": monthly_res.data or [],
            "generated_at": datetime.now().isoformat(),
        }

        # Cache for 5 minutes
        await redis_service.set(cache_key, result, expire=300)
        return result
    except Exception as e:
        logger.error(f"Failed to fetch dashboard summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard summary")


@router.get("/stats/trends/")
@limiter.limit("5/minute")
async def get_system_trends(
    request: Request,
    current_admin: Annotated[User | None, Depends(require_permission("system:stats"))] = None,
) -> dict[str, Any]:
    """
    Get 30-day activity trends.
    """
    cache_key = "admin_trends_v1"
    cached = await redis_service.get(cache_key)
    if cached:
        return cached

    try:
        admin_client = await get_async_supabase_admin_client()
        result = await admin_client.rpc("get_admin_trends", {"days_back": 30}).execute()

        trends_data = result.data or {}
        await redis_service.set(cache_key, trends_data, expire=600)
        return trends_data
    except Exception as e:
        logger.error(f"Failed to get trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch activity trends")


@router.get("/stats/monthly/")
@limiter.limit("5/minute")
async def get_monthly_stats(
    request: Request,
    year: int | None = None,
    current_admin: Annotated[User | None, Depends(require_permission("system:stats"))] = None,
) -> dict[str, Any]:
    """
    Get monthly system performance report.
    """
    cache_key = f"admin_monthly_{year or datetime.now().year}"
    cached = await redis_service.get(cache_key)
    if cached:
        return cached

    try:
        admin_client = await get_async_supabase_admin_client()
        params = {"report_year": year} if year else {}
        result = await admin_client.rpc("get_monthly_report", params).execute()

        data = {"data": result.data or [], "year": year or datetime.now().year}
        await redis_service.set(cache_key, data, expire=1800)  # Cache longer
        return data
    except Exception as e:
        logger.error(f"Failed to fetch monthly stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch monthly report")
