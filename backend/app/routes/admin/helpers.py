from __future__ import annotations

from typing import Annotated, Any, cast

from fastapi import Query, Request


class CommonPagination:
    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=1000)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
        sort_by: Annotated[str, Query(alias="sort")] = "created_at",
        order: Annotated[str, Query()] = "desc",
    ):
        self.limit = limit
        self.offset = offset
        self.sort_by = sort_by
        self.order = order


from app.utils.audit_logger import log_admin_action


async def create_admin_audit_log(
    admin_client: Any,
    user_id: str,
    action: str,
    resource: str,
    changes: dict[str, Any],
    target_id: str = "",
    request: Request | None = None,
) -> None:
    """Utility function to create audit log records for admin actions."""
    await log_admin_action(
        admin_client=admin_client,
        admin_id=user_id,
        action=action,
        target_type=resource,
        target_id=target_id,
        details=changes,
    )


async def fetch_cached_admin_list(
    cache_key: str,
    cache_bust: bool,
    ttl: int,
    query_builder: Any,
) -> dict[str, Any]:
    """Execute query with Redis caching fallback for admin list endpoints."""
    from app.services.redis_service import redis_service

    if not cache_bust:
        cached = await redis_service.get(cache_key)
        if cached is not None:
            return cast(dict[str, Any], cached)

    result = await query_builder.execute()
    response = {"data": result.data, "total": result.count}
    if not cache_bust:
        await redis_service.set(cache_key, response, expire=ttl)
    return response


async def fetch_photo_by_id(admin_client: Any, photo_id: str) -> dict[str, Any] | None:
    """Fetch photo details by photo ID using admin client."""
    res = await admin_client.table("cat_photos").select("id, image_url, user_id").eq("id", photo_id).single().execute()
    if res.data and isinstance(res.data, dict):
        return cast(dict[str, Any], res.data)
    return None
