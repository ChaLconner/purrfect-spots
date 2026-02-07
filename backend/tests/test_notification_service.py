from unittest.mock import MagicMock

import pytest

from services.notification_service import NotificationService


@pytest.fixture
def notification_service():
    mock_supabase = MagicMock()
    return NotificationService(mock_supabase)

async def test_create_notification(notification_service):
    notification_service.supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "n1", "user_id": "u1"}]
    
    res = await notification_service.create_notification(
        user_id="u1", 
        type="like", 
        message="Test msg", 
        actor_id="u2"
    )
    
    assert res["id"] == "n1"
    notification_service.supabase.table.return_value.insert.assert_called_once()
    
async def test_create_notification_self(notification_service):
    # Should not create notification for self
    res = await notification_service.create_notification(
        user_id="u1", 
        type="like", 
        message="Test msg", 
        actor_id="u1"
    )
    
    assert res == {}
    notification_service.supabase.table.return_value.insert.assert_not_called()

async def test_mark_as_read(notification_service):
    await notification_service.mark_as_read("u1", "n1")
    notification_service.supabase.table.return_value.update.assert_called_with({"is_read": True})
