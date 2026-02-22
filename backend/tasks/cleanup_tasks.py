import asyncio
import contextlib

from logger import logger
from services.notification_service import NotificationService
from utils.supabase_client import get_async_supabase_admin_client


async def _cleanup_notifications_job() -> None:
    while True:
        try:
            logger.info("Running daily notification cleanup job...")
            admin_client = await get_async_supabase_admin_client()
            notification_service = NotificationService(admin_client)
            await notification_service.cleanup_old_notifications(days=30)
        except asyncio.CancelledError:
            logger.info("Notification cleanup job cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in notification cleanup job: {e}")

        # Sleep for 24 hours (86400 seconds)
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("Notification cleanup job cancelled during sleep.")
            break


_task: asyncio.Task | None = None


async def start_cleanup_jobs() -> None:
    global _task
    if _task is None:
        logger.info("Starting background cleanup jobs")
        _task = asyncio.create_task(_cleanup_notifications_job())


async def stop_cleanup_jobs() -> None:
    global _task
    if _task is not None:
        logger.info("Stopping background cleanup jobs")
        _task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _task
        _task = None
