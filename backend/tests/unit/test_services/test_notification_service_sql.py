from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.notification_service import NotificationService

_USER_1 = "00000000-0000-4000-a000-000000000001"


@pytest.fixture
def notification_service_sql():
    mock_supabase = MagicMock()
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    return NotificationService(mock_supabase, db=mock_db), mock_db


@pytest.mark.asyncio
async def test_get_notifications_sql_uses_datetime_cutoff(notification_service_sql):
    service, mock_db = notification_service_sql

    row = MagicMock()
    row._mapping = {"id": "notif-1", "message": "hello"}
    query_result = MagicMock()
    query_result.fetchall.return_value = [row]
    mock_db.execute.return_value = query_result

    result = await service.get_notifications(_USER_1, limit=15, offset=0)

    assert result == [{"id": "notif-1", "message": "hello"}]
    _, params = mock_db.execute.await_args.args
    assert params["u_id"] == _USER_1
    assert isinstance(params["since"], datetime)
    assert params["lim"] == 15
    assert params["off"] == 0


@pytest.mark.asyncio
async def test_cleanup_old_notifications_sql_uses_datetime_cutoff(notification_service_sql):
    service, mock_db = notification_service_sql

    delete_result = MagicMock()
    delete_result.rowcount = 2
    mock_db.execute.return_value = delete_result

    await service.cleanup_old_notifications(days=30)

    _, params = mock_db.execute.await_args.args
    assert isinstance(params["cutoff"], datetime)
    mock_db.commit.assert_awaited_once()
