import asyncio
import inspect
import os
import time
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, cast

import stripe
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from stripe import SignatureVerificationError
from supabase import AClient

from app.config import config
from app.logger import logger
from app.repositories import UserRepository
from app.services.redis_service import RedisLockTimeout, RedisLockUnavailable, redis_service
from app.services.treats_service import TreatsService

# ── Stripe Initialisation ────────────────────────────────────────────
# Pin the API version so a dashboard upgrade never silently breaks
# webhook payload shapes or SDK behaviour.
stripe.api_key = config.STRIPE_SECRET_KEY or os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = config.STRIPE_API_VERSION

# Subscription statuses that grant Pro access.
_ACTIVE_STATUSES = frozenset({"active", "trialing"})
_CANCELLABLE_STATUSES = frozenset({"active", "trialing", "past_due", "incomplete"})

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

_PLAN_PRICE_CACHE: tuple[float, tuple[str, str | None], dict[str, Any]] | None = None
_PLAN_PRICE_CACHE_TTL_SECONDS = 300


class SubscriptionPersistenceError(RuntimeError):
    """Raised when billing state cannot be durably persisted."""


def _list_all_customer_subscriptions(customer_id: str) -> list[Any]:
    """List every Stripe subscription, not only the first 100 records."""
    collection = stripe.Subscription.list(
        customer=customer_id,
        status="all",
        limit=100,
    )
    auto_paging_iter = getattr(collection, "auto_paging_iter", None)
    if callable(auto_paging_iter):
        paged = list(auto_paging_iter())
        # MagicMock-based tests expose a callable mock but no real iterator.
        # Fall back to first-page data when that mock yields nothing.
        if paged or not getattr(collection, "data", None):
            return paged
    return list(getattr(collection, "data", []) or [])


async def cancel_customer_subscriptions(customer_id: str) -> int:
    """Stop future renewals for every live Stripe subscription of a customer."""
    if not customer_id:
        return 0

    try:
        subscriptions = await run_in_threadpool(_list_all_customer_subscriptions, customer_id)
    except stripe.error.InvalidRequestError as exc:
        if "No such customer" in str(exc) or getattr(exc, "code", None) == "resource_missing":
            logger.info("Stripe customer %s already absent; no subscriptions to cancel", customer_id)
            return 0
        raise

    canceled = 0
    for subscription in subscriptions:
        status = subscription.get("status") if isinstance(subscription, dict) else getattr(subscription, "status", None)
        if status in _CANCELLABLE_STATUSES:
            subscription_id = (
                subscription.get("id") if isinstance(subscription, dict) else getattr(subscription, "id", None)
            )
            if not subscription_id:
                logger.warning("Skipping cancellable Stripe subscription without ID for customer %s", customer_id)
                continue
            await run_in_threadpool(stripe.Subscription.modify, str(subscription_id), cancel_at_period_end=True)
            canceled += 1
    return canceled


