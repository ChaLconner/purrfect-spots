import asyncio
import contextlib
from datetime import UTC, datetime, timedelta

from logger import logger
from services.notification_service import NotificationService
from services.storage_service import storage_service
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
            raise
        except Exception as e:
            logger.error(f"Error in notification cleanup job: {e}")

        # Sleep for 24 hours (86400 seconds)
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            logger.info("Notification cleanup job cancelled during sleep.")
            raise


async def _cleanup_orphaned_s3_files_job() -> None:
    """
    Background job to identify and delete files in S3 that don't have
    corresponding entries in the database (orphaned files).
    Only deletes files older than 24 hours to avoid race conditions with uploads.
    """
    while True:
        try:
            logger.info("Running S3 orphaned files cleanup job...")
            admin_client = await get_async_supabase_admin_client()

            # 1. Get all image URLs from database
            # For large datasets, this should be paginated or streamed
            result = await admin_client.table("cat_photos").select("image_url").execute()
            db_image_urls = {row["image_url"] for row in result.data} if result.data else set()

            # 2. List all files in S3
            s3_files = await storage_service.list_files(prefix="upload/")

            # 3. Compare and identify orphans
            now = datetime.now(UTC)
            orphans_to_delete = []

            for key, last_modified in s3_files:
                # Reconstruct the URL to match DB format (simple check)
                # Note: This logic depends on how storage_service.upload_file builds the URL
                # In this app, it's https://{bucket}.s3.{region}.amazonaws.com/{key}

                # Check age (only delete if > 24 hours old)
                if now - last_modified < timedelta(hours=24):
                    continue

                # Check if it exists in any DB URL
                # (A simple string check is used as URLs might have varying formats/CDNs)
                is_referenced = any(key in url for url in db_image_urls)

                if not is_referenced:
                    orphans_to_delete.append(key)

            # 4. Delete orphans
            if orphans_to_delete:
                logger.info("Found %d orphaned files in S3. Starting deletion...", len(orphans_to_delete))
                for key in orphans_to_delete:
                    # Construct dummy URL for delete_file method
                    dummy_url = f"https://dummy.s3.amazonaws.com/{key}"
                    await storage_service.delete_file(dummy_url)
                logger.info("Successfully deleted %d orphaned files from S3.", len(orphans_to_delete))
            else:
                logger.info("No orphaned S3 files found.")

        except asyncio.CancelledError:
            logger.info("S3 cleanup job cancelled.")
            raise
        except Exception as e:
            logger.error(f"Error in S3 cleanup job: {e}")

        # Sleep for 24 hours
        try:
            await asyncio.sleep(86400)
        except asyncio.CancelledError:
            raise


_notification_task: asyncio.Task | None = None
_account_deletion_task: asyncio.Task | None = None
_s3_cleanup_task: asyncio.Task | None = None


async def _cleanup_deleted_accounts_job() -> None:
    while True:
        try:
            logger.info("Running daily account deletion cleanup job...")
            admin_client = await get_async_supabase_admin_client()
            user_service = UserService(admin_client, admin_client)
            await user_service.execute_hard_delete()
        except asyncio.CancelledError:
            logger.info("Account deletion cleanup job cancelled.")
            raise
        except Exception as e:
            logger.error(f"Error in account deletion cleanup job: {e}")

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
