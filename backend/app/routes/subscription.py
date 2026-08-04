from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from stripe import SignatureVerificationError

from app.config import config
from app.dependencies import get_subscription_service
from app.limiter import limiter
from app.logger import logger
from app.middleware.auth_middleware import get_current_user_from_credentials
from app.schemas.common import MessageResponse
from app.schemas.subscription import (
    CheckoutSessionResponse,
    CreateCheckoutRequest,
    CreatePortalRequest,
    PortalResponse,
    SubscriptionPlansResponse,
    SubscriptionStatus,
)
from app.schemas.user import User
from app.services.queue_service import QueueBackpressure, QueueUnavailable, queue_service
from app.services.subscription_service import SubscriptionPersistenceError, SubscriptionService

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.get("/plans", response_model=SubscriptionPlansResponse)
@limiter.limit("30/minute")
async def get_subscription_plans(
    request: Request,
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> SubscriptionPlansResponse:
    """Return current public subscription prices from Stripe."""
    try:
        return SubscriptionPlansResponse(**(await subscription_service.get_plan_prices()))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Subscription pricing lookup failed: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail="Subscription pricing temporarily unavailable") from e


@router.post("/checkout", response_model=CheckoutSessionResponse)
@limiter.limit("5/minute")
async def create_checkout_session(
    request: Request,
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
        result = await subscription_service.create_checkout_session(
            user_id=current_user.id,
            email=current_user.email,
            price_id=price_id,
            success_url=config.resolve_frontend_url(default_path="/subscription?purchase=success"),
            cancel_url=config.resolve_frontend_url(default_path="/subscription?purchase=cancel"),
            stripe_customer_id=getattr(current_user, "stripe_customer_id", None),
        )
        return CheckoutSessionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Checkout creation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post(
    "/webhook",
    response_model=MessageResponse,
    responses={503: {"description": "Webhook queue or persistence temporarily unavailable"}},
)
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
        if config.ENABLE_STRIPE_WEBHOOK_QUEUE:
            event = subscription_service.construct_webhook_event(payload, stripe_signature)
            await queue_service.enqueue_stripe_webhook(event)
        else:
            await subscription_service.handle_webhook(payload, stripe_signature)
    except (ValueError, SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid payload")
    except SubscriptionPersistenceError:
        # Non-2xx tells Stripe to retry after a transient database failure.
        raise HTTPException(status_code=503, detail="Webhook persistence temporarily unavailable")
    except (QueueUnavailable, QueueBackpressure):
        # Never fall back to request-cycle processing when queue mode is on.
        # Stripe receives a non-2xx response and retries the event.
        raise HTTPException(status_code=503, detail="Webhook queue temporarily unavailable")
    except Exception as e:
        logger.exception("Webhook processing failed: %s", e)
        raise HTTPException(status_code=500, detail="Webhook processing failed")

    return MessageResponse(message="accepted" if config.ENABLE_STRIPE_WEBHOOK_QUEUE else "success")


@router.get("/status", response_model=SubscriptionStatus)
@limiter.limit("30/minute")
async def get_subscription_status(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    subscription_service: Annotated[SubscriptionService, Depends(get_subscription_service)],
) -> SubscriptionStatus:
    """Get current user's subscription status."""
    result = await subscription_service.get_subscription_status(current_user.id)
    return SubscriptionStatus(**result)


@router.post("/cancel", response_model=MessageResponse)
@limiter.limit("5/minute")
async def cancel_subscription(
    request: Request,
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
@limiter.limit("10/minute")
async def create_portal_session(
    request: Request,
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