class SubscriptionService:
    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        self.user_repo = UserRepository(supabase_client, db=db)
        self.treats_service = TreatsService(supabase_client, db=db)

    # ── DB helpers ────────────────────────────────────────────────────

    async def _get_user_data(self, filters: dict[str, Any], fields: str = "*") -> dict[str, Any] | None:
        """Fetch user data via UserRepository."""
        return await self.user_repo.get_user(filters, fields=fields)

    async def _update_user_data(self, updates: dict[str, Any], filters: dict[str, Any]) -> dict[str, Any] | None:
        """Update user data via UserRepository."""
        user = await self.user_repo.get_user_strict(filters)
        if not user or "id" not in user:
            return None
        success = await self.user_repo.update_user_strict(user["id"], updates)
        if not success:
            raise SubscriptionPersistenceError(f"Failed to persist subscription state for user {user['id']}")
        updated = await self.user_repo.get_user_strict({"id": user["id"]})
        if updated is None:
            raise SubscriptionPersistenceError(f"Failed to verify subscription state for user {user['id']}")
        return updated

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

    @staticmethod
    def _subscription_value(subscription: Any, key: str, default: Any = None) -> Any:
        if isinstance(subscription, dict):
            return subscription.get(key, default)
        return getattr(subscription, key, default)

    @staticmethod
    def _price_value(price: Any, key: str, default: Any = None) -> Any:
        if isinstance(price, dict):
            return price.get(key, default)
        return getattr(price, key, default)

    @classmethod
    def _normalise_public_price(cls, plan: str, price: Any) -> dict[str, Any]:
        """Expose only stable, non-sensitive Stripe Price fields to clients."""
        if cls._price_value(price, "active", True) is False:
            raise HTTPException(status_code=503, detail=f"Stripe {plan} subscription price is inactive")

        currency = str(cls._price_value(price, "currency", "")).lower()
        if not currency:
            raise HTTPException(status_code=503, detail="Stripe subscription price has no currency")

        raw_amount = cls._price_value(price, "unit_amount")
        if raw_amount is None:
            raw_amount = cls._price_value(price, "unit_amount_decimal")
        try:
            amount = int(Decimal(str(raw_amount)))
            if Decimal(str(raw_amount)) != Decimal(str(raw_amount)).to_integral_value() or amount < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError, TypeError):
            raise HTTPException(status_code=503, detail="Stripe subscription price has no valid amount") from None

        recurring = cls._price_value(price, "recurring")
        interval = cls._price_value(recurring, "interval") if recurring else None
        interval_count = cls._price_value(recurring, "interval_count", 1) if recurring else 1
        if not isinstance(interval, str) or not interval or not isinstance(interval_count, int) or interval_count < 1:
            raise HTTPException(status_code=503, detail="Stripe subscription price is not recurring")

        return {
            "plan": plan,
            "unit_amount": amount,
            "currency": currency,
            "interval": interval,
            "interval_count": interval_count,
        }

    async def get_plan_prices(self) -> dict[str, Any]:
        """Read current public plan prices from Stripe, never frontend constants."""
        monthly_id = config.STRIPE_PRO_PRICE_ID
        annual_id = config.STRIPE_PRO_ANNUAL_PRICE_ID
        if not monthly_id:
            raise HTTPException(status_code=503, detail="Subscription pricing is not configured")

        cache_key = (str(monthly_id), str(annual_id) if annual_id else None)
        global _PLAN_PRICE_CACHE
        now = time.monotonic()
        if _PLAN_PRICE_CACHE and _PLAN_PRICE_CACHE[0] > now and _PLAN_PRICE_CACHE[1] == cache_key:
            return _PLAN_PRICE_CACHE[2]

        try:

            async def no_annual_price() -> Any:
                return None

            monthly_price, annual_price = await asyncio.gather(
                run_in_threadpool(stripe.Price.retrieve, str(monthly_id)),
                run_in_threadpool(stripe.Price.retrieve, str(annual_id)) if annual_id else no_annual_price(),
            )
            prices: dict[str, Any] = {
                "monthly": self._normalise_public_price("monthly", monthly_price),
                "annual": self._normalise_public_price("annual", annual_price) if annual_price else None,
            }
        except HTTPException:
            raise
        except stripe.error.StripeError as exc:
            logger.error("Failed to retrieve subscription prices from Stripe: %s", exc, exc_info=True)
            raise HTTPException(status_code=503, detail="Subscription pricing temporarily unavailable") from exc

        _PLAN_PRICE_CACHE = (now + _PLAN_PRICE_CACHE_TTL_SECONDS, cache_key, prices)
        return prices

    async def _apply_subscription_snapshot(
        self,
        subscription: Any,
        *,
        user_id: str | None,
        event_id: str | None,
        event_created_at: datetime | None,
    ) -> bool:
        """Persist one ordered subscription snapshot and reconcile customer access."""
        subscription_id = self._subscription_value(subscription, "id")
        customer_id = self._subscription_value(subscription, "customer")
        status = str(self._subscription_value(subscription, "status", ""))
        period_end = self._subscription_value(subscription, "current_period_end")
        period_end_dt = datetime.fromtimestamp(period_end, UTC) if period_end else None
        is_pro_plan = self._subscription_matches_pro_plan(subscription)

        if not subscription_id or not customer_id:
            raise ValueError("Subscription event is missing subscription or customer ID")

        # An active Stripe subscription must have a finite period end. Fail
        # closed if a malformed/future payload omits it; otherwise an active
        # row with NULL end date could grant indefinite Pro access.
        if status in _ACTIVE_STATUSES and period_end_dt is None:
            logger.error("Ignoring active subscription %s without current_period_end", subscription_id)
            return False

        if event_id and event_created_at:
            rpc_result = await self.supabase.rpc(
                "apply_stripe_subscription_event",
                {
                    "p_subscription_id": str(subscription_id),
                    "p_customer_id": str(customer_id),
                    "p_user_id": user_id,
                    "p_status": status,
                    "p_is_pro_plan": is_pro_plan,
                    "p_cancel_at_period_end": bool(
                        self._subscription_value(subscription, "cancel_at_period_end", False)
                    ),
                    "p_current_period_end": period_end_dt.isoformat() if period_end_dt else None,
                    "p_event_id": event_id,
                    "p_event_created_at": event_created_at.isoformat(),
                },
            ).execute()
            raw_data = getattr(rpc_result, "data", None)
            if isinstance(raw_data, list):
                raw_data = raw_data[0] if raw_data else None
            if not isinstance(raw_data, dict):
                raise SubscriptionPersistenceError("Subscription state RPC returned no result")
            if not raw_data.get("user_found", True):
                logger.warning("Subscription event %s has no matching user for customer %s", event_id, customer_id)
            applied = bool(raw_data.get("applied", False))
            if applied and raw_data.get("user_found", True):
                await self._invalidate_auth_cache_for_customer(str(customer_id))
            return applied

        # Direct calls remain useful for unit-level handlers and migration rollback checks.
        if status in _ACTIVE_STATUSES and not is_pro_plan:
            logger.warning("Ignoring subscription %s with unexpected Pro price", subscription_id)
            return False
        if status in _ACTIVE_STATUSES and period_end_dt is None:
            logger.warning("Ignoring subscription %s without current_period_end", subscription_id)
            return False
        if status in _ACTIVE_STATUSES:
            await self._update_user_data(
                {
                    "is_pro": True,
                    "cancel_at_period_end": bool(self._subscription_value(subscription, "cancel_at_period_end", False)),
                    "subscription_end_date": period_end_dt.isoformat() if period_end_dt else None,
                },
                {"id": user_id} if user_id else {"stripe_customer_id": customer_id},
            )
        else:
            await self._revoke_pro_status_by_customer_id(str(customer_id))
        return True

    async def _invalidate_auth_cache_for_customer(self, customer_id: str) -> None:
        """Drop cached auth snapshots after billing entitlement changes."""
        try:
            user_data = await self._get_user_data({"stripe_customer_id": customer_id}, "id")
            user_id = user_data.get("id") if user_data else None
            if not user_id:
                return
            # Lazy import avoids the auth-middleware/service import cycle.
            from app.middleware.auth_middleware import invalidate_user_auth_cache

            await invalidate_user_auth_cache(str(user_id))
        except Exception:
            # Durable billing state is already committed; cache invalidation is
            # best-effort and the expiry guard still fails closed.
            logger.warning("Failed to invalidate auth cache for Stripe customer %s", customer_id, exc_info=True)

    async def _claim_webhook_event(self, event_id: str, event_type: str, event_created_at: datetime) -> bool:
        result = await self.supabase.rpc(
            "claim_stripe_webhook_event",
            {
                "p_event_id": event_id,
                "p_event_type": event_type,
                "p_event_created_at": event_created_at.isoformat(),
            },
        ).execute()
        raw_data = getattr(result, "data", None)
        if isinstance(raw_data, list):
            raw_data = raw_data[0] if raw_data else None
        if isinstance(raw_data, dict):
            return bool(raw_data.get("claimed", False))
        return bool(raw_data)

    async def _complete_webhook_event(self, event_id: str) -> None:
        await self.supabase.rpc("complete_stripe_webhook_event", {"p_event_id": event_id}).execute()

    async def _fail_webhook_event(self, event_id: str, error_message: str) -> None:
        await self.supabase.rpc(
            "fail_stripe_webhook_event",
            {"p_event_id": event_id, "p_error": error_message[:1000]},
        ).execute()

    async def _get_or_create_stripe_customer(
        self, user_id: str, email: str, existing_customer_id: str | None = None, force_create: bool = False
    ) -> str:
        """Resolve or create a Stripe Customer ID for the given user."""
        if existing_customer_id and not force_create:
            return existing_customer_id

        db_customer_id = None
        if not force_create:
            user_data = await self._get_user_data({"id": user_id}, "stripe_customer_id")
            if user_data:
                db_customer_id = user_data.get("stripe_customer_id")

        if db_customer_id and not force_create:
            return cast(str, db_customer_id)

        # Create in Stripe (sync SDK → threadpool)
        customer_idempotency_key = (
            f"stripe-customer-recreate-{user_id}-{existing_customer_id or 'unknown'}"
            if force_create
            else f"stripe-customer-{user_id}"
        )
        customer = await run_in_threadpool(
            stripe.Customer.create,
            email=email,
            metadata={"user_id": user_id},
            idempotency_key=customer_idempotency_key,
        )
        customer_id: str = customer.id

        await self._update_user_data({"stripe_customer_id": customer_id}, {"id": user_id})
        return customer_id

    async def _ensure_no_live_subscription(self, customer_id: str) -> None:
        """Prevent a second billable subscription for the same customer."""
        try:
            subscriptions = await run_in_threadpool(_list_all_customer_subscriptions, customer_id)
        except stripe.error.InvalidRequestError as exc:
            if "No such customer" in str(exc) or getattr(exc, "code", None) == "resource_missing":
                return
            raise

        for subscription in subscriptions:
            status = (
                subscription.get("status") if isinstance(subscription, dict) else getattr(subscription, "status", None)
            )
            if status in _CANCELLABLE_STATUSES:
                raise HTTPException(
                    status_code=409,
                    detail="An active or pending subscription already exists. Use the customer portal to manage it.",
                )

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

            # One distributed lock covers customer resolution, live-subscription
            # check, and Stripe session creation. Stable Stripe idempotency key
            # handles retries after the lock is released while checkout remains open.
            async with redis_service.lock(f"subscription:checkout:{user_id}", ttl=90, wait_timeout=15):
                customer_id = await self._get_or_create_stripe_customer(user_id, email, stripe_customer_id)
                await self._ensure_no_live_subscription(customer_id)

                idempotency_key = f"checkout-sub-{user_id}-{price_id}-{customer_id}"
                try:
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
                except stripe.error.InvalidRequestError as e:
                    if "No such customer" in str(e) or getattr(e, "code", None) == "resource_missing":
                        logger.warning(
                            "Stripe customer %s not found. Creating new customer for user %s", customer_id, user_id
                        )
                        customer_id = await self._get_or_create_stripe_customer(
                            user_id,
                            email,
                            existing_customer_id=customer_id,
                            force_create=True,
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
                            idempotency_key=f"{idempotency_key}-retry-{customer_id}",
                        )
                    else:
                        raise
                return {
                    "checkout_url": checkout_session.url or "",
                    "session_id": checkout_session.id,
                }
        except RedisLockTimeout as exc:
            raise HTTPException(status_code=409, detail="Another checkout is already being created") from exc
        except RedisLockUnavailable as exc:
            raise HTTPException(status_code=503, detail="Checkout temporarily unavailable") from exc
        except stripe.error.StripeError as e:
            logger.error("Stripe error creating checkout session: %s", e, exc_info=True)
            raise HTTPException(status_code=400, detail=f"Stripe error: {e.user_message or str(e)}") from e
        except Exception as e:
            logger.error("Failed to create checkout session: %s", e, exc_info=True)
            raise

    # ── Webhook ──────────────────────────────────────────────────────

    async def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        """Handles Stripe Webhook events."""
        endpoint_secret = config.STRIPE_WEBHOOK_SECRET or os.getenv("STRIPE_WEBHOOK_SECRET")
        if not endpoint_secret:
            logger.error("Stripe webhook received while STRIPE_WEBHOOK_SECRET is not configured")
            raise SubscriptionPersistenceError("Stripe webhook secret is not configured")
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError:
            logger.error("Stripe webhook: invalid payload")
            raise
        except SignatureVerificationError as e:
            logger.error("Stripe webhook: invalid signature: %s", e)
            raise

        event_type: str = str(event["type"])
        event_id = str(event.get("id") or "")
        event_created = event.get("created")
        if not event_id or not event_created:
            raise ValueError("Stripe webhook event is missing id or created timestamp")
        event_created_at = datetime.fromtimestamp(int(event_created), UTC)
        data_object = event["data"]["object"]

        from collections.abc import Awaitable, Callable

        handler_map: dict[str, Callable[[Any, str, datetime], Awaitable[None]]] = {
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
            if not await self._claim_webhook_event(event_id, event_type, event_created_at):
                logger.info("Skipping duplicate or concurrently processed Stripe event %s", event_id)
                return
            try:
                await handler(data_object, event_id, event_created_at)
            except Exception as exc:
                try:
                    await self._fail_webhook_event(event_id, str(exc))
                except Exception:
                    logger.exception("Failed to record Stripe webhook failure for %s", event_id)
                raise
            await self._complete_webhook_event(event_id)
        else:
            logger.info("Unhandled Stripe webhook event type: %s", event_type)

    async def _dispatch_checkout_completed(
        self, session: dict[str, Any], event_id: str | None = None, event_created_at: datetime | None = None
    ) -> None:
        """Route checkout.session.completed based on mode."""
        mode = session.get("mode")
        if mode == "subscription":
            await self._handle_checkout_session_completed(session, event_id, event_created_at)
        elif mode == "payment":
            await self._handle_payment_session_completed(session)
        else:
            logger.warning("Unknown checkout mode: %s", mode)

    # ── Subscription lifecycle handlers ──────────────────────────────

    async def _handle_checkout_session_completed(
        self, session: dict[str, Any], event_id: str | None = None, event_created_at: datetime | None = None
    ) -> None:
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

        await self._apply_subscription_snapshot(
            sub,
            user_id=user_id,
            event_id=event_id,
            event_created_at=event_created_at,
        )
        logger.info("Subscription activated for user %s", user_id)

    async def _activate_pro_status_for_user(self, sub: Any, query_filter: dict[str, Any]) -> None:
        """Update user record with active Pro subscription metadata."""
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
            query_filter,
        )

    async def _handle_payment_session_completed(self, session: dict[str, Any]) -> None:
        """Handle one-time payments (e.g., Treats) by delegating to specialized service."""
        purchase_type = session.get("metadata", {}).get("type")

        if purchase_type == "treat_purchase":
            await self.treats_service.fulfill_treat_purchase(session)
        else:
            logger.info("Unhandled payment session type: %s", purchase_type)

    async def _revoke_pro_status_by_customer_id(self, customer_id: str) -> None:
        """Revoke Pro subscription status for a customer."""
        await self._update_user_data(
            {
                "is_pro": False,
                "subscription_end_date": None,
                "cancel_at_period_end": False,
            },
            {"stripe_customer_id": customer_id},
        )

    async def _handle_subscription_deleted(
        self, subscription: dict[str, Any], event_id: str | None = None, event_created_at: datetime | None = None
    ) -> None:
        customer_id = subscription.get("customer")
        if not customer_id:
            logger.warning("subscription.deleted missing customer_id")
            return

        await self._apply_subscription_snapshot(
            subscription,
            user_id=None,
            event_id=event_id,
            event_created_at=event_created_at,
        )
        logger.info("Subscription deleted for customer %s", customer_id)

    async def _handle_subscription_updated(
        self, subscription: dict[str, Any], event_id: str | None = None, event_created_at: datetime | None = None
    ) -> None:
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

        await self._apply_subscription_snapshot(
            subscription,
            user_id=None,
            event_id=event_id,
            event_created_at=event_created_at,
        )
        logger.info(
            "Subscription updated for customer %s — status=%s cancel_at_period_end=%s",
            customer_id,
            subscription.get("status", ""),
            subscription.get("cancel_at_period_end", False),
        )

    # ── Dunning handlers ─────────────────────────────────────────────

    async def _handle_invoice_payment_failed(
        self, invoice: dict[str, Any], event_id: str | None = None, event_created_at: datetime | None = None
    ) -> None:
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

        # SEC: Alert team on payment failure so churning users are caught early.
        try:
            import sentry_sdk

            sentry_sdk.capture_message(
                f"Invoice payment failed: invoice={invoice_id} customer={customer_id} attempt={attempt_count}",
                level="warning",
            )
        except Exception:
            # Sentry alerting is best-effort; never let it break webhook handling.
            pass

    async def _handle_invoice_paid(
        self, invoice: dict[str, Any], event_id: str | None = None, event_created_at: datetime | None = None
    ) -> None:
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
            raise SubscriptionPersistenceError(
                f"Failed to retrieve Stripe subscription {subscription_id} while processing invoice.paid"
            ) from e

        if not self._subscription_is_active(sub) or not self._subscription_matches_pro_plan(sub):
            logger.info(
                "invoice.paid: subscription %s is not an active Pro plan — skipping restore",
                subscription_id,
            )
            return

        await self._apply_subscription_snapshot(
            sub,
            user_id=None,
            event_id=event_id,
            event_created_at=event_created_at,
        )
        logger.info(
            "invoice.paid: Pro access restored for customer %s via subscription %s",
            customer_id,
            subscription_id,
        )

    async def _list_billing_users(self) -> list[dict[str, str]]:
        """Read all users with Stripe customer IDs in bounded pages."""
        users: list[dict[str, str]] = []
        offset = 0
        page_size = 500
        while True:
            query = self.supabase.table("users").select("id,stripe_customer_id")
            response_value: Any = query.range(offset, offset + page_size - 1).execute()
            if inspect.isawaitable(response_value):
                response_value = await response_value
            rows = getattr(response_value, "data", None)
            if not isinstance(rows, list):
                break
            for row in rows:
                if not isinstance(row, dict):
                    continue
                user_id = row.get("id")
                customer_id = row.get("stripe_customer_id")
                if user_id and customer_id:
                    users.append({"id": str(user_id), "stripe_customer_id": str(customer_id)})
            if len(rows) < page_size:
                break
            offset += page_size
        return users

    async def _reconcile_customer(self, user_id: str, customer_id: str, run_at: datetime) -> int:
        """Sync one customer's complete Stripe subscription set."""
        try:
            subscriptions = await run_in_threadpool(_list_all_customer_subscriptions, customer_id)
        except stripe.error.InvalidRequestError as exc:
            if "No such customer" in str(exc) or getattr(exc, "code", None) == "resource_missing":
                logger.warning("Reconciliation found deleted Stripe customer %s", customer_id)
                await self._revoke_pro_status_by_customer_id(customer_id)
                return 0
            raise

        has_live_pro_subscription = False
        reconciled = 0
        for subscription in subscriptions:
            subscription_id = self._subscription_value(subscription, "id")
            if not subscription_id:
                logger.warning("Skipping Stripe subscription without ID for customer %s", customer_id)
                continue
            subscription_customer = str(self._subscription_value(subscription, "customer", customer_id))
            if subscription_customer != customer_id:
                logger.warning(
                    "Skipping subscription %s returned for unexpected customer %s", subscription_id, customer_id
                )
                continue

            status = str(self._subscription_value(subscription, "status", ""))
            period_end = self._subscription_value(subscription, "current_period_end")
            period_end_is_valid = isinstance(period_end, (int, float)) and period_end > 0
            if self._subscription_matches_pro_plan(subscription) and (
                (status in _ACTIVE_STATUSES and period_end_is_valid)
                or (
                    status == "past_due"
                    and period_end_is_valid
                    and datetime.fromtimestamp(float(period_end), UTC) > run_at
                )
            ):
                has_live_pro_subscription = True

            event_id = f"reconciliation:{int(run_at.timestamp())}:{subscription_id}"
            applied = await self._apply_subscription_snapshot(
                subscription,
                user_id=user_id,
                event_id=event_id,
                event_created_at=run_at,
            )
            reconciled += int(applied)

        # An empty Stripe set, malformed active subscription, or only a
        # non-Pro price must revoke stale local entitlement immediately.
        if not has_live_pro_subscription:
            await self._revoke_pro_status_by_customer_id(customer_id)
        return reconciled

    async def reconcile_all_subscriptions(self) -> dict[str, int]:
        """Periodically repair local billing state from Stripe's source of truth."""
        try:
            async with redis_service.lock(
                "subscription:reconciliation",
                ttl=max(300, int(config.SUBSCRIPTION_RECONCILIATION_INTERVAL_SECONDS) * 2),
                wait_timeout=0.1,
            ):
                users = await self._list_billing_users()
                run_at = datetime.now(UTC)
                reconciled = 0
                failed = 0
                for user in users:
                    try:
                        reconciled += await self._reconcile_customer(user["id"], user["stripe_customer_id"], run_at)
                    except Exception:
                        failed += 1
                        logger.error(
                            "Subscription reconciliation failed for user %s/customer %s",
                            user["id"],
                            user["stripe_customer_id"],
                            exc_info=True,
                        )
                return {
                    "customers_scanned": len(users),
                    "subscriptions_reconciled": reconciled,
                    "failed_customers": failed,
                    "skipped": 0,
                }
        except RedisLockTimeout:
            logger.info("Subscription reconciliation already running on another instance")
            return {"customers_scanned": 0, "subscriptions_reconciled": 0, "failed_customers": 0, "skipped": 1}
        except RedisLockUnavailable as exc:
            raise SubscriptionPersistenceError("Subscription reconciliation lock unavailable") from exc

    # ── Query helpers ────────────────────────────────────────────────

    async def get_subscription_status(self, user_id: str) -> dict[str, Any]:
        data = await self._get_user_data(
            {"id": user_id}, "is_pro, subscription_end_date, stripe_customer_id, cancel_at_period_end, treat_balance"
        )
        if data:
            end_date = data.get("subscription_end_date")
            if data.get("is_pro") and end_date:
                try:
                    parsed_end = end_date if isinstance(end_date, datetime) else datetime.fromisoformat(str(end_date))
                    if parsed_end <= datetime.now(UTC):
                        data = {**data, "is_pro": False, "cancel_at_period_end": False}
                except (TypeError, ValueError):
                    logger.warning("Invalid subscription_end_date for user %s", user_id)
                    data = {**data, "is_pro": False, "cancel_at_period_end": False}
            elif data.get("is_pro"):
                # Never expose a paid entitlement without a finite expiry.
                data = {**data, "is_pro": False, "cancel_at_period_end": False}
            return data

        return {
            "is_pro": False,
            "cancel_at_period_end": False,
            "treat_balance": 0,
        }

    async def _require_stripe_customer_id(self, user_id: str, error_msg: str) -> str:
        """Fetch stripe customer id for user or raise ValueError."""
        user_data = await self._get_user_data({"id": user_id}, "stripe_customer_id")
        customer_id = user_data.get("stripe_customer_id") if user_data else None
        if not customer_id:
            raise ValueError(error_msg)
        return cast(str, customer_id)

    async def create_portal_session(self, user_id: str, return_url: str | None = None) -> str:
        """Create a Stripe Customer Portal session."""
        customer_id = await self._require_stripe_customer_id(user_id, "No customer ID found for user or user not found")

        safe_return_url = config.resolve_frontend_url(return_url, default_path="/subscription")
        try:
            portal_session = await run_in_threadpool(
                stripe.billing_portal.Session.create,
                customer=customer_id,
                return_url=safe_return_url,
            )
            return portal_session.url
        except stripe.error.InvalidRequestError as e:
            if "No such customer" in str(e) or getattr(e, "code", None) == "resource_missing":
                logger.warning("Stripe customer %s not found when creating portal. Clearing invalid ID.", customer_id)
                await self._update_user_data({"stripe_customer_id": None}, {"id": user_id})
                raise ValueError("Stripe customer record invalid or missing. Please subscribe first.") from e
            raise

    async def cancel_subscription(self, user_id: str) -> None:
        """Cancel active, trialing, past-due, or incomplete subscriptions."""
        customer_id = await self._require_stripe_customer_id(user_id, "No subscription found or user not found")
        canceled = await cancel_customer_subscriptions(customer_id)
        if not canceled:
            raise ValueError("No active or pending subscription to cancel")
