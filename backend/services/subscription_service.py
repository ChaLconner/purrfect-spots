import os
from datetime import datetime, timezone
from typing import Any, Dict

import stripe
from supabase import Client

from logger import logger

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class SubscriptionService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def create_checkout_session(
        self, user_id: str, email: str, price_id: str,
        success_url: str, cancel_url: str
    ) -> Dict[str, str]:
        """Creates a Stripe Checkout Session."""
        try:
            # Check if user already has a Stripe Customer ID
            user_res = self.supabase.table("users").select("stripe_customer_id").eq("id", user_id).single().execute()
            customer_id = user_res.data.get("stripe_customer_id") if user_res.data else None

            if not customer_id:
                # Create a new Customer in Stripe
                customer = stripe.Customer.create(
                    email=email,
                    metadata={"user_id": user_id}
                )
                customer_id = customer.id
                # Update user with stripe_customer_id
                self.supabase.table("users").update({"stripe_customer_id": customer_id}).eq("id", user_id).execute()

            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": user_id}
            )
            return {
                "checkout_url": checkout_session.url or "",
                "session_id": checkout_session.id
            }
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise e

    async def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        """Handles Stripe Webhook events."""
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            raise e
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise e

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            mode = session.get("mode")
            if mode == "subscription":
                await self._handle_checkout_session_completed(session)
            elif mode == "payment":
                await self._handle_payment_session_completed(session)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await self._handle_subscription_deleted(subscription)

    async def _handle_checkout_session_completed(self, session):
        user_id = session.get("metadata", {}).get("user_id")
        if not user_id:
            # Try to find by customer_id if metadata missing
             customer_id = session.get("customer")
             if customer_id:
                 res = self.supabase.table("users").select("id").eq("stripe_customer_id", customer_id).single().execute()
                 if res.data:
                     user_id = res.data["id"]
        
        if user_id:
            # Retrieve subscription details to get end date
            subscription_id = session.get("subscription")
            if subscription_id:
                sub = stripe.Subscription.retrieve(subscription_id)
                # Ensure we have a datetime object
                current_period_end = datetime.fromtimestamp(sub.current_period_end, timezone.utc)  # type: ignore
                
                self.supabase.table("users").update({
                    "is_pro": True,
                    "subscription_end_date": current_period_end.isoformat()
                }).eq("id", user_id).execute()

    async def _handle_payment_session_completed(self, session):
        """Handle one-time payments (e.g., Treats)"""
        user_id = session.get("metadata", {}).get("user_id")
        purchase_type = session.get("metadata", {}).get("type")
        package = session.get("metadata", {}).get("package")

        if not user_id:
            logger.error("Payment session completed without user_id in metadata")
            return

        if purchase_type == "treat_purchase" and package:
            # Determine treat amount based on package
            # This logic duplicates the map in router, maybe refactor later or store in metadata more robustly
            treats_map = {
                'small': 10,
                'medium': 35, # 30 + 5 bonus
                'large': 125, # 100 + 25 bonus
                'legendary': 650 # 500 + 150 bonus
            }
            amount = treats_map.get(package, 0)
            
            if amount > 0:
                # Add treats using RPC call to avoid race conditions
                try:
                    # Idempotency check handled by unique constraint on stripe_session_id
                    
                    # Use atomic update for balance
                    self.supabase.rpc("increment_treats", {"user_id": user_id, "amount": amount}).execute()
                    
                    # Log transaction with stripe_session_id
                    self.supabase.table("treats_transactions").insert({
                        "to_user_id": user_id,
                        "amount": amount,
                        "transaction_type": "purchase",
                        "description": f"Purchased {package} pack",
                        "stripe_session_id": session.get("id")
                    }).execute()
                    
                    # Also update total_treats_received? No, this is PURCHASE, not received from user.
                    # But maybe we want to track total purchased? Optional.
                    
                    logger.info(f"Added {amount} treats to user {user_id}")
                except Exception as e:
                    # If unique violation (duplicate webhook), we can ignore safely
                    if "treats_transactions_stripe_session_id_key" in str(e):
                        logger.info(f"Duplicate webhook processed for session {session.get('id')}")
                    else:
                        logger.error(f"Failed to add treats: {e}")

    async def _handle_subscription_deleted(self, subscription):
        customer_id = subscription.get("customer")
        if customer_id:
            self.supabase.table("users").update({
                "is_pro": False,
                "subscription_end_date": None
            }).eq("stripe_customer_id", customer_id).execute()

    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        res = self.supabase.table("users").select("is_pro, subscription_end_date, stripe_customer_id").eq("id", user_id).single().execute()
        return res.data if res.data else {"is_pro": False}

    async def cancel_subscription(self, user_id: str):
         # Logic to cancel subscription via Stripe API
         # Get stripe_customer_id -> get list of subscriptions -> cancel active one
         res = self.supabase.table("users").select("stripe_customer_id").eq("id", user_id).single().execute()
         customer_id = res.data.get("stripe_customer_id")
         if not customer_id:
             raise ValueError("No subscription found")
         
         subscriptions = stripe.Subscription.list(customer=customer_id, status='active')
         for sub in subscriptions.auto_paging_iter():
             stripe.Subscription.modify(sub.id, cancel_at_period_end=True)
