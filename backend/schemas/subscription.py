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
    subscription_end_date: datetime | None
    stripe_customer_id: str | None
