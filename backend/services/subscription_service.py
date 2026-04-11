import os
import uuid
from datetime import UTC, datetime
from typing import Any, cast

import stripe
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from config import config
from logger import logger
from services.treats_service import TreatsService
from supabase import AClient

# ── Stripe Initialisation ────────────────────────────────────────────
# Pin the API version so a dashboard upgrade never silently breaks
# webhook payload shapes or SDK behaviour.
stripe.api_key = config.STRIPE_SECRET_KEY or os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = "2025-02-24.acacia"

# Subscription statuses that grant Pro access.
_ACTIVE_STATUSES = frozenset({"active", "trialing"})

# Webhook events handled by this service.
_HANDLED_WEBHOOK_EVENTS = frozenset(
    {
        "checkout.session.completed",
        "customer.subscription.deleted",
        "customer.subscription.updated",
        "invoice.payment_failed",
        "invoice.payment_action_required",
        "invoice.paid",
    }
)


class SubscriptionService:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        self.treats_service = TreatsService(supabase_client, db=db)

    # ── DB helpers ────────────────────────────────────────────────────

    async def _get_user_data(self, filters: dict[str, Any], fields: str = "*") -> dict[str, Any] | None:
        """Fetch user data using either SQLAlchemy or Supabase client."""
        try:
            if self.db:
                db_session = self.db
                allowed_keys = {"id", "email", "stripe_customer_id"}
                where_conditions = [f"{k} = :{k}" for k in filters if k in allowed_keys]
                safe_fields = fields  # always passed as constants
                where_clause = " AND ".join(where_conditions)
                sql_query = text(f"SELECT {safe_fields} FROM users WHERE {where_clause}")  # noqa: S608
                result = await db_session.execute(sql_query, filters)
                row = result.fetchone()
                return dict(row._mapping) if row else None

            supa_query = self.supabase.table("users").select(fields)
            for key, value in filters.items():
                supa_query = supa_query.eq(key, value)

            res = await supa_query.limit(1).execute()
            return cast(dict[str, Any], res.data[0]) if res.data else None
        except Exception as e:
            logger.error("Error fetching user data: %s", e)
            return None

    async def _update_user_data(self, updates: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any] | None:
        """Update user data using either SQLAlchemy or Supabase client."""
        try:
            if self.db:
                db_session = self.db
                allowed_updates = {
                    "stripe_customer_id",
                    "is_pro",
                    "subscription_end_date",
                    "cancel_at_period_end",
                }
                allowed_filters = {"id", "email", "stripe_customer_id"}
                set_parts = [f"{k} = :val_{k}" for k in updates if k in allowed_updates]
                where_parts = [f"{k} = :find_{k}" for k in filters if k in allowed_filters]

                params = {f"val_{k}": v for k, v in updates.items() if k in allowed_updates}
                params.update({f"find_{k}": v for k, v in filters.items() if k in allowed_filters})

                set_clause = ", ".join(set_parts)
                where_clause = " AND ".join(where_parts)

                sql_query = text(f"UPDATE users SET {set_clause} WHERE {where_clause} RETURNING *")  # noqa: S608
                result = await db_session.execute(sql_query, params)
                await db_session.commit()
                row = result.fetchone()
                return dict(row._mapping) if row else None

            supa_query = self.supabase.table("users").update(updates)
            for key, value in filters.items():
                supa_query = supa_query.eq(key, value)

            res = await supa_query.execute()
            return cast(dict[str, Any], res.data[0]) if res.data else None
        except Exception as e:
            if self.db:
                await self.db.rollback()
            logger.error("Error updating user data: %s", e)
            return None

    # ── Helpers ──────────────────────────────────────────────────────

    def _extract_subscription_price_ids(self, subscription: Any) -> set[str]:
        """Extract Stripe price IDs from a subscription payload/object."""
        items = subscription.get("items") if isinstance(subscription, dict) else getattr(subscription, "items", None)
        raw_items = items.get("data", []) if isinstance(items, dict) else getattr(items, "data", []) if items else []

        price_ids: set[str] = set()
        for item in raw_items or []:
            price = item.get("price") if isinstance(item, dict) else getattr(item, "price", None)
            price_id = price.get("id") if isinstance(price, dict) else getattr(price, "id", None)
            if price_id:
                price_ids.add(str(price_id))

        return price_ids

    def _subscription_matches_pro_plan(self, subscription: Any) -> bool:
        """Validate that the subscription contains the configured Pro plan price."""
        valid_price_ids = {config.STRIPE_PRO_PRICE_ID, config.STRIPE_PRO_ANNUAL_PRICE_ID} - {None, ""}
        if not valid_price_ids:
            logger.error("No Pro plan price IDs configured; refusing to activate subscription benefits")
            return False

        return bool(valid_price_ids.intersection(self._extract_subscription_price_ids(subscription)))

    def _subscription_is_active(self, subscription: Any) -> bool:
        """Return True only when the subscription status grants Pro access."""
        status = subscription.get("status") if isinstance(subscription, dict) else getattr(subscription, "status", None)
        return str(status) in _ACTIVE_STATUSES

    async def _get_or_create_stripe_customer(
        self, user_id: str, email: str, existing_customer_id: str | None = None
    ) -> str:
        """Resolve or create a Stripe Customer ID for the given user."""
        if existing_customer_id:
            return existing_customer_id

        db_customer_id = None
        user_data = await self._get_user_data({"id": user_id}, "stripe_customer_id")
        if user_data:
            db_customer_id = user_data.get("stripe_customer_id")

        if db_customer_id:
            return cast(str, db_customer_id)

        # Create in Stripe (sync SDK → threadpool)
        customer = await run_in_threadpool(
            stripe.Customer.create,
            email=email,
            metadata={"user_id": user_id},
        )
        customer_id: str = customer.id

        await self._update_user_data({"stripe_customer_id": customer_id}, {"id": user_id})
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
    ) -> dict[str, str]:
        """Creates a Stripe Checkout Session for a subscription.

        Uses an idempotency key scoped to (user_id, price_id) so that accidental
        double-clicks or network retries do not create duplicate sessions.
        """
        try:
            if not price_id:
                raise ValueError("Missing Stripe price configuration for Pro plan")

            customer_id = await self._get_or_create_stripe_customer(user_id, email, stripe_customer_id)

            # Idempotency key: prevents duplicate checkout sessions for the same
            # user/plan pair within the Stripe idempotency window (24 h).
            idempotency_key = f"checkout-sub-{user_id}-{price_id}-{uuid.uuid4().hex[:8]}"

            checkout_session = await run_in_threadpool(
                stripe.checkout.Session.create,
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"user_id": user_id},
                idempotency_key=idempotency_key,
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
        endpoint_secret = config.STRIPE_WEBHOOK_SECRET or os.getenv("STRIPE_WEBHOOK_SECRET")
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            logger.error("Stripe webhook: invalid payload")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error("Stripe webhook: invalid signature: %s", e)
            raise

        event_type: str = event["type"]
        data_object = event["data"]["object"]

        from collections.abc import Awaitable, Callable

        handler_map: dict[str, Callable[[Any], Awaitable[None]]] = {
            "checkout.session.completed": self._dispatch_checkout_completed,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "customer.subscription.updated": self._handle_subscription_updated,
            # ── Dunning / payment-failure events ─────────────────────
            "invoice.payment_failed": self._handle_invoice_payment_failed,
            "invoice.payment_action_required": self._handle_invoice_payment_failed,
            "invoice.paid": self._handle_invoice_paid,
        }

        handler = handler_map.get(event_type)
        if handler:
            await handler(data_object)
        else:
            logger.info("Unhandled Stripe webhook event type: %s", event_type)

    async def _dispatch_checkout_completed(self, session: dict[str, Any]) -> None:
        """Route checkout.session.completed based on mode."""
        mode = session.get("mode")
        if mode == "subscription":
            await self._handle_checkout_session_completed(session)
        elif mode == "payment":
            await self._handle_payment_session_completed(session)
        else:
            logger.warning("Unknown checkout mode: %s", mode)

    # ── Subscription lifecycle handlers ──────────────────────────────

    async def _handle_checkout_session_completed(self, session: dict[str, Any]) -> None:
        user_id = session.get("metadata", {}).get("user_id")

        if not user_id:
            # Fallback: resolve via customer_id
            customer_id = session.get("customer")
            if customer_id:
                user_data = await self._get_user_data({"stripe_customer_id": customer_id}, "id")
                if user_data:
                    user_id = user_data.get("id")

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

        # Guard: only activate if the subscription is both active AND for our Pro plan
        if not self._subscription_is_active(sub):
            logger.warning(
                "Ignoring subscription activation: status not active. subscription=%s status=%s",
                subscription_id,
                getattr(sub, "status", "unknown"),
            )
            return

        if not self._subscription_matches_pro_plan(sub):
            logger.warning(
                "Ignoring subscription activation for unexpected price(s): subscription=%s prices=%s",
                subscription_id,
                sorted(self._extract_subscription_price_ids(sub)),
            )
            return

        current_period_end = datetime.fromtimestamp(
            cast(Any, sub).current_period_end,
            UTC,
        )

        await self._update_user_data(
            {
                "is_pro": True,
                "subscription_end_date": current_period_end.isoformat(),
                "cancel_at_period_end": sub.cancel_at_period_end,
            },
            {"id": user_id},
        )
        logger.info("Subscription activated for user %s", user_id)

    async def _handle_payment_session_completed(self, session: dict[str, Any]) -> None:
        """Handle one-time payments (e.g., Treats) by delegating to specialized service."""
        purchase_type = session.get("metadata", {}).get("type")

        if purchase_type == "treat_purchase":
            await self.treats_service.fulfill_treat_purchase(session)
        else:
            logger.info("Unhandled payment session type: %s", purchase_type)

    async def _handle_subscription_deleted(self, subscription: dict[str, Any]) -> None:
        customer_id = subscription.get("customer")
        if not customer_id:
            logger.warning("subscription.deleted missing customer_id")
            return

        await self._update_user_data(
            {
                "is_pro": False,
                "subscription_end_date": None,
                "cancel_at_period_end": False,
            },
            {"stripe_customer_id": customer_id},
        )
        logger.info("Subscription deleted for customer %s", customer_id)

    async def _handle_subscription_updated(self, subscription: dict[str, Any]) -> None:
        """Sync Pro status whenever a subscription is updated.

        Critical fix: we now check the subscription **status**.  If the status is
        not in _ACTIVE_STATUSES (e.g. 'past_due', 'unpaid', 'incomplete',
        'incomplete_expired', 'canceled') we revoke Pro access immediately so that
        a failed renewal never silently keeps a user in paid tier.
        """
        customer_id = subscription.get("customer")
        if not customer_id:
            logger.warning("Subscription updated event missing customer_id")
            return

        sub_status = subscription.get("status", "")
        is_currently_active = sub_status in _ACTIVE_STATUSES
        cancel_at_period_end = subscription.get("cancel_at_period_end", False)
        raw_period_end = subscription.get("current_period_end")

        if not is_currently_active:
            # Subscription has lapsed (payment failure, cancellation, etc.)
            # Revoke Pro access immediately to prevent free access after failed payment.
            await self._update_user_data(
                {
                    "is_pro": False,
                    "subscription_end_date": None,
                    "cancel_at_period_end": False,
                },
                {"stripe_customer_id": customer_id},
            )
            logger.warning(
                "Subscription status '%s' is not active — revoking Pro for customer %s",
                sub_status,
                customer_id,
            )
            return

        if raw_period_end is None:
            logger.warning(
                "Subscription updated event missing current_period_end for customer %s",
                customer_id,
            )
            return

        current_period_end = datetime.fromtimestamp(raw_period_end, UTC)

        await self._update_user_data(
            {
                "is_pro": True,
                "cancel_at_period_end": cancel_at_period_end,
                "subscription_end_date": current_period_end.isoformat(),
            },
            {"stripe_customer_id": customer_id},
        )
        logger.info(
            "Subscription updated for customer %s — status=%s cancel_at_period_end=%s",
            customer_id,
            sub_status,
            cancel_at_period_end,
        )

    # ── Dunning handlers ─────────────────────────────────────────────

    async def _handle_invoice_payment_failed(self, invoice: dict[str, Any]) -> None:
        """Triggered when Stripe fails to charge the customer for a renewal.

        We log the incident so that alerting/monitoring tools can surface it.
        Stripe's automatic Smart-Retries will reattempt the charge up to 4 times
        (configurable in the Dashboard).  If all retries are exhausted Stripe will
        emit customer.subscription.updated (status=past_due) or
        customer.subscription.deleted, which we already handle above.

        At this point we do NOT immediately revoke access — we let Smart Retries run
        first to give the customer a grace period.  Access is revoked only if the
        subscription transitions to past_due/unpaid via _handle_subscription_updated.
        """
        customer_id = invoice.get("customer")
        invoice_id = invoice.get("id")
        attempt_count = invoice.get("attempt_count", 0)
        next_payment_attempt = invoice.get("next_payment_attempt")

        logger.warning(
            "Invoice payment failed: invoice=%s customer=%s attempt=%s next_retry=%s",
            invoice_id,
            customer_id,
            attempt_count,
            next_payment_attempt,
        )

        # TODO: trigger an email/Sentry alert here so the team is notified of
        # churning users early.  Example:
        #   await self.notification_service.send_payment_failed_email(customer_id)

    async def _handle_invoice_paid(self, invoice: dict[str, Any]) -> None:
        """Triggered when a renewal invoice is paid successfully.

        Ensures that a customer who had their access revoked (e.g. after a failed
        payment that eventually succeeded on a Smart-Retry) gets their Pro status
        restored without requiring a new Checkout session.
        """
        customer_id = invoice.get("customer")
        subscription_id = invoice.get("subscription")

        if not customer_id or not subscription_id:
            return

        # Fetch the subscription to verify it is still active and matches Pro plan
        try:
            sub = await run_in_threadpool(stripe.Subscription.retrieve, subscription_id)
        except Exception as e:
            logger.error("invoice.paid: failed to retrieve subscription %s: %s", subscription_id, e)
            return

        if not self._subscription_is_active(sub) or not self._subscription_matches_pro_plan(sub):
            logger.info(
                "invoice.paid: subscription %s is not an active Pro plan — skipping restore",
                subscription_id,
            )
            return

        current_period_end = datetime.fromtimestamp(
            cast(Any, sub).current_period_end,
            UTC,
        )

        await self._update_user_data(
            {
                "is_pro": True,
                "subscription_end_date": current_period_end.isoformat(),
                "cancel_at_period_end": sub.cancel_at_period_end,
            },
            {"stripe_customer_id": customer_id},
        )
        logger.info(
            "invoice.paid: Pro access restored for customer %s via subscription %s",
            customer_id,
            subscription_id,
        )

    # ── Query helpers ────────────────────────────────────────────────

    async def get_subscription_status(self, user_id: str) -> dict[str, Any]:
        data = await self._get_user_data(
            {"id": user_id}, "is_pro, subscription_end_date, stripe_customer_id, cancel_at_period_end, treat_balance"
        )
        if data:
            return data

        return {
            "is_pro": False,
            "cancel_at_period_end": False,
            "treat_balance": 0,
        }

    async def create_portal_session(self, user_id: str, return_url: str | None = None) -> str:
        """Create a Stripe Customer Portal session."""
        user_data = await self._get_user_data({"id": user_id}, "stripe_customer_id")
        customer_id = user_data.get("stripe_customer_id") if user_data else None

        if not customer_id:
            raise ValueError("No customer ID found for user or user not found")

        safe_return_url = config.resolve_frontend_url(return_url, default_path="/subscription")
        portal_session = await run_in_threadpool(
            stripe.billing_portal.Session.create,
            customer=customer_id,
            return_url=safe_return_url,
        )
        return portal_session.url

    async def cancel_subscription(self, user_id: str) -> None:
        """Cancel active subscriptions (set to cancel at period end)."""
        user_data = await self._get_user_data({"id": user_id}, "stripe_customer_id")
        customer_id = user_data.get("stripe_customer_id") if user_data else None

        if not customer_id:
            raise ValueError("No subscription found or user not found")

        subscriptions = await run_in_threadpool(stripe.Subscription.list, customer=customer_id, status="active")
        if not subscriptions.data:
            raise ValueError("No active subscription to cancel")

        for sub in subscriptions.data:
            await run_in_threadpool(stripe.Subscription.modify, sub.id, cancel_at_period_end=True)
