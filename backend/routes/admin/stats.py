import asyncio
from collections import Counter
from datetime import date, datetime, timedelta
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


def _coerce_date(value: Any) -> date | None:
    """Convert supported DB values to a plain date."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).date()
        except ValueError:
            return None
    return None


def _build_daily_series(
    rows: list[dict[str, Any]],
    field_name: str,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    counts = Counter(
        parsed_date.isoformat()
        for row in rows
        if (parsed_date := _coerce_date(row.get(field_name))) and start_date <= parsed_date <= end_date
    )

    series: list[dict[str, Any]] = []
    current = start_date
    while current <= end_date:
        key = current.isoformat()
        series.append({"date": key, "count": counts.get(key, 0)})
        current += timedelta(days=1)
    return series


def _build_monthly_series(
    rows: list[dict[str, Any]],
    field_name: str,
    year: int,
) -> list[int]:
    counts = [0] * 12
    for row in rows:
        parsed_date = _coerce_date(row.get(field_name))
        if parsed_date and parsed_date.year == year:
            counts[parsed_date.month - 1] += 1
    return counts


async def _fetch_trends_fallback(admin_client: Any, days_back: int = 30) -> dict[str, Any]:
    """Compute admin trends without relying on the RPC existing in the DB."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    start_iso = datetime.combine(start_date, datetime.min.time()).isoformat()

    user_task = admin_client.table("users").select("created_at").gte("created_at", start_iso).execute()
    photo_task = admin_client.table("cat_photos").select("uploaded_at").gte("uploaded_at", start_iso).execute()
    report_task = admin_client.table("reports").select("created_at").gte("created_at", start_iso).execute()

    user_res, photo_res, report_res = await asyncio.gather(user_task, photo_task, report_task)

    user_rows = user_res.data or []
    photo_rows = photo_res.data or []
    report_rows = report_res.data or []

    return {
        "users": _build_daily_series(user_rows, "created_at", start_date, end_date),
        "photos": _build_daily_series(photo_rows, "uploaded_at", start_date, end_date),
        "reports": _build_daily_series(report_rows, "created_at", start_date, end_date),
    }


