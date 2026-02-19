from unittest.mock import MagicMock

import pytest

from services.notification_service import NotificationService

# Test UUIDs
_USER_1 = "00000000-0000-4000-a000-000000000001"
_USER_2 = "00000000-0000-4000-a000-000000000002"
_NOTIF_1 = "00000000-0000-4000-b000-000000000001"


@pytest.fixture
def notification_service():
    mock_supabase = MagicMock()
    return NotificationService(mock_supabase)


async def test_create_notification(notification_service):
    notification_service.supabase.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": _NOTIF_1, "user_id": _USER_1}
    ]

    res = await notification_service.create_notification(user_id=_USER_1, type="like", message="Test msg", actor_id=_USER_2)

    assert res["id"] == _NOTIF_1
    notification_service.supabase.table.return_value.insert.assert_called_once()


async def test_create_notification_self(notification_service):
    # Should not create notification for self
    res = await notification_service.create_notification(user_id=_USER_1, type="like", message="Test msg", actor_id=_USER_1)

    assert res == {}
    notification_service.supabase.table.return_value.insert.assert_not_called()


async def test_create_notification_invalid_uuid(notification_service):
    """Should skip notification for invalid UUID user_id"""
    res = await notification_service.create_notification(user_id="not-a-uuid", type="like", message="Test msg")
    assert res == {}
    notification_service.supabase.table.return_value.insert.assert_not_called()


async def test_mark_as_read(notification_service):
    await notification_service.mark_as_read(_USER_1, _NOTIF_1)
    notification_service.supabase.table.return_value.update.assert_called_with({"is_read": True})
