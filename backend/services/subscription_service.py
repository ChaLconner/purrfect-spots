import os
from datetime import datetime, timezone
from typing import Any, Dict

import stripe
from starlette.concurrency import run_in_threadpool
from supabase import Client

from logger import logger
from services.treats_service import TreatsService

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class SubscriptionService:
    def __init__(self, supabase_client: Client) -> None:
        self.supabase = supabase_client
        self.treats_service = TreatsService(supabase_client)

    # ── Helpers ──────────────────────────────────────────────────────

    async def _get_or_create_stripe_customer(
        self, user_id: str, email: str, existing_customer_id: str | None = None
    ) -> str:
        """Resolve or create a Stripe Customer ID for the given user.

        Checks in order:
        1. Provided customer_id argument
        2. Database lookup
        3. Create new customer via Stripe API
        """
        if existing_customer_id:
            return existing_customer_id

        # DB lookup (sync call → threadpool)
        user_res = await run_in_threadpool(
            lambda: self.supabase.table("users")
            .select("stripe_customer_id")
            .eq("id", user_id)
            .single()
            .execute()
        )
        db_customer_id = user_res.data.get("stripe_customer_id") if user_res.data else None
        if db_customer_id:
            from typing import cast
            return cast(str, db_customer_id)

        # Create in Stripe (sync SDK → threadpool)
        customer = await run_in_threadpool(
            stripe.Customer.create,
            email=email,
            metadata={"user_id": user_id},
        )
        customer_id: str = customer.id

        # Persist back to DB
        await run_in_threadpool(
            lambda: self.supabase.table("users")
            .update({"stripe_customer_id": customer_id})
            .eq("id", user_id)
            .execute()
        )
        return customer_id

    # ── Checkout ─────────────────────────────────────────────────────

    async def create_checkout_session(
        self,
        user_id: str,
        email: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        stripe_customer_id: str | None = None,
    ) -> Dict[str, str]:
        """Creates a Stripe Checkout Session for a subscription."""
        try:
            customer_id = await self._get_or_create_stripe_customer(
                user_id, email, stripe_customer_id
            )

            checkout_session = await run_in_threadpool(
                stripe.checkout.Session.create,
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": user_id},
            )
            return {
                "checkout_url": checkout_session.url or "",
                "session_id": checkout_session.id,
            }
        except Exception as e:
            logger.error("Failed to create checkout session: %s", e, exc_info=True)
            raise

    # ── Webhook ──────────────────────────────────────────────────────

    async def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        """Handles Stripe Webhook events."""
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            logger.error("Stripe webhook: invalid payload")
            raise
        except stripe.error.SignatureVerificationError:
            logger.error("Stripe webhook: invalid signature")
            raise

        event_type: str = event["type"]
        data_object = event["data"]["object"]

        handler_map = {
            "checkout.session.completed": self._dispatch_checkout_completed,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "customer.subscription.updated": self._handle_subscription_updated,
        }

        handler = handler_map.get(event_type)
        if handler:
            await handler(data_object)
        else:
            logger.info("Unhandled Stripe webhook event type: %s", event_type)

    async def _dispatch_checkout_completed(self, session: Dict[str, Any]) -> None:
        """Route checkout.session.completed based on mode."""
        mode = session.get("mode")
        if mode == "subscription":
            await self._handle_checkout_session_completed(session)
        elif mode == "payment":
            await self._handle_payment_session_completed(session)
        else:
            logger.warning("Unknown checkout mode: %s", mode)

    # ── Subscription lifecycle handlers ──────────────────────────────

    async def _handle_checkout_session_completed(self, session: Dict[str, Any]) -> None:
        user_id = session.get("metadata", {}).get("user_id")

        if not user_id:
            # Fallback: resolve via customer_id
            customer_id = session.get("customer")
            if customer_id:
                res = await run_in_threadpool(
                    lambda: self.supabase.table("users")
                    .select("id")
                    .eq("stripe_customer_id", customer_id)
                    .single()
                    .execute()
                )
                if res.data:
                    user_id = res.data["id"]

        if not user_id:
            logger.error(
                "checkout.session.completed: could not resolve user_id. session=%s",
                session.get("id"),
            )
            return

        subscription_id = session.get("subscription")
        if not subscription_id:
            logger.warning("checkout.session.completed missing subscription id")
            return

        # Retrieve subscription details (sync SDK → threadpool)
        sub = await run_in_threadpool(stripe.Subscription.retrieve, subscription_id)
        current_period_end = datetime.fromtimestamp(
            sub.current_period_end, timezone.utc  # type: ignore[arg-type]
        )

        await run_in_threadpool(
            lambda: self.supabase.table("users")
            .update(
                {
                    "is_pro": True,
                    "subscription_end_date": current_period_end.isoformat(),
                    "cancel_at_period_end": sub.cancel_at_period_end,
                }
            )
            .eq("id", user_id)
            .execute()
        )
        logger.info("Subscription activated for user %s", user_id)

    async def _handle_payment_session_completed(self, session: Dict[str, Any]) -> None:
        """Handle one-time payments (e.g., Treats) by delegating to specialized services."""
        purchase_type = session.get("metadata", {}).get("type")

        if purchase_type == "treat_purchase":
            await self.treats_service.fulfill_treat_purchase(session)
        else:
            logger.info("Unhandled payment session type: %s", purchase_type)

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> None:
        customer_id = subscription.get("customer")
        if not customer_id:
            logger.warning("subscription.deleted missing customer_id")
            return

        await run_in_threadpool(
            lambda: self.supabase.table("users")
            .update(
                {
                    "is_pro": False,
                    "subscription_end_date": None,
                    "cancel_at_period_end": False,
                }
            )
            .eq("stripe_customer_id", customer_id)
            .execute()
        )
        logger.info("Subscription deleted for customer %s", customer_id)

    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> None:
        customer_id = subscription.get("customer")
        if not customer_id:
            logger.warning("Subscription updated event missing customer_id")
            return

        cancel_at_period_end = subscription.get("cancel_at_period_end", False)
        raw_period_end = subscription.get("current_period_end")

        if raw_period_end is None:
            logger.warning(
                "Subscription updated event missing current_period_end for customer %s",
                customer_id,
            )
            return

        current_period_end = datetime.fromtimestamp(raw_period_end, timezone.utc)

        await run_in_threadpool(
            lambda: self.supabase.table("users")
            .update(
                {
                    "cancel_at_period_end": cancel_at_period_end,
                    "subscription_end_date": current_period_end.isoformat(),
                }
            )
            .eq("stripe_customer_id", customer_id)
            .execute()
        )

    # ── Query helpers ────────────────────────────────────────────────

    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        res = await run_in_threadpool(
            lambda: self.supabase.table("users")
            .select(
                "is_pro, subscription_end_date, stripe_customer_id, "
                "cancel_at_period_end, treat_balance"
            )
            .eq("id", user_id)
            .single()
            .execute()
        )
        return res.data if res.data else {
            "is_pro": False,
            "cancel_at_period_end": False,
            "treat_balance": 0,
        }

    async def create_portal_session(self, user_id: str, return_url: str) -> str:
        """Create a Stripe Customer Portal session."""
        res = await run_in_threadpool(
            lambda: self.supabase.table("users")
            .select("stripe_customer_id")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not res.data:
            raise ValueError("User not found")

        customer_id = res.data.get("stripe_customer_id")
        if not customer_id:
            raise ValueError("No customer ID found for user")

        portal_session = await run_in_threadpool(
            stripe.billing_portal.Session.create,
            customer=customer_id,
            return_url=return_url,
        )
        return portal_session.url

    async def cancel_subscription(self, user_id: str) -> None:
        """Cancel active subscriptions (set to cancel at period end)."""
        res = await run_in_threadpool(
            lambda: self.supabase.table("users")
            .select("stripe_customer_id")
            .eq("id", user_id)
            .single()
            .execute()
        )
        if not res.data:
            raise ValueError("User not found")

        customer_id = res.data.get("stripe_customer_id")
        if not customer_id:
            raise ValueError("No subscription found")

        subscriptions = await run_in_threadpool(
            stripe.Subscription.list, customer=customer_id, status="active"
        )
        if not subscriptions.data:
            raise ValueError("No active subscription to cancel")

        # Cancel only the first/active subscription
        for sub in subscriptions.data:
            await run_in_threadpool(
                stripe.Subscription.modify, sub.id, cancel_at_period_end=True
            )
