from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request

from config import config
from dependencies import get_subscription_service
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.common import MessageResponse
from schemas.subscription import (
    CheckoutSessionResponse,
    CreateCheckoutRequest,
    CreatePortalRequest,
    PortalResponse,
    SubscriptionStatus,
)
from schemas.user import User
from services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    req: Annotated[CreateCheckoutRequest | None, Body()] = None,
) -> CheckoutSessionResponse:
    """Create a Stripe Checkout Session for subscription."""
    plan = req.plan if req else "monthly"

    price_id = config.STRIPE_PRO_ANNUAL_PRICE_ID if plan == "annual" else config.STRIPE_PRO_PRICE_ID

    if not price_id:
        raise HTTPException(status_code=503, detail="Subscription checkout is not configured for this plan")

    try:
        return await subscription_service.create_checkout_session(
            user_id=current_user.id,
            email=current_user.email,
            price_id=price_id,
            success_url=config.resolve_frontend_url(default_path="/subscription?purchase=success"),
            cancel_url=config.resolve_frontend_url(default_path="/subscription?purchase=cancel"),
            stripe_customer_id=current_user.stripe_customer_id,
        )
    except Exception as e:
        logger.error("Checkout creation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/webhook", response_model=MessageResponse)
async def stripe_webhook(
    request: Request,
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    stripe_signature: Annotated[str | None, Header(alias="stripe-signature")] = None,
) -> MessageResponse:
    """Handle Stripe Webhooks."""
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

    return MessageResponse(message="success")


@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> SubscriptionStatus:
    """Get current user's subscription status."""
    return await subscription_service.get_subscription_status(current_user.id)


@router.post("/cancel", response_model=MessageResponse)
async def cancel_subscription(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> MessageResponse:
    """Cancel subscription."""
    try:
        await subscription_service.cancel_subscription(current_user.id)
        return MessageResponse(message="Subscription cancelled")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Cancellation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.post("/portal", response_model=PortalResponse)
async def create_portal_session(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    req: Annotated[CreatePortalRequest | None, Body()] = None,
) -> PortalResponse:
    """Create Stripe Customer Portal session."""
    try:
        url = await subscription_service.create_portal_session(current_user.id, req.return_url if req else None)
        return PortalResponse(url=url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Portal creation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create portal session")
