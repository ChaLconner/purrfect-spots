import asyncio
import contextlib

from logger import logger
from services.notification_service import NotificationService
from services.user_service import UserService
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


_notification_task: asyncio.Task | None = None
_account_deletion_task: asyncio.Task | None = None

async def _cleanup_deleted_accounts_job() -> None:
    while True:
        try:
            logger.info("Running daily account deletion cleanup job...")
            admin_client = await get_async_supabase_admin_client()
            user_service = UserService(admin_client, admin_client)
            await user_service.execute_hard_delete()
        except asyncio.CancelledError:
            logger.info("Account deletion cleanup job cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in account deletion cleanup job: {e}")

        # Sleep for 24 hours (86400 seconds)
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("Account deletion cleanup job cancelled during sleep.")
            break

async def start_cleanup_jobs() -> None:
    global _notification_task
    global _account_deletion_task
    logger.info("Starting background cleanup jobs")
    if _notification_task is None:
        _notification_task = asyncio.create_task(_cleanup_notifications_job())
    if _account_deletion_task is None:
        _account_deletion_task = asyncio.create_task(_cleanup_deleted_accounts_job())

async def stop_cleanup_jobs() -> None:
    global _notification_task
    global _account_deletion_task
    logger.info("Stopping background cleanup jobs")

    tasks = []
    if _notification_task is not None:
        _notification_task.cancel()
        tasks.append(_notification_task)
        _notification_task = None

    if _account_deletion_task is not None:
        _account_deletion_task.cancel()
        tasks.append(_account_deletion_task)
        _account_deletion_task = None

    if tasks:
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks)
