import os

from fastapi import APIRouter, Depends, HTTPException

from config import config
from dependencies import get_supabase_admin_client
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.treats import GiveTreatRequest, PurchaseTreatsRequest, TreatBalanceResponse
from services.treats_service import TreatsService
from user_models.user import User

router = APIRouter(prefix="/treats", tags=["Treats"])

def get_treats_service(supabase=Depends(get_supabase_admin_client)):
    return TreatsService(supabase)

@router.get("/balance", response_model=TreatBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user_from_credentials),
    treats_service: TreatsService = Depends(get_treats_service),
):
    """Get current user's treat balance and recent history"""
    return await treats_service.get_balance(current_user.id)

@router.post("/give")
async def give_treat(
    req: GiveTreatRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    treats_service: TreatsService = Depends(get_treats_service),
):
    """Give treats to a photo owner"""
    try:
        return await treats_service.give_treat(current_user.id, req.photo_id, req.amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to give treats: {e}")
        raise HTTPException(status_code=500, detail="Internal error")

@router.post("/purchase/checkout")
async def purchase_treats_checkout(
    req: PurchaseTreatsRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    treats_service: TreatsService = Depends(get_treats_service),
):
    """Purchase treats pack"""
    # Mapping package to price ID
    price_map = {
        'small': os.getenv("STRIPE_TREAT_SMALL_PRICE_ID"),    # 10 treats (฿49)
        'medium': os.getenv("STRIPE_TREAT_MEDIUM_PRICE_ID"),  # 35 treats (฿129)
        'large': os.getenv("STRIPE_TREAT_LARGE_PRICE_ID"),    # 125 treats (฿399)
        'legendary': os.getenv("STRIPE_TREAT_LEGENDARY_PRICE_ID"), # 650 treats (฿1,499)
    }
    
    price_id = price_map.get(req.package)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid package")
        
    try:
        frontend_url = config.FRONTEND_URL
        return await treats_service.purchase_treats_checkout(
            user_id=current_user.id,
            package=req.package,
            price_id=price_id,
            success_url=f"{frontend_url}/profile?purchase=success",
            cancel_url=f"{frontend_url}/treats/store?purchase=cancel"
        )
    except Exception as e:
        logger.error(f"Purchase checkout failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate purchase")

@router.get("/leaderboard")
async def get_leaderboard(
    treats_service: TreatsService = Depends(get_treats_service),
):
    """Get top treat receivers"""
    return await treats_service.get_leaderboard()
