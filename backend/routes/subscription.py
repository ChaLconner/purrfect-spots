from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from dependencies import get_subscription_service
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.subscription import (
    CheckoutSessionResponse,
    CreateCheckoutRequest,
    CreatePortalRequest,
    PortalResponse,
    SubscriptionStatus,
)
from services.subscription_service import SubscriptionService
from user_models.user import User

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    checkout_req: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, Any]:
    """
    Create a Stripe Checkout Session for subscription
    """
    try:
        return await subscription_service.create_checkout_session(
            user_id=current_user.id,
            email=current_user.email,
            price_id=checkout_req.price_id,
            success_url=checkout_req.success_url,
            cancel_url=checkout_req.cancel_url,
            stripe_customer_id=current_user.stripe_customer_id,
        )
    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, str]:
    """
    Handle Stripe Webhooks
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe Signature")

    payload = await request.body()
    try:
        await subscription_service.handle_webhook(payload, stripe_signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        logger.error("Webhook processing failed: %s", e)
        raise HTTPException(status_code=400, detail="Webhook processing failed")

    return {"status": "success"}


@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(get_current_user_from_credentials),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, Any]:
    """
    Get current user's subscription status
    """
    return await subscription_service.get_subscription_status(current_user.id)


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user_from_credentials),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, str]:
    """
    Cancel subscription
    """
    try:
        await subscription_service.cancel_subscription(current_user.id)
        return {"message": "Subscription cancelled"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Cancellation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    req: CreatePortalRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, str]:
    """
    Create Stripe Customer Portal session
    """
    try:
        url = await subscription_service.create_portal_session(current_user.id, req.return_url)
        return {"url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Portal creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")
