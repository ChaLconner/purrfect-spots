from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from config import config
from dependencies import get_current_token, get_supabase_admin_client
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.treats import GiveTreatRequest, PurchaseTreatsRequest, TreatBalanceResponse
from services.treats_service import TreatsService
from user_models.user import User

router = APIRouter(prefix="/treats", tags=["Treats"])


def get_treats_service(supabase: Client = Depends(get_supabase_admin_client)) -> TreatsService:
    return TreatsService(supabase)


@router.get("/balance", response_model=TreatBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user_from_credentials),
    treats_service: TreatsService = Depends(get_treats_service),
) -> dict[str, Any]:
    """Get current user's treat balance and recent history"""
    return await treats_service.get_balance(current_user.id)


@router.post("/give")
async def give_treat(
    req: GiveTreatRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    treats_service: TreatsService = Depends(get_treats_service),
    token: str = Depends(get_current_token),
) -> dict[str, Any]:
    """Give treats to a photo owner"""
    try:
        return await treats_service.give_treat(current_user.id, req.photo_id, req.amount, jwt_token=token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to give treats: %s", e)
        raise HTTPException(status_code=500, detail="Internal error")


@router.post("/purchase/checkout")
async def purchase_treats_checkout(
    req: PurchaseTreatsRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    treats_service: TreatsService = Depends(get_treats_service),
) -> dict[str, str]:
    """Purchase treats pack"""
    # Fetch package data from DB (uses cache internally)
    package_data = await treats_service.get_package_by_id(req.package)
    price_id = package_data.get("price_id") if package_data else None

    if not price_id:
        raise HTTPException(
            status_code=400, detail="Invalid package or price not configured in database"
        )

    try:
        frontend_url = config.FRONTEND_URL
        return await treats_service.purchase_treats_checkout(
            user_id=current_user.id,
            package=req.package,
            price_id=price_id,
            success_url=f"{frontend_url}/profile?purchase=success",
            cancel_url=f"{frontend_url}/subscription?purchase=cancel",
            stripe_customer_id=current_user.stripe_customer_id,
        )
    except Exception as e:
        logger.error("Purchase checkout failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to initiate purchase")


@router.get("/packages")
async def get_treat_packages(
    treats_service: TreatsService = Depends(get_treats_service),
) -> dict[str, dict[str, Any]]:
    """Get available treat packages from database"""
    return await treats_service.get_packages()


@router.get("/leaderboard")
async def get_leaderboard(
    period: str = "all_time",
    treats_service: TreatsService = Depends(get_treats_service),
) -> list[dict[str, Any]]:
    """Get top treat receivers"""
    if period not in ["weekly", "monthly", "all_time"]:
        raise HTTPException(status_code=400, detail="Invalid period")
    from typing import cast
    return cast(list[dict[str, Any]], await treats_service.get_leaderboard(period))
