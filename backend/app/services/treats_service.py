import os
import time
from typing import Any, ClassVar, cast

import stripe
from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from supabase import AClient

from app.config import config
from app.logger import logger, sanitize_log_value
from app.schemas.notification import NotificationType
from app.services.notification_service import NotificationService
from app.utils.cache import cached_leaderboard, invalidate_leaderboard_cache

# Pin the same API version as subscription_service to ensure consistent
# webhook payload shapes across all Stripe SDK calls in this service.
stripe.api_key = config.STRIPE_SECRET_KEY or os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = config.STRIPE_API_VERSION

_PACKAGES_CACHE_TTL = 300  # 5 minutes


from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import UserRepository


class TreatsService:
    _packages_cache: ClassVar[dict[str, dict[str, Any]] | None] = None
    _packages_cache_ts: ClassVar[float] = 0.0

    def __init__(self, supabase_client: AClient, db: AsyncSession | None = None) -> None:
        self.supabase = supabase_client
        self.db = db
        self.user_repo = UserRepository(supabase_client, db=db)
        self.TRANSACTION_COLUMNS = "id, from_user_id, to_user_id, photo_id, amount, transaction_type, created_at"
        self.notification_service = NotificationService(supabase_client)

    # ── Give treats ──────────────────────────────────────────────────

    async def give_treat(
        self, from_user_id: str, photo_id: str, amount: int, jwt_token: str | None = None
    ) -> dict[str, Any]:
        """Give treats to a photo owner (fully atomic via DB RPC)."""
        try:
            if self.db:
                result = await self._give_treat_sql(from_user_id, photo_id, amount)
            else:
                result = await self._give_treat_supabase(from_user_id, photo_id, amount)

            # Fire-and-forget notification
            to_user_id = result.get("to_user_id")
            if to_user_id:
                await self._send_treat_notification(from_user_id, to_user_id, photo_id, amount)
            else:
                await self._send_treat_notification_fallback(from_user_id, photo_id, amount)

            # Invalidate leaderboard cache so updates reflect immediately
            await invalidate_leaderboard_cache()

            return {
                "success": True,
                "message": f"Gave {amount} treats",
                "new_balance": result.get("new_balance"),
                "amount_given": amount,
            }

        except ValueError:
            if self.db:
                await self.db.rollback()
            raise
        except Exception as e:
            if self.db:
                await self.db.rollback()
            logger.error("Give treat failed: %s", e, exc_info=True)
            raise

    async def _give_treat_sql(self, from_user_id: str, photo_id: str, amount: int) -> dict[str, Any]:
        """Give treats using SQLAlchemy RPC call."""
        if not self.db:
            raise ValueError("Database session is required for SQL RPC")
        db_session = self.db
        query = text(
            "SELECT rpc.success, rpc.error, rpc.to_user_id, rpc.new_balance "
            "FROM json_to_record(public.give_treat_atomic("
            "CAST(:p_from_user_id AS UUID), CAST(:p_photo_id AS UUID), CAST(:p_amount AS INTEGER)"
            ")) AS rpc(success BOOLEAN, error TEXT, to_user_id UUID, new_balance INTEGER)"
        )
        result = await db_session.execute(
            query,
            {
                "p_from_user_id": from_user_id,
                "p_photo_id": photo_id,
                "p_amount": amount,
            },
        )
        row = result.fetchone()
        if not row:
            raise ValueError("Unknown error (no response from RPC)")

        await db_session.commit()

        if not row[0]:  # success
            raise ValueError(row[1] or "Unknown error")  # error

        return {"to_user_id": row[2], "new_balance": row[3]}

    async def _give_treat_supabase(self, from_user_id: str, photo_id: str, amount: int) -> dict[str, Any]:
        """Give treats using Supabase RPC call."""
        from app.utils.supabase_client import get_async_supabase_admin_client

        admin_client = await get_async_supabase_admin_client()

        res = await admin_client.rpc(
            "give_treat_atomic",
            {
                "p_from_user_id": from_user_id,
                "p_photo_id": photo_id,
                "p_amount": amount,
            },
        ).execute()

        raw_data = res.data
        if isinstance(raw_data, dict):
            result = cast(dict[str, Any], raw_data)
        elif isinstance(raw_data, list) and raw_data and isinstance(raw_data[0], dict):
            result = cast(dict[str, Any], raw_data[0])
        else:
            raise ValueError("Unknown error (no response from RPC)")

        if not result.get("success"):
            raise ValueError(result.get("error", "Unknown error"))

        return result

    async def _send_treat_notification(self, from_user_id: str, to_user_id: str, photo_id: str, amount: int) -> None:
        """Send notification when treats are given."""
        try:
            actor_name = "Someone"
            if self.db:
                query = text("SELECT name FROM users WHERE id = :u_id LIMIT 1")
                result = await self.db.execute(query, {"u_id": from_user_id})
                row = result.fetchone()
                if row:
                    actor_name = row[0]
            else:
                actor_res = await self.supabase.table("users").select("name").eq("id", from_user_id).single().execute()
                actor_data = cast(dict[str, Any] | None, actor_res.data)
                actor_name = cast(str, actor_data.get("name")) if actor_data else "Someone"

            await self.notification_service.create_notification(
                user_id=to_user_id,
                actor_id=from_user_id,
                type=NotificationType.TREAT.value,
                title="Treat Received!",
                message=f"{actor_name} sent you {amount} treats!",
                resource_id=photo_id,
                resource_type="photo",
            )
        except Exception as e:
            logger.error("Failed to send treat notification: %s", e)

    async def _send_treat_notification_fallback(self, from_user_id: str, photo_id: str, amount: int) -> None:
        """Fallback notification path when to_user_id not returned by RPC."""
        try:
            to_user_id = None
            if self.db:
                query = text("SELECT user_id FROM cat_photos WHERE id = :p_id LIMIT 1")
                result = await self.db.execute(query, {"p_id": photo_id})
                row = result.fetchone()
                if row:
                    to_user_id = row[0]
            else:
                photo_res = (
                    await self.supabase.table("cat_photos").select("user_id").eq("id", photo_id).single().execute()
                )
                if photo_res.data:
                    photo_data = cast(dict[str, Any], photo_res.data)
                    to_user_id = cast(str, photo_data["user_id"])

            if to_user_id:
                await self._send_treat_notification(from_user_id, to_user_id, photo_id, amount)
        except Exception as e:
            logger.error("Failed to send treat notification (fallback): %s", e)

    # ── Purchase checkout ────────────────────────────────────────────

    async def purchase_treats_checkout(
        self,
        user_id: str,
        package: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        stripe_customer_id: str | None = None,
    ) -> dict[str, str]:
        """Create a Stripe Checkout Session for treat purchase."""
        try:
            # Build session params — link to customer if available
            session_params: dict[str, Any] = {
                "payment_method_types": ["card"],
                "line_items": [{"price": price_id, "quantity": 1}],
                "mode": "payment",
                "success_url": success_url,
                "cancel_url": cancel_url,
                "metadata": {
                    "user_id": user_id,
                    "type": "treat_purchase",
                    "package": package,
                },
                "payment_intent_data": {"metadata": {"user_id": user_id, "package": package}},
            }

            # Associate with existing Stripe customer for unified history
            cust_id = stripe_customer_id
            if not cust_id:
                user_data = await self.user_repo.get_user({"id": user_id}, fields="stripe_customer_id")
                cust_id = user_data.get("stripe_customer_id") if user_data else None

            if cust_id:
                session_params["customer"] = cust_id

            # Idempotency key: 60-second bucket deduplicates double-clicks
            # while still allowing a fresh session after the window expires.
            time_bucket = int(time.time()) // 60
            idempotency_key = f"checkout-treat-{user_id}-{package}-{time_bucket}"
            try:
                checkout_session = await run_in_threadpool(
                    lambda: stripe.checkout.Session.create(**session_params, idempotency_key=idempotency_key)
                )
            except stripe.error.InvalidRequestError as e:
                if "No such customer" in str(e) or getattr(e, "code", None) == "resource_missing":
                    logger.warning(
                        "Stripe customer %s invalid for user %s. Removing invalid customer ID and retrying.",
                        cust_id,
                        user_id,
                    )
                    await self.user_repo.update_user(user_id, {"stripe_customer_id": None})
                    session_params.pop("customer", None)
                    new_idempotency_key = f"checkout-treat-{user_id}-{package}-{time_bucket}-retry"
                    checkout_session = await run_in_threadpool(
                        lambda: stripe.checkout.Session.create(**session_params, idempotency_key=new_idempotency_key)
                    )
                else:
                    raise
            return {
                "checkout_url": checkout_session.url or "",
                "session_id": checkout_session.id,
            }
        except stripe.error.StripeError as e:
            logger.error("Stripe purchase session creation failed: %s", e, exc_info=True)
            raise HTTPException(status_code=400, detail=f"Stripe error: {e.user_message or str(e)}") from e
        except Exception as e:
            logger.error("Stripe purchase session creation failed: %s", e, exc_info=True)
            raise

    # ── Balance & Transactions ───────────────────────────────────────

    async def get_balance(self, user_id: str) -> dict[str, Any]:
        if self.db:
            try:
                # Get balance
                balance_query = text("SELECT treat_balance FROM users WHERE id = :u_id LIMIT 1")
                balance_res = await self.db.execute(balance_query, {"u_id": user_id})
                balance_row = balance_res.fetchone()
                balance = balance_row[0] if balance_row else 0

                # Get recent transactions
                trans_query = text(
                    "SELECT id, from_user_id, to_user_id, photo_id, amount, transaction_type, created_at "
                    "FROM treats_transactions "
                    "WHERE from_user_id = :u_id OR to_user_id = :u_id "
                    "ORDER BY created_at DESC "
                    "LIMIT 10"
                )
                trans_res = await self.db.execute(trans_query, {"u_id": user_id})
                recent_transactions = [dict(row._mapping) for row in trans_res]

                return {
                    "balance": balance,
                    "recent_transactions": recent_transactions,
                }
            except Exception as e:
                logger.warning(f"SQLAlchemy get_balance failed, falling back to Supabase: {e}")
                # Fallback to Supabase

        supa_user_res = (
            await self.supabase.table("users").select("treat_balance").eq("id", user_id).maybe_single().execute()
        )
        user_data_balance = cast(dict[str, Any] | None, supa_user_res.data) if supa_user_res else None
        balance = (
            cast(int, user_data_balance["treat_balance"])
            if user_data_balance and "treat_balance" in user_data_balance
            else 0
        )

        supa_trans_res = (
            await self.supabase.table("treats_transactions")
            .select(self.TRANSACTION_COLUMNS)
            .or_(f"from_user_id.eq.{user_id},to_user_id.eq.{user_id}")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        return {
            "balance": balance,
            "recent_transactions": cast(list[dict[str, Any]], supa_trans_res.data or []),
        }

    # ── Leaderboard ──────────────────────────────────────────────────

    @cached_leaderboard
    async def get_leaderboard(self, period: str = "all_time", limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        """Top treat receivers (Most Spoiled Cats owners)."""
        try:
            if self.db:
                query = text("SELECT * FROM get_leaderboard(:p_period::text, :p_limit::integer, :p_offset::integer)")
                result = await self.db.execute(query, {"p_period": period, "p_limit": limit, "p_offset": offset})
                rows = [dict(row._mapping) for row in result]
            else:
                res = await self.supabase.rpc(
                    "get_leaderboard", {"p_period": period, "p_limit": limit, "p_offset": offset}
                ).execute()
                rows = cast(list[dict[str, Any]], res.data or [])

            return rows
        except Exception as e:
            logger.warning("SQL leaderboard fetch failed, checking fallback: %s", e)
            if self.db:
                await self.db.rollback()
            # Fallback for all_time if RPC fails or during migration
            if period == "all_time":
                return await self._get_leaderboard_fallback(limit=limit, offset=offset)
            return []

    async def _get_leaderboard_fallback(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        if self.db:
            try:
                query = text(
                    "SELECT id, name, username, picture, total_treats_received "
                    "FROM users "
                    "ORDER BY total_treats_received DESC "
                    "LIMIT :limit OFFSET :offset"
                )
                result = await self.db.execute(query, {"limit": limit, "offset": offset})
                return [dict(row._mapping) for row in result]
            except Exception as e:
                logger.warning(f"SQLAlchemy _get_leaderboard_fallback failed: {e}")
                await self.db.rollback()

        res = (
            await self.supabase.table("users")
            .select("id, name, username, picture, total_treats_received")
            .order("total_treats_received", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return cast(list[dict[str, Any]], res.data or [])

    # ── Packages (cached) ────────────────────────────────────────────

    async def get_packages(self) -> dict[str, dict[str, Any]]:
        """Fetch treat packages from database with in-memory caching."""
        now = time.monotonic()
        cached_packages = type(self)._packages_cache
        if cached_packages is not None and (now - type(self)._packages_cache_ts) < _PACKAGES_CACHE_TTL:
            return cached_packages

        try:
            data = []
            if self.db:
                query = text("SELECT * FROM treat_packages WHERE is_active = TRUE")
                result = await self.db.execute(query)
                data = [dict(row._mapping) for row in result]
            else:
                res = await self.supabase.table("treat_packages").select("*").eq("is_active", True).execute()
                data = cast(list[dict[str, Any]], res.data or [])

            packages: dict[str, dict[str, Any]] = {}
            for row in data:
                packages[row["id"]] = {
                    "amount": row["amount"],
                    "price": float(row["price"]),
                    "name": row["name"],
                    "bonus": row["bonus"],
                    "price_per_treat": (float(row["price_per_treat"]) if row["price_per_treat"] else None),
                    "price_id": row["price_id"],
                }

            # Update cache
            type(self)._packages_cache = packages
            type(self)._packages_cache_ts = now
            return packages
        except Exception as e:
            logger.error("Failed to fetch treat packages: %s", e)
            # Return stale cache if available
            stale_packages = type(self)._packages_cache
            if stale_packages is not None:
                return stale_packages
            return {}

    async def get_package_by_id(self, package_id: str) -> dict[str, Any] | None:
        """Fetch a specific treat package (uses cached packages first)."""
        # Try cache first
        packages = await self.get_packages()
        if package_id in packages:
            return packages[package_id]

        # Direct DB fallback (in case cache is stale)
        try:
            data = None
            if self.db:
                query = text("SELECT * FROM treat_packages WHERE id = :p_id AND is_active = TRUE LIMIT 1")
                result = await self.db.execute(query, {"p_id": package_id})
                row = result.fetchone()
                if row:
                    data = dict(row._mapping)
            else:
                res = (
                    await self.supabase.table("treat_packages")
                    .select("*")
                    .eq("id", package_id)
                    .eq("is_active", True)
                    .maybe_single()
                    .execute()
                )
                data = cast(dict[str, Any] | None, res.data if res is not None else None)

            if data:
                return {
                    "amount": data["amount"],
                    "price": float(data["price"]),
                    "name": data["name"],
                    "bonus": data["bonus"],
                    "price_per_treat": (float(data["price_per_treat"]) if data["price_per_treat"] else None),
                    "price_id": data["price_id"],
                }
            return None
        except Exception as e:
            logger.error("Failed to fetch treat package %s: %s", sanitize_log_value(package_id), e)
            return None

    # ── Fulfillment (webhook) ────────────────────────────────────────

    async def fulfill_treat_purchase(self, session: dict[str, Any]) -> None:
        """Handle fulfilling a treat purchase after payment session completion."""
        user_id = session.get("metadata", {}).get("user_id")
        package_id = session.get("metadata", {}).get("package")
        session_id = session.get("id")

        if not user_id or not package_id:
            logger.error("Fulfillment failed: missing metadata. user_id=%r, package=%r", user_id, package_id)
            raise ValueError("Treat purchase webhook is missing required metadata")

        package = await self.get_package_by_id(package_id)
        if not package or package.get("amount", 0) <= 0:
            logger.error("Fulfillment failed: package %r not found or invalid", package_id)
            raise ValueError("Treat package not found or invalid")

        amount = package["amount"]
        description = f"Purchased {package['name']} pack"

        try:
            if self.db:
                await self._fulfill_purchase_sql(user_id, amount, description, str(session_id))
            else:
                await self._fulfill_purchase_supabase(user_id, amount, description, str(session_id))
        except Exception as e:
            if self.db:
                await self.db.rollback()
            logger.error("Failed to add treats in fulfillment: %s", e, exc_info=True)
            raise

    async def _fulfill_purchase_sql(self, user_id: str, amount: int, description: str, session_id: str) -> None:
        """Fulfill treat purchase using SQLAlchemy."""
        if not self.db:
            logger.error("Database session is required for fulfillment")
            return
        db_session = self.db
        query = text(
            "SELECT rpc.error, rpc.duplicate, rpc.new_balance "
            "FROM json_to_record(public.purchase_treats_atomic("
            ":p_user_id, :p_amount, :p_description, :p_stripe_session_id"
            ")) AS rpc(error TEXT, duplicate BOOLEAN, new_balance INTEGER)"
        )
        result = await db_session.execute(
            query,
            {
                "p_user_id": user_id,
                "p_amount": amount,
                "p_description": description,
                "p_stripe_session_id": session_id,
            },
        )
        row = result.fetchone()
        if not row:
            raise RuntimeError("Failed to process purchase: no response from RPC")

        await db_session.commit()

        error, duplicate, new_balance = row
        if error:
            raise RuntimeError(f"Failed to process purchase: {error}")
        if duplicate:
            logger.info("Duplicate webhook processed for session %s", session_id)
        else:
            logger.info("Added %d treats to user %r. New balance: %s", amount, user_id, new_balance)

    async def _fulfill_purchase_supabase(self, user_id: str, amount: int, description: str, session_id: str) -> None:
        """Fulfill treat purchase using Supabase."""
        res = await self.supabase.rpc(
            "purchase_treats_atomic",
            {
                "p_user_id": user_id,
                "p_amount": amount,
                "p_description": description,
                "p_stripe_session_id": session_id,
            },
        ).execute()

        data = cast(dict[str, Any], res.data or {})
        if data.get("error"):
            raise RuntimeError(f"Failed to process purchase: {data.get('error')}")
        if data.get("duplicate"):
            logger.info("Duplicate webhook processed for session %s", session_id)
        else:
            logger.info("Added %d treats to user %r. New balance: %s", amount, user_id, data.get("new_balance"))
