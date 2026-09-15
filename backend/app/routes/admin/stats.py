import asyncio
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from postgrest.types import CountMethod

from app.dependencies import get_async_supabase_admin_client
from app.limiter import limiter
from app.logger import logger
from app.middleware.auth_middleware import require_permission
from app.routes.admin.helpers import ADMIN_ERROR_RESPONSES
from app.schemas.user import User

router = APIRouter()

from app.services.redis_service import redis_service

# Legacy stats cache removed
MONTHLY_FALLBACK_POINTS_SUPPORTED = False


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
    """Compute trends with three bounded range queries, not one query per day."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)

    async def fetch_rows(table: str, field: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        query = (
            admin_client.table(table)
            .select(field)
            .gte(field, datetime.combine(start_date, datetime.min.time()).isoformat())
            .lt(field, (datetime.combine(end_date, datetime.min.time()) + timedelta(days=1)).isoformat())
        )
        for key, value in (filters or {}).items():
            query = query.eq(key, value)
        result = await query.execute()
        rows = result.data
        if isinstance(rows, list):
            return cast(list[dict[str, Any]], rows)
        # Some legacy clients expose only a bounded count. Keep degraded
        # fallback useful without issuing one query per day/month.
        count = getattr(result, "count", None)
        if isinstance(count, int) and count > 0:
            return [{field: start_date.isoformat()} for _ in range(count)]
        return []

    users, photos, reports = await asyncio.gather(
        fetch_rows("users", "created_at"),
        fetch_rows("cat_photos", "uploaded_at"),
        fetch_rows("reports", "created_at"),
    )
    return {
        "users": _build_daily_series(users, "created_at", start_date, end_date),
        "photos": _build_daily_series(photos, "uploaded_at", start_date, end_date),
        "reports": _build_daily_series(reports, "created_at", start_date, end_date),
    }


async def _fetch_monthly_report_fallback(admin_client: Any, report_year: int) -> list[dict[str, Any]]:
    """Compute monthly dashboard data with three bounded year queries."""
    year_start = datetime(report_year, 1, 1)
    year_end = datetime(report_year + 1, 1, 1)

    async def fetch_rows(table: str, field: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        query = (
            admin_client.table(table).select(field).gte(field, year_start.isoformat()).lt(field, year_end.isoformat())
        )
        for key, value in (filters or {}).items():
            query = query.eq(key, value)
        result = await query.execute()
        rows = result.data
        if isinstance(rows, list):
            return cast(list[dict[str, Any]], rows)
        count = getattr(result, "count", None)
        if isinstance(count, int) and count > 0:
            return [{field: year_start.isoformat()} for _ in range(count)]
        return []

    users, photos, reports = await asyncio.gather(
        fetch_rows("users", "created_at"),
        fetch_rows("cat_photos", "uploaded_at"),
        fetch_rows("reports", "updated_at", {"status": "resolved"}),
    )
    user_counts = _build_monthly_series(users, "created_at", report_year)
    photo_counts = _build_monthly_series(photos, "uploaded_at", report_year)
    report_counts = _build_monthly_series(reports, "updated_at", report_year)

    return [
        {
            "month_timestamp": datetime(report_year, month, 1).isoformat(),
            "new_users": user_counts[month - 1],
            "new_photos": photo_counts[month - 1],
            "resolved_reports": report_counts[month - 1],
            "points_earned": 0,
            "points_earned_degraded": not MONTHLY_FALLBACK_POINTS_SUPPORTED,
        }
        for month in range(1, 13)
    ]


def _dashboard_result(
    total_users: int,
    total_photos: int,
    pending_reports: int,
    total_reports: int,
    trends: dict[str, Any],
    monthly: list[Any],
) -> dict[str, Any]:
    return {
        "stats": {
            "total_users": total_users,
            "total_photos": total_photos,
            "pending_reports": pending_reports,
            "total_reports": total_reports,
        },
        "trends": trends,
        "monthly": monthly,
        "generated_at": datetime.now().isoformat(),
    }


async def _fetch_dashboard_summary_rpc(admin_client: Any) -> dict[str, Any]:
    stats_tasks = [
        admin_client.table("users").select("id", count=CountMethod.exact).limit(1).execute(),
        admin_client.table("cat_photos").select("id", count=CountMethod.exact).limit(1).execute(),
        admin_client.table("reports").select("id", count=CountMethod.exact).eq("status", "pending").execute(),
        admin_client.table("reports").select("id", count=CountMethod.exact).limit(1).execute(),
    ]
    all_res = await asyncio.gather(
        *stats_tasks,
        admin_client.rpc("get_admin_trends", {"days_back": 30}).execute(),
        admin_client.rpc("get_monthly_report", {"report_year": datetime.now().year}).execute(),
    )
    user_res, photo_res, pending_res, total_res, trends_res, monthly_res = all_res
    trends_data = cast(dict[str, Any], trends_res.data or {})
    monthly_data = cast(list[Any], monthly_res.data or [])
    if not trends_data:
        trends_data = await _fetch_trends_fallback(admin_client, days_back=30)
    if not monthly_data:
        monthly_data = await _fetch_monthly_report_fallback(admin_client, datetime.now().year)
    return _dashboard_result(
        user_res.count or 0,
        photo_res.count or 0,
        pending_res.count or 0,
        total_res.count or 0,
        trends_data,
        monthly_data,
    )


async def _safe_dashboard_count(
    admin_client: Any,
    table: str,
    count_method: CountMethod = CountMethod.exact,
    filters: dict[str, Any] | None = None,
) -> int:
    try:
        query = admin_client.table(table).select("id", count=count_method)
        for key, value in (filters or {}).items():
            query = query.eq(key, value)
        result = await query.limit(1).execute()
        return result.count or 0
    except Exception as exc:
        logger.error("Fallback count failed for %s: %s", table, exc)
        return 0


async def _safe_dashboard_trends(admin_client: Any) -> dict[str, Any]:
    try:
        return await _fetch_trends_fallback(admin_client, days_back=30)
    except Exception as exc:
        logger.error("Fallback trends failed: %s", exc)
        return {"users": [], "photos": [], "reports": []}


async def _safe_dashboard_monthly(admin_client: Any) -> list[Any]:
    try:
        return await _fetch_monthly_report_fallback(admin_client, datetime.now().year)
    except Exception as exc:
        logger.error("Fallback monthly failed: %s", exc)
        return []


async def _fetch_dashboard_summary_fallback(admin_client: Any) -> dict[str, Any]:
    total_users, total_photos, pending_reports, total_reports = await asyncio.gather(
        _safe_dashboard_count(admin_client, "users"),
        _safe_dashboard_count(admin_client, "cat_photos"),
        _safe_dashboard_count(admin_client, "reports", filters={"status": "pending"}),
        _safe_dashboard_count(admin_client, "reports"),
    )
    trends_data, monthly_data = await asyncio.gather(
        _safe_dashboard_trends(admin_client),
        _safe_dashboard_monthly(admin_client),
    )
    return _dashboard_result(
        total_users,
        total_photos,
        pending_reports,
        total_reports,
        trends_data,
        monthly_data,
    )


@router.get("/summary", responses=ADMIN_ERROR_RESPONSES)
@limiter.limit("10/minute")
async def get_dashboard_summary(
    request: Request,
    current_admin: Annotated[User, Depends(require_permission("system:stats"))],
) -> dict[str, Any]:
    """
    Consolidated dashboard summary: stats, trends, and monthly data.
    Uses Redis for distributed caching.
    """
    cache_key = "admin_dashboard_summary_v1"
    cached = await redis_service.get(cache_key)
    if cached:
        return cast(dict[str, Any], cached)

    try:
        admin_client = await get_async_supabase_admin_client()
        result = await _fetch_dashboard_summary_rpc(admin_client)
        await redis_service.set(cache_key, result, expire=300)
        return result
    except Exception as exc:
        logger.warning("Dashboard summary RPC path failed; retrying with Python fallback: %s", exc, exc_info=True)
        try:
            admin_client = await get_async_supabase_admin_client()
            result = await _fetch_dashboard_summary_fallback(admin_client)
            await redis_service.set(cache_key, result, expire=300)
            return result
        except Exception as fallback_error:
            logger.error("Failed to fetch dashboard summary (Ultimate Fallback): %s", fallback_error, exc_info=True)
            return {
                "stats": {"total_users": 0, "total_photos": 0, "pending_reports": 0, "total_reports": 0},
                "trends": {"users": [], "photos": [], "reports": []},
                "monthly": [],
                "generated_at": datetime.now().isoformat(),
                "error": "Partial data load failed",
            }


async def _get_trends_data_with_fallback(admin_client: Any, days_back: int = 30) -> dict[str, Any]:
    try:
        result = await admin_client.rpc("get_admin_trends", {"days_back": days_back}).execute()
        trends_data = cast(dict[str, Any], result.data or {})
        if trends_data:
            return trends_data
    except Exception as e:
        logger.warning("Admin trends RPC failed; using Python fallback: %s", e, exc_info=True)
    return await _fetch_trends_fallback(admin_client, days_back=days_back)


async def _get_monthly_data_with_fallback(admin_client: Any, year: int) -> list[dict[str, Any]]:
    try:
        params = {"report_year": year}
        result = await admin_client.rpc("get_monthly_report", params).execute()
        monthly_data = result.data or []
        if monthly_data:
            return cast(list[dict[str, Any]], monthly_data)
    except Exception as e:
        logger.warning("Monthly stats RPC failed; using Python fallback: %s", e, exc_info=True)
    return await _fetch_monthly_report_fallback(admin_client, year)


@router.get("/trends", responses=ADMIN_ERROR_RESPONSES)
@limiter.limit("5/minute")
async def get_system_trends(
    request: Request,
    current_admin: Annotated[User, Depends(require_permission("system:stats"))],
) -> dict[str, Any]:
    """
    Get 30-day activity trends.
    """
    cache_key = "admin_trends_v1"
    cached = await redis_service.get(cache_key)
    if cached:
        return cast(dict[str, Any], cached)

    try:
        admin_client = await get_async_supabase_admin_client()
        trends_data = await _get_trends_data_with_fallback(admin_client, days_back=30)
        await redis_service.set(cache_key, trends_data, expire=600)
        return trends_data
    except Exception as fallback_error:
        logger.error("Failed to get trends: %s", fallback_error, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch activity trends")


@router.get("/monthly", responses=ADMIN_ERROR_RESPONSES)
@limiter.limit("5/minute")
async def get_monthly_stats(
    request: Request,
    current_admin: Annotated[User, Depends(require_permission("system:stats"))],
    year: int | None = None,
) -> dict[str, Any]:
    """
    Get monthly system performance report.
    """
    target_year = year or datetime.now().year
    cache_key = f"admin_monthly_{target_year}"
    cached = await redis_service.get(cache_key)
    if cached:
        return cast(dict[str, Any], cached)

    try:
        admin_client = await get_async_supabase_admin_client()
        monthly_list = await _get_monthly_data_with_fallback(admin_client, target_year)
        data = {"data": monthly_list, "year": target_year}
        await redis_service.set(cache_key, data, expire=1800)
        return data
    except Exception as fallback_error:
        logger.error("Failed to fetch monthly stats: %s", fallback_error, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch monthly report")
