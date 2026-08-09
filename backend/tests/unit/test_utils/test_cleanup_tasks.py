import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.tasks.cleanup_tasks import (
    _cleanup_notifications_job,
    run_maintenance_tasks,
    start_cleanup_jobs,
    stop_cleanup_jobs,
)


class TestCleanupTasks:
    @pytest.mark.asyncio
    async def test_start_stop_cleanup_jobs(self):
        with patch("app.tasks.cleanup_tasks._cleanup_notifications_job", return_value=None):
            await start_cleanup_jobs()
            from app.tasks import cleanup_tasks

            assert cleanup_tasks._notification_task is not None

            await stop_cleanup_jobs()
            assert cleanup_tasks._notification_task is None

    @pytest.mark.asyncio
    async def test_cleanup_notifications_job_execution(self):
        mock_client = AsyncMock()
        mock_service = AsyncMock()

        with (
            patch("app.tasks.cleanup_tasks.get_async_supabase_admin_client", return_value=mock_client),
            patch("app.tasks.cleanup_tasks.NotificationService", return_value=mock_service),
            patch("asyncio.sleep", side_effect=asyncio.CancelledError),
            pytest.raises(asyncio.CancelledError),
        ):
            await _cleanup_notifications_job()

        mock_service.cleanup_old_notifications.assert_called_once_with(days=30)

    @pytest.mark.asyncio
    async def test_cleanup_notifications_job_error(self):
        with (
            patch("app.tasks.cleanup_tasks.get_async_supabase_admin_client", side_effect=Exception("DB Error")),
            patch("asyncio.sleep", side_effect=asyncio.CancelledError),
            pytest.raises(asyncio.CancelledError),
        ):
            await _cleanup_notifications_job()
            # Should log error and continue to sleep (which cancels it)

    @pytest.mark.asyncio
    async def test_manual_maintenance_surfaces_task_failures(self):
        with (
            patch("app.tasks.cleanup_tasks._cleanup_notifications", new_callable=AsyncMock, return_value="failed"),
            patch(
                "app.tasks.cleanup_tasks._cleanup_deleted_accounts", new_callable=AsyncMock, return_value="completed"
            ),
            patch("app.tasks.cleanup_tasks._cleanup_orphaned_s3_files", new_callable=AsyncMock, return_value="skipped"),
        ):
            result = await run_maintenance_tasks()

        assert result["status"] == "failed"
        assert result["notifications"] == "failed"
        assert result["deleted_accounts"] == "completed"
        assert result["s3_orphans"] == "skipped"
