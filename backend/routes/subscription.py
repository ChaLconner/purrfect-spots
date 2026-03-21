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
from schemas.user import User
from services.subscription_service import SubscriptionService

router = APIRouter(prefix="/subscription", tags=["Subscription"])


from typing import Annotated


@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    checkout_req: CreateCheckoutRequest,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> dict[str, Any]:
    """
    Create a Stripe Checkout Session for subscription.

    Raises:
        HTTPException: 500 - If checkout session creation fails.
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
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
    stripe_signature: Annotated[str | None, Header(alias="stripe-signature")] = None,
) -> dict[str, str]:
    """
    Handle Stripe Webhooks.

    Raises:
        HTTPException: 400 - If Stripe signature is missing or payload is invalid.
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
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> dict[str, Any]:
    """
    Get current user's subscription status.
    """
    return await subscription_service.get_subscription_status(current_user.id)


@router.post("/cancel")
async def cancel_subscription(
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> dict[str, str]:
    """
    Cancel subscription.

    Raises:
        HTTPException: 400 - If cancellation fails due to validation error.
        HTTPException: 500 - If cancellation fails due to internal error.
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
    req: Annotated[CreatePortalRequest, Depends()],
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> dict[str, str]:
    """
    Create Stripe Customer Portal session.

    Raises:
        HTTPException: 400 - If portal session creation fails due to validation error.
        HTTPException: 500 - If portal session creation fails due to internal error.
    """
    try:
        url = await subscription_service.create_portal_session(current_user.id, req.return_url)
        return {"url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Portal creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")
