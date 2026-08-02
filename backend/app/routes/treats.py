from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import config
from app.dependencies import get_current_token, get_treats_service
from app.logger import logger
from app.middleware.auth_middleware import get_current_user_from_credentials
from app.schemas.treats import (
    CheckoutUrlResponse,
    GiveTreatRequest,
    GiveTreatResponse,
    LeaderboardEntry,
    PurchaseTreatsRequest,
    TreatBalanceResponse,
)
from app.schemas.user import User
from app.services.treats_service import TreatsService

router = APIRouter(prefix="/treats", tags=["Treats"])


@router.get("/balance", response_model=TreatBalanceResponse)
async def get_balance(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    treats_service: Annotated[TreatsService, Depends(get_treats_service)],
) -> TreatBalanceResponse:
    """Get current user's treat balance and recent history."""
    result = await treats_service.get_balance(current_user.id)
    return TreatBalanceResponse(**result)


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
        result = await treats_service.purchase_treats_checkout(
            user_id=current_user.id,
            package=req.package,
            price_id=price_id,
            success_url=config.resolve_frontend_url(default_path="/profile?purchase=success"),
            cancel_url=config.resolve_frontend_url(default_path="/subscription?purchase=cancel"),
            stripe_customer_id=getattr(current_user, "stripe_customer_id", None),
        )
        return CheckoutUrlResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Purchase checkout failed: %s", e, exc_info=True)
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
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
) -> list[LeaderboardEntry]:
    """Get top treat receivers with pagination."""
    if period not in ["weekly", "monthly", "all_time"]:
        raise HTTPException(status_code=400, detail="Invalid period")
    results = await treats_service.get_leaderboard(period, limit=limit, offset=offset)
    return [LeaderboardEntry(**entry) if isinstance(entry, dict) else entry for entry in results]
