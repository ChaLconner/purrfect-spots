from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from config import config
from dependencies import get_current_token, get_treats_service
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.treats import (
    CheckoutUrlResponse,
    GiveTreatRequest,
    GiveTreatResponse,
    LeaderboardEntry,
    PurchaseTreatsRequest,
    TreatBalanceResponse,
)
from schemas.user import User
from services.treats_service import TreatsService

router = APIRouter(prefix="/treats", tags=["Treats"])


@router.get("/balance", response_model=TreatBalanceResponse)
async def get_balance(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    treats_service: Annotated[TreatsService, Depends(get_treats_service)],
) -> TreatBalanceResponse:
    """Get current user's treat balance and recent history."""
    return await treats_service.get_balance(current_user.id)


@router.post("/give", response_model=GiveTreatResponse)
async def give_treat(
    req: GiveTreatRequest,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    treats_service: Annotated[TreatsService, Depends(get_treats_service)],
    token: Annotated[str, Depends(get_current_token)],
) -> GiveTreatResponse:
    """Give treats to a photo owner."""
    try:
        result = await treats_service.give_treat(current_user.id, req.photo_id, req.amount, jwt_token=token)
        return GiveTreatResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to give treats: %s", e)
        raise HTTPException(status_code=500, detail="Internal error")


@router.post("/purchase/checkout", response_model=CheckoutUrlResponse)
async def purchase_treats_checkout(
    req: PurchaseTreatsRequest,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    treats_service: Annotated[TreatsService, Depends(get_treats_service)],
) -> CheckoutUrlResponse:
    """Purchase treats pack."""
    package_data = await treats_service.get_package_by_id(req.package)
    price_id = package_data.get("price_id") if package_data else None

    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid package or price not configured in database")

    try:
        frontend_url = config.FRONTEND_URL
        result = await treats_service.purchase_treats_checkout(
            user_id=current_user.id,
            package=req.package,
            price_id=price_id,
            success_url=f"{frontend_url}/profile?purchase=success",
            cancel_url=f"{frontend_url}/subscription?purchase=cancel",
            stripe_customer_id=current_user.stripe_customer_id,
        )
        return CheckoutUrlResponse(**result)
    except Exception as e:
        logger.error("Purchase checkout failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to initiate purchase")


@router.get("/packages", response_model=dict[str, Any])
async def get_treat_packages(
    treats_service: Annotated[TreatsService, Depends(get_treats_service)],
) -> dict[str, Any]:
    """Get available treat packages from database."""
    return await treats_service.get_packages()


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    treats_service: Annotated[TreatsService, Depends(get_treats_service)],
    period: str = "all_time",
) -> list[LeaderboardEntry]:
    """Get top treat receivers."""
    if period not in ["weekly", "monthly", "all_time"]:
        raise HTTPException(status_code=400, detail="Invalid period")
    results = await treats_service.get_leaderboard(period)
    return [LeaderboardEntry(**entry) if isinstance(entry, dict) else entry for entry in results]
