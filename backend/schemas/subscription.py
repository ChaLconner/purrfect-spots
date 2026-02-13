from datetime import datetime

from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    price_id: str  # Stripe Price ID (e.g., "price_xxx")
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str

class SubscriptionStatus(BaseModel):
    is_pro: bool
    subscription_end_date: datetime | None = None
    cancel_at_period_end: bool = False
    stripe_customer_id: str | None = None
    treat_balance: int = 0

class CreatePortalRequest(BaseModel):
    return_url: str

class PortalResponse(BaseModel):
    url: str
