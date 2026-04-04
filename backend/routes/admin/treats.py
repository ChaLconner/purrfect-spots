from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from postgrest.types import CountMethod
from pydantic import BaseModel, Field

from dependencies import get_async_supabase_admin_client
from logger import logger
from middleware.auth_middleware import require_permission
from schemas.user import User

router = APIRouter()

MAX_GRANT_AMOUNT = 10000


class GrantTreatRequest(BaseModel):
    user_id: str = Field(..., min_length=36, max_length=36, description="UUID of the target user")
    amount: int = Field(..., ge=1, le=MAX_GRANT_AMOUNT, description=f"Number of treats to grant (1-{MAX_GRANT_AMOUNT})")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for the grant")


@router.get("/transactions/")
async def list_treat_transactions(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=1000)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    transaction_type: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    current_admin: Annotated[User, Depends(require_permission("treats:manage"))] = None,
):
    """List all treat transactions (purchases, giving, grants)."""
    try:
        admin_client = await get_async_supabase_admin_client()

        query = (
            admin_client.table("treats_transactions")
            .select(
                "*, from_user:from_user_id(name, email), to_user:to_user_id(name, email)",
                count=CountMethod.exact,
            )
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        if transaction_type:
            query = query.eq("transaction_type", transaction_type)

        result = await query.execute()

        data = result.data or []
        total = result.count if result.count is not None else len(data)

        return {"data": data, "total": total, "offset": offset, "limit": limit}
    except Exception as e:
        logger.error("Failed to list treat transactions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch transactions")


async def _fetch_treat_stats_fallback(admin_client) -> dict:
    """Fallback: fetch aggregated columns from users table in batches to avoid memory issues."""
    total_in_circulation = 0
    total_given_to_cats = 0
    user_count_with_balance = 0

    batch_size = 1000
    offset = 0

    while True:
        balance_res = (
            await admin_client.table("users")
            .select("treat_balance, total_treats_received")
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        rows = balance_res.data or []
        if not rows:
            break

        for u in rows:
            balance = u.get("treat_balance") or 0
            total_in_circulation += balance
            total_given_to_cats += u.get("total_treats_received") or 0
            if balance > 0:
                user_count_with_balance += 1

        if len(rows) < batch_size:
            break
        offset += batch_size

    return {
        "total_in_circulation": total_in_circulation,
        "total_given_to_cats": total_given_to_cats,
        "user_count_with_balance": user_count_with_balance,
    }


@router.get("/stats/")
async def get_treat_stats(
    current_admin: Annotated[User, Depends(require_permission("treats:manage"))] = None,
):
    """Get global treat statistics."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # Try RPC first (requires migration 026)
        try:
            stats_res = await admin_client.rpc("get_treat_admin_stats").execute()
            if stats_res.data and len(stats_res.data) > 0:
                row = stats_res.data[0]
                return {
                    "total_in_circulation": row.get("total_in_circulation", 0),
                    "total_given_to_cats": row.get("total_given_to_cats", 0),
                    "user_count_with_balance": row.get("user_count_with_balance", 0),
                }
        except Exception:
            logger.warning("get_treat_admin_stats RPC not available, using fallback")

        return await _fetch_treat_stats_fallback(admin_client)
    except Exception as e:
        logger.error("Failed to fetch treat stats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch treat stats")


@router.get("/users/search/")
async def search_users_for_grant(
    q: Annotated[str, Query(min_length=1, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
    current_admin: Annotated[User, Depends(require_permission("treats:manage"))] = None,
):
    """Search users by name or email for the grant modal."""
    try:
        admin_client = await get_async_supabase_admin_client()
        result = (
            await admin_client.table("users")
            .select("id, name, email")
            .or_(f"name.ilike.%{q}%,email.ilike.%{q}%")
            .limit(limit)
            .execute()
        )
        return {"data": result.data or []}
    except Exception as e:
        logger.error("Failed to search users: %s", e)
        raise HTTPException(status_code=500, detail="Failed to search users")


@router.post("/grant/")
async def grant_treats_manually(
    request: Request,
    data: GrantTreatRequest,
    current_admin: Annotated[User, Depends(require_permission("treats:manage"))] = None,
):
    """Manually grant treats to a user (System Grant)."""
    try:
        admin_client = await get_async_supabase_admin_client()

        # Check user exists
        user_check = (
            await admin_client.table("users").select("id, treat_balance").eq("id", data.user_id).single().execute()
        )
        if not user_check.data:
            raise HTTPException(status_code=404, detail="User not found")

        # Try atomic RPC first (requires migration 026)
        granted = False
        try:
            await admin_client.rpc(
                "admin_grant_treats",
                {"p_user_id": data.user_id, "p_amount": data.amount},
            ).execute()
            granted = True
        except Exception:
            logger.warning("admin_grant_treats RPC not available, using fallback")

        # Fallback: atomic-ish UPDATE (treat_balance = treat_balance + amount)
        if not granted:
            new_balance = (user_check.data.get("treat_balance") or 0) + data.amount
            await admin_client.table("users").update({"treat_balance": new_balance}).eq("id", data.user_id).execute()

        # Record transaction
        await (
            admin_client.table("treats_transactions")
            .insert(
                {
                    "to_user_id": data.user_id,
                    "amount": data.amount,
                    "transaction_type": "system_grant",
                    "description": data.reason,
                }
            )
            .execute()
        )

        # Log Audit
        await (
            admin_client.table("audit_logs")
            .insert(
                {
                    "user_id": current_admin.id,
                    "action": "GRANT_TREATS",
                    "resource": "users",
                    "changes": {"target_user_id": data.user_id, "amount": data.amount, "reason": data.reason},
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                }
            )
            .execute()
        )

        return {"message": f"Successfully granted {data.amount} treats"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error("Failed to grant treats: %s", e)
        raise HTTPException(status_code=500, detail="Failed to grant treats")