async def _fetch_monthly_report_fallback(admin_client: Any, report_year: int) -> list[dict[str, Any]]:
    """Compute monthly dashboard data in Python when DB RPCs are stale or missing."""
    year_start = datetime(report_year, 1, 1)
    next_year_start = datetime(report_year + 1, 1, 1)
    start_iso = year_start.isoformat()
    end_iso = next_year_start.isoformat()

    users_task = (
        admin_client.table("users")
        .select("created_at")
        .gte("created_at", start_iso)
        .lt("created_at", end_iso)
        .execute()
    )
    photos_task = (
        admin_client.table("cat_photos")
        .select("uploaded_at")
        .gte("uploaded_at", start_iso)
        .lt("uploaded_at", end_iso)
        .execute()
    )
    reports_task = (
        admin_client.table("reports")
        .select("updated_at")
        .eq("status", "resolved")
        .gte("updated_at", start_iso)
        .lt("updated_at", end_iso)
        .execute()
    )
    treats_task = (
        admin_client.table("treats_transactions")
        .select("created_at,amount")
        .eq("transaction_type", "PURCHASE")
        .gte("created_at", start_iso)
        .lt("created_at", end_iso)
        .execute()
    )

    user_res, photo_res, report_res, treats_res = await asyncio.gather(
        users_task, photos_task, reports_task, treats_task
    )

    user_counts = _build_monthly_series(user_res.data or [], "created_at", report_year)
    photo_counts = _build_monthly_series(photo_res.data or [], "uploaded_at", report_year)
    report_counts = _build_monthly_series(report_res.data or [], "updated_at", report_year)

    points_earned = [0] * 12
    for row in treats_res.data or []:
        parsed_date = _coerce_date(row.get("created_at"))
        if parsed_date and parsed_date.year == report_year:
            points_earned[parsed_date.month - 1] += int(row.get("amount") or 0)

    return [
        {
            "month_timestamp": datetime(report_year, month, 1).isoformat(),
            "new_users": user_counts[month - 1],
            "new_photos": photo_counts[month - 1],
            "resolved_reports": report_counts[month - 1],
            "points_earned": points_earned[month - 1],
        }
        for month in range(1, 13)
    ]


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

        trends_data = trends_res.data or {}
        monthly_data = monthly_res.data or []

        if not trends_data:
            trends_data = await _fetch_trends_fallback(admin_client, days_back=30)
        if not monthly_data:
            monthly_data = await _fetch_monthly_report_fallback(admin_client, datetime.now().year)

        result = {
            "stats": {
                "total_users": user_res.count or 0,
                "total_photos": photo_res.count or 0,
                "pending_reports": pending_res.count or 0,
                "total_reports": total_res.count or 0,
            },
            "trends": trends_data,
            "monthly": monthly_data,
            "generated_at": datetime.now().isoformat(),
        }

        # Cache for 5 minutes
        await redis_service.set(cache_key, result, expire=300)
        return result
    except Exception as e:
        logger.warning("Dashboard summary RPC path failed; retrying with Python fallback: %s", e, exc_info=True)
        try:
            admin_client = await get_async_supabase_admin_client()
            stats_tasks = [
                admin_client.table("users").select("id", count=CountMethod.estimated).limit(1).execute(),
                admin_client.table("cat_photos").select("id", count=CountMethod.estimated).limit(1).execute(),
                admin_client.table("reports").select("id", count=CountMethod.exact).eq("status", "pending").execute(),
                admin_client.table("reports").select("id", count=CountMethod.estimated).limit(1).execute(),
            ]
            user_res, photo_res, pending_res, total_res = await asyncio.gather(*stats_tasks)
            result = {
                "stats": {
                    "total_users": user_res.count or 0,
                    "total_photos": photo_res.count or 0,
                    "pending_reports": pending_res.count or 0,
                    "total_reports": total_res.count or 0,
                },
                "trends": await _fetch_trends_fallback(admin_client, days_back=30),
                "monthly": await _fetch_monthly_report_fallback(admin_client, datetime.now().year),
                "generated_at": datetime.now().isoformat(),
            }
            await redis_service.set(cache_key, result, expire=300)
            return result
        except Exception as fallback_error:
            logger.error("Failed to fetch dashboard summary: %s", fallback_error, exc_info=True)
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
        if not trends_data:
            trends_data = await _fetch_trends_fallback(admin_client, days_back=30)
        await redis_service.set(cache_key, trends_data, expire=600)
        return trends_data
    except Exception as e:
        logger.warning("Admin trends RPC failed; using Python fallback: %s", e, exc_info=True)
        try:
            admin_client = await get_async_supabase_admin_client()
            trends_data = await _fetch_trends_fallback(admin_client, days_back=30)
            await redis_service.set(cache_key, trends_data, expire=600)
            return trends_data
        except Exception as fallback_error:
            logger.error("Failed to get trends: %s", fallback_error, exc_info=True)
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

        monthly_data = result.data or []
        if not monthly_data:
            monthly_data = await _fetch_monthly_report_fallback(admin_client, year or datetime.now().year)
        data = {"data": monthly_data, "year": year or datetime.now().year}
        await redis_service.set(cache_key, data, expire=1800)  # Cache longer
        return data
    except Exception as e:
        logger.warning("Monthly stats RPC failed; using Python fallback: %s", e, exc_info=True)
        try:
            admin_client = await get_async_supabase_admin_client()
            data = {
                "data": await _fetch_monthly_report_fallback(admin_client, year or datetime.now().year),
                "year": year or datetime.now().year,
            }
            await redis_service.set(cache_key, data, expire=1800)
            return data
        except Exception as fallback_error:
            logger.error("Failed to fetch monthly stats: %s", fallback_error, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to fetch monthly report")
