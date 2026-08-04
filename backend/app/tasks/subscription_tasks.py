"""Periodic Stripe-to-database subscription reconciliation."""

import asyncio

from app.config import config
from app.logger import logger
from app.services.redis_service import RedisLockError, redis_service
from app.services.subscription_service import SubscriptionService
from app.utils.supabase_client import get_async_supabase_admin_client


async def reconcile_subscriptions_once() -> None:
    """Run one best-effort reconciliation pass."""
    lock_ttl = max(300, config.SUBSCRIPTION_RECONCILIATION_INTERVAL_SECONDS)
    try:
        async with redis_service.lock("maintenance:subscription-reconciliation", ttl=lock_ttl, wait_timeout=0):
            admin_client = await get_async_supabase_admin_client()
            summary = await SubscriptionService(admin_client).reconcile_all_subscriptions()
            logger.info("Subscription reconciliation complete: %s", summary)
    except RedisLockError:
        logger.info("Subscription reconciliation skipped because another worker owns the lock")


async def _subscription_reconciliation_job() -> None:
    while True:
        try:
            await reconcile_subscriptions_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            # Keep scheduler alive; next pass retries transient Stripe/DB errors.
            logger.error("Subscription reconciliation job failed", exc_info=True)
        await asyncio.sleep(config.SUBSCRIPTION_RECONCILIATION_INTERVAL_SECONDS)


_subscription_reconciliation_task: asyncio.Task | None = None


async def start_subscription_reconciliation_job() -> None:
    """Start one reconciliation task per application process."""
    global _subscription_reconciliation_task
    if not config.ENABLE_SUBSCRIPTION_RECONCILIATION:
        logger.info("Subscription reconciliation disabled")
        return
    if _subscription_reconciliation_task is None:
        _subscription_reconciliation_task = asyncio.create_task(_subscription_reconciliation_job())
        logger.info(
            "Started subscription reconciliation every %s seconds",
            config.SUBSCRIPTION_RECONCILIATION_INTERVAL_SECONDS,
        )


async def stop_subscription_reconciliation_job() -> None:
    """Cancel the reconciliation task during application shutdown."""
    global _subscription_reconciliation_task
    task = _subscription_reconciliation_task
    _subscription_reconciliation_task = None
    if task is not None:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.debug("Subscription reconciliation task cancelled during shutdown")
