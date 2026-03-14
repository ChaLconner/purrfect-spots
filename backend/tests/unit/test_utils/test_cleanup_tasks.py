import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from tasks.cleanup_tasks import _cleanup_notifications_job, start_cleanup_jobs, stop_cleanup_jobs


class TestCleanupTasks:
    @pytest.mark.asyncio
    async def test_start_stop_cleanup_jobs(self):
        with patch("tasks.cleanup_tasks._cleanup_notifications_job", return_value=None):
            await start_cleanup_jobs()
            from tasks import cleanup_tasks

            assert cleanup_tasks._task is not None

            await stop_cleanup_jobs()
            assert cleanup_tasks._task is None

    @pytest.mark.asyncio
    async def test_cleanup_notifications_job_execution(self):
        mock_client = AsyncMock()
        mock_service = AsyncMock()

        with (
            patch("tasks.cleanup_tasks.get_async_supabase_admin_client", return_value=mock_client),
            patch("tasks.cleanup_tasks.NotificationService", return_value=mock_service),
            patch("asyncio.sleep", side_effect=asyncio.CancelledError),
        ):
            await _cleanup_notifications_job()

        mock_service.cleanup_old_notifications.assert_called_once_with(days=30)

    @pytest.mark.asyncio
    async def test_cleanup_notifications_job_error(self):
        with (
            patch("tasks.cleanup_tasks.get_async_supabase_admin_client", side_effect=Exception("DB Error")),
            patch("asyncio.sleep", side_effect=asyncio.CancelledError),
        ):
            await _cleanup_notifications_job()
            # Should log error and continue to sleep (which cancels it)
