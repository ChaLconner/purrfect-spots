import asyncio
import contextlib
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from urllib.parse import urlparse

from app.logger import logger
from app.services.notification_service import NotificationService
from app.services.redis_service import RedisLockError, redis_service
from app.services.storage_service import storage_service
from app.services.user_service import UserService
from app.utils.supabase_client import get_async_supabase_admin_client


async def _cleanup_notifications() -> str:
    """Run notification cleanup once and return an observable outcome."""
    try:
        async with redis_service.lock("maintenance:notifications", ttl=3600, wait_timeout=0):
            logger.info("Running notification cleanup...")
            admin_client = await get_async_supabase_admin_client()
            notification_service = NotificationService(admin_client)
            await notification_service.cleanup_old_notifications(days=30)
            return "completed"
    except RedisLockError:
        logger.info("Notification cleanup skipped because another worker owns the lock")
        return "skipped"
    except Exception as e:
        logger.error(f"Error in notification cleanup: {e}")
        return "failed"


async def _cleanup_notifications_job() -> None:
    while True:
        await _cleanup_notifications()

        # Sleep for 24 hours (86400 seconds)
        await asyncio.sleep(86400)


def _collect_referenced_s3_keys(rows: list[dict[str, Any]]) -> set[str]:
    referenced_keys: set[str] = set()
    for row in rows:
        image_url = row.get("image_url") if isinstance(row, dict) else None
        if not isinstance(image_url, str) or not image_url:
            continue
        path = urlparse(image_url).path.lstrip("/")
        marker = path.find("upload/")
        if marker >= 0:
            referenced_keys.add(path[marker:])
    return referenced_keys


def _find_orphaned_s3_files(
    s3_files: list[tuple[str, datetime]], referenced_keys: set[str], now: datetime
) -> list[str]:
    return [
        key
        for key, last_modified in s3_files
        if now - last_modified >= timedelta(hours=24) and key not in referenced_keys
    ]


async def _cleanup_orphaned_s3_files() -> str:
    """Run S3 orphaned files cleanup once and return an observable outcome."""
    try:
        async with redis_service.lock("maintenance:s3-orphans", ttl=3600, wait_timeout=0):
            logger.info("Running S3 orphaned files cleanup...")
            admin_client = await get_async_supabase_admin_client()

            # 1. Get all image URLs from database
            result = await admin_client.table("cat_photos").select("image_url").execute()
            rows = cast(list[dict[str, Any]], result.data or [])
            referenced_keys = _collect_referenced_s3_keys(rows)

            # 2. List all files in S3
            s3_files = await storage_service.list_files(prefix="upload/")

            # 3. Compare and identify orphans
            now = datetime.now(UTC)
            orphans_to_delete = _find_orphaned_s3_files(s3_files, referenced_keys, now)

            # 4. Delete orphans
            if orphans_to_delete:
                logger.info("Found %d orphaned files in S3. Starting deletion...", len(orphans_to_delete))
                await storage_service.delete_files(orphans_to_delete)
                logger.info("Successfully deleted %d orphaned files from S3.", len(orphans_to_delete))
            else:
                logger.info("No orphaned S3 files found.")

            return "completed"

    except RedisLockError:
        logger.info("S3 cleanup skipped because another worker owns the lock")
        return "skipped"
    except Exception as e:
        logger.error(f"Error in S3 cleanup: {e}")
        return "failed"


async def _cleanup_orphaned_s3_files_job() -> None:
    """
    Background job to identify and delete files in S3 that don't have
    corresponding entries in the database (orphaned files).
    Only deletes files older than 24 hours to avoid race conditions with uploads.
    """
    while True:
        await _cleanup_orphaned_s3_files()

        # Sleep for 24 hours
        await asyncio.sleep(86400)


_notification_task: asyncio.Task | None = None
_account_deletion_task: asyncio.Task | None = None
_s3_cleanup_task: asyncio.Task | None = None


async def _cleanup_deleted_accounts() -> str:
    """Run account deletion cleanup once and return an observable outcome."""
    try:
        async with redis_service.lock("maintenance:deleted-accounts", ttl=3600, wait_timeout=0):
            logger.info("Running account deletion cleanup...")
            admin_client = await get_async_supabase_admin_client()
            user_service = UserService(admin_client, admin_client)
            result = await user_service.execute_hard_delete()
            return "failed" if result.get("failed", 0) else "completed"
    except RedisLockError:
        logger.info("Account deletion cleanup skipped because another worker owns the lock")
        return "skipped"
    except Exception as e:
        logger.error(f"Error in account deletion cleanup: {e}")
        return "failed"


async def _cleanup_deleted_accounts_job() -> None:
    while True:
        await _cleanup_deleted_accounts()

        # Sleep for 24 hours (86400 seconds)
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("Account deletion cleanup job cancelled during sleep.")
            raise


async def start_cleanup_jobs() -> None:
    global _notification_task
    global _account_deletion_task
    global _s3_cleanup_task
    logger.info("Starting background cleanup jobs")
    if _notification_task is None:
        _notification_task = asyncio.create_task(_cleanup_notifications_job())
    if _account_deletion_task is None:
        _account_deletion_task = asyncio.create_task(_cleanup_deleted_accounts_job())
    if _s3_cleanup_task is None:
        _s3_cleanup_task = asyncio.create_task(_cleanup_orphaned_s3_files_job())
    await asyncio.sleep(0)


async def stop_cleanup_jobs() -> None:
    global _notification_task
    global _account_deletion_task
    global _s3_cleanup_task
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

    if _s3_cleanup_task is not None:
        _s3_cleanup_task.cancel()
        tasks.append(_s3_cleanup_task)
        _s3_cleanup_task = None

    if tasks:
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(*tasks)


async def run_maintenance_tasks() -> dict[str, str]:
    """Run all maintenance tasks exactly once and expose each outcome."""
    logger.info("Starting manual maintenance task execution")
    results = {
        "notifications": await _cleanup_notifications(),
        "deleted_accounts": await _cleanup_deleted_accounts(),
        "s3_orphans": await _cleanup_orphaned_s3_files(),
    }
    failed = [name for name, status in results.items() if status == "failed"]
    status = "failed" if failed else "completed"
    message = "All maintenance tasks executed successfully"
    if failed:
        message = f"Maintenance tasks failed: {', '.join(failed)}"
    return {"status": status, **results, "message": message}
