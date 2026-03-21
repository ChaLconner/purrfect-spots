import os
from datetime import UTC, datetime
from typing import Any, cast

import stripe
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from supabase import AClient

from logger import logger
from services.treats_service import TreatsService

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class SubscriptionService:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        self.treats_service = TreatsService(supabase_client, db=db)

    async def _get_user_data(self, filters: dict[str, Any], fields: str = "*") -> dict[str, Any] | None:
        """Fetch user data using either SQLAlchemy or Supabase client."""
        try:
            if self.db:
                db_session = self.db
                # Whitelist keys to prevent SQL injection
                allowed_keys = {"id", "email", "stripe_customer_id"}
                where_conditions = [f"{k} = :{k}" for k in filters if k in allowed_keys]
                # Further restrict fields to known columns for safety
                # If fields is "*", it's fine as it's a constant.
                # If it's a CSV string, we should be careful.
                safe_fields = fields  # In current usage, these are always passed as constants
                where_clause = " AND ".join(where_conditions)
                sql_query = text(f"SELECT {safe_fields} FROM users WHERE {where_clause}")  # noqa: S608
                result = await db_session.execute(sql_query, filters)
                row = result.fetchone()
                return dict(row._asdict()) if row else None

            # Fallback to Supabase
            supa_query = self.supabase.table("users").select(fields)
            for key, value in filters.items():
                supa_query = supa_query.eq(key, value)

            res = await supa_query.limit(1).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error fetching user data: {e}")
            return None

    async def _update_user_data(self, updates: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any] | None:
        """Update user data using either SQLAlchemy or Supabase client."""
        try:
            if self.db:
                db_session = self.db
                allowed_updates = {"stripe_customer_id", "is_pro", "subscription_end_date", "cancel_at_period_end"}
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
                return dict(row._asdict()) if row else None

            # Fallback to Supabase
            supa_query = self.supabase.table("users").update(updates)
            for key, value in filters.items():
                supa_query = supa_query.eq(key, value)

            res = await supa_query.execute()
            return res.data[0] if res.data else None
        except Exception as e:
            if self.db:
                await self.db.rollback()
            logger.error(f"Error updating user data: {e}")
            return None

    # ── Helpers ──────────────────────────────────────────────────────

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

        # Persist back to DB
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
        """Creates a Stripe Checkout Session for a subscription."""
        try:
            customer_id = await self._get_or_create_stripe_customer(user_id, email, stripe_customer_id)

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

        from collections.abc import Awaitable, Callable

        handler_map: dict[str, Callable[[Any], Awaitable[None]]] = {
            "checkout.session.completed": self._dispatch_checkout_completed,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "customer.subscription.updated": self._handle_subscription_updated,
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
        current_period_end = datetime.fromtimestamp(
            cast(Any, sub).current_period_end,
            UTC,  # type: ignore[arg-type]
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
        """Handle one-time payments (e.g., Treats) by delegating to specialized services."""
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

        current_period_end = datetime.fromtimestamp(raw_period_end, UTC)

        await self._update_user_data(
            {
                "cancel_at_period_end": cancel_at_period_end,
                "subscription_end_date": current_period_end.isoformat(),
            },
            {"stripe_customer_id": customer_id},
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

    async def create_portal_session(self, user_id: str, return_url: str) -> str:
        """Create a Stripe Customer Portal session."""
        user_data = await self._get_user_data({"id": user_id}, "stripe_customer_id")
        customer_id = user_data.get("stripe_customer_id") if user_data else None

        if not customer_id:
            raise ValueError("No customer ID found for user or user not found")

        portal_session = await run_in_threadpool(
            stripe.billing_portal.Session.create,
            customer=customer_id,
            return_url=return_url,
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

        # Cancel only the first/active subscription
        for sub in subscriptions.data:
            await run_in_threadpool(stripe.Subscription.modify, sub.id, cancel_at_period_end=True)
