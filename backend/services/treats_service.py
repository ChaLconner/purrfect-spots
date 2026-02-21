import os
import time
from typing import Any, Dict, List

import stripe
from starlette.concurrency import run_in_threadpool
from supabase import AClient

from logger import logger
from schemas.notification import NotificationType
from services.notification_service import NotificationService
from utils.cache import cached_leaderboard

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ── In-memory package cache ──────────────────────────────────────────
_packages_cache: Dict[str, Dict[str, Any]] | None = None
_packages_cache_ts: float = 0.0
_PACKAGES_CACHE_TTL = 300  # 5 minutes


class TreatsService:
    def __init__(self, supabase_client: AClient) -> None:
        self.supabase = supabase_client
        self.notification_service = NotificationService(supabase_client)

    # ── Give treats ──────────────────────────────────────────────────

    async def give_treat(
        self, from_user_id: str, photo_id: str, amount: int, jwt_token: str | None = None
    ) -> Dict[str, Any]:
        """Give treats to a photo owner (fully atomic via DB RPC)."""
        try:
            from utils.supabase_client import get_async_supabase_admin_client

            # Use admin client to bypass RLS/JWT issues
            admin_client = await get_async_supabase_admin_client()

            res = await admin_client.rpc(
                "give_treat_atomic",
                {
                    "p_from_user_id": from_user_id,
                    "p_photo_id": photo_id,
                    "p_amount": amount,
                },
            ).execute()

            if not res.data or len(res.data) == 0:
                raise ValueError("Unknown error (no response from RPC)")

            result = res.data[0]
            if not result.get("success"):
                raise ValueError(result.get("error", "Unknown error"))

            # Fire-and-forget notification (don't fail the transaction)
            to_user_id = result.get("to_user_id")
            if to_user_id:
                await self._send_treat_notification(from_user_id, to_user_id, photo_id, amount)
            else:
                # Fallback: query photo owner (only if RPC didn't return it)
                await self._send_treat_notification_fallback(from_user_id, photo_id, amount)

            return {
                "success": True,
                "message": f"Gave {amount} treats",
                "new_balance": result.get("new_balance"),
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error("Give treat failed: %s", e, exc_info=True)
            raise

    async def _send_treat_notification(self, from_user_id: str, to_user_id: str, photo_id: str, amount: int) -> None:
        """Send notification when treats are given."""
        try:
            actor_res = await self.supabase.table("users").select("name").eq("id", from_user_id).single().execute()

            actor_name = actor_res.data.get("name") if actor_res.data else "Someone"

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
            photo_res = await self.supabase.table("cat_photos").select("user_id").eq("id", photo_id).single().execute()

            if photo_res.data:
                to_user_id = photo_res.data["user_id"]
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
    ) -> Dict[str, str]:
        """Create a Stripe Checkout Session for treat purchase."""
        try:
            # Build session params — link to customer if available
            session_params: Dict[str, Any] = {
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
            if stripe_customer_id:
                session_params["customer"] = stripe_customer_id
            else:
                # Try to find existing customer
                user_res = (
                    await self.supabase.table("users")
                    .select("stripe_customer_id")
                    .eq("id", user_id)
                    .maybe_single()
                    .execute()
                )

                db_customer_id = user_res.data.get("stripe_customer_id") if user_res and user_res.data else None
                if db_customer_id:
                    session_params["customer"] = db_customer_id

            checkout_session = await run_in_threadpool(lambda: stripe.checkout.Session.create(**session_params))
            return {
                "checkout_url": checkout_session.url or "",
                "session_id": checkout_session.id,
            }
        except Exception as e:
            logger.error("Stripe purchase session creation failed: %s", e, exc_info=True)
            raise

    # ── Balance & Transactions ───────────────────────────────────────

    async def get_balance(self, user_id: str) -> Dict[str, Any]:
        user_res = await self.supabase.table("users").select("treat_balance").eq("id", user_id).single().execute()

        balance = user_res.data["treat_balance"] if user_res.data else 0

        trans_res = (
            await self.supabase.table("treats_transactions")
            .select("*")
            .or_(f"from_user_id.eq.{user_id},to_user_id.eq.{user_id}")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        return {
            "balance": balance,
            "recent_transactions": trans_res.data or [],
        }

    # ── Leaderboard ──────────────────────────────────────────────────

    @cached_leaderboard
    async def get_leaderboard(self, period: str = "all_time") -> List[Dict[str, Any]]:
        """Top treat receivers (Most Spoiled Cats owners)."""
        try:
            res = await self.supabase.rpc("get_leaderboard", {"p_period": period}).execute()
            data: List[Dict[str, Any]] = res.data or []
            return data
        except Exception as e:
            logger.error(f"Failed to fetch leaderboard: {e}")
            # Fallback for all_time if RPC fails or during migration
            if period == "all_time":
                return await self._get_leaderboard_fallback()
            return []

    async def _get_leaderboard_fallback(self) -> List[Dict[str, Any]]:
        res = (
            await self.supabase.table("users")
            .select("id, name, username, picture, total_treats_received")
            .order("total_treats_received", desc=True)
            .limit(10)
            .execute()
        )
        return res.data or []

    # ── Packages (cached) ────────────────────────────────────────────

    async def get_packages(self) -> Dict[str, Dict[str, Any]]:
        """Fetch treat packages from database with in-memory caching."""
        global _packages_cache, _packages_cache_ts

        now = time.monotonic()
        if _packages_cache is not None and (now - _packages_cache_ts) < _PACKAGES_CACHE_TTL:
            return _packages_cache

        try:
            res = await self.supabase.table("treat_packages").select("*").eq("is_active", True).execute()
            packages: Dict[str, Dict[str, Any]] = {}
            for row in res.data or []:
                packages[row["id"]] = {
                    "amount": row["amount"],
                    "price": float(row["price"]),
                    "name": row["name"],
                    "bonus": row["bonus"],
                    "price_per_treat": (float(row["price_per_treat"]) if row["price_per_treat"] else None),
                    "price_id": row["price_id"],
                }

            # Update cache
            _packages_cache = packages
            _packages_cache_ts = now
            return packages
        except Exception as e:
            logger.error("Failed to fetch treat packages: %s", e)
            # Return stale cache if available
            if _packages_cache is not None:
                return _packages_cache
            return {}

    async def get_package_by_id(self, package_id: str) -> Dict[str, Any] | None:
        """Fetch a specific treat package (uses cached packages first)."""
        # Try cache first
        packages = await self.get_packages()
        if package_id in packages:
            return packages[package_id]

        # Direct DB fallback (in case cache is stale)
        try:
            res = (
                await self.supabase.table("treat_packages")
                .select("*")
                .eq("id", package_id)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )

            if res is not None and res.data:
                return {
                    "amount": res.data["amount"],
                    "price": float(res.data["price"]),
                    "name": res.data["name"],
                    "bonus": res.data["bonus"],
                    "price_per_treat": (float(res.data["price_per_treat"]) if res.data["price_per_treat"] else None),
                    "price_id": res.data["price_id"],
                }
            return None
        except Exception as e:
            logger.error("Failed to fetch treat package %s: %s", package_id, e)
            return None

    # ── Fulfillment (webhook) ────────────────────────────────────────

    async def fulfill_treat_purchase(self, session: Dict[str, Any]) -> None:
        """Handle fulfilling a treat purchase after payment session completion."""
        user_id = session.get("metadata", {}).get("user_id")
        package_id = session.get("metadata", {}).get("package")
        session_id = session.get("id")

        if not user_id or not package_id:
            logger.error(
                "Fulfillment failed: missing metadata. user_id=%s, package=%s",
                user_id,
                package_id,
            )
            return

        # Determine treat amount
        package = await self.get_package_by_id(package_id)
        if not package:
            logger.error("Fulfillment failed: package %s not found", package_id)
            return

        amount = package.get("amount", 0)

        if amount <= 0:
            logger.error("Fulfillment failed: invalid amount for package %s", package_id)
            return

        try:
            # Add treats ATOMICALLY (idempotent via stripe_session_id)
            res = await self.supabase.rpc(
                "purchase_treats_atomic",
                {
                    "p_user_id": user_id,
                    "p_amount": amount,
                    "p_description": f"Purchased {package['name']} pack",
                    "p_stripe_session_id": session_id,
                },
            ).execute()

            result = res.data or {}

            if result.get("error"):
                logger.error("Failed to process purchase: %s", result.get("error"))
            elif result.get("duplicate"):
                logger.info("Duplicate webhook processed for session %s", session_id)
            else:
                logger.info(
                    "Added %d treats to user %s. New balance: %s",
                    amount,
                    user_id,
                    result.get("new_balance"),
                )
        except Exception as e:
            logger.error("Failed to add treats in fulfillment: %s", e, exc_info=True)
