from unittest.mock import MagicMock

import pytest

from exceptions import NotFoundError, ExternalServiceError
from services.social_service import SocialService


@pytest.fixture
def social_service():
    mock_supabase = MagicMock()
    return SocialService(mock_supabase)


@pytest.mark.asyncio
async def test_toggle_like_insert(social_service):
    """Test liking a photo (insert new like)"""
    # Mock RPC response for toggle_photo_like
    rpc_mock = MagicMock()
    rpc_mock.execute.return_value.data = [{"liked": True, "likes_count": 5}]
    social_service.supabase.rpc.return_value = rpc_mock
    
    # Mock photo owner fetch for notification (should not be our user)
    photo_mock = MagicMock()
    photo_mock.execute.return_value.data = {"user_id": "owner1", "location_name": "Cat Park"}
    social_service.supabase.table.return_value.select.return_value.eq.return_value.single.return_value = photo_mock
    
    res = await social_service.toggle_like("user1", "photo1")
    
    assert res["liked"] is True
    assert res["likes_count"] == 5
    social_service.supabase.rpc.assert_called_once_with(
        "toggle_photo_like",
        {"p_user_id": "user1", "p_photo_id": "photo1"}
    )


@pytest.mark.asyncio
async def test_toggle_like_delete(social_service):
    """Test unliking a photo (delete existing like)"""
    # Mock RPC response for toggle_photo_like
    rpc_mock = MagicMock()
    rpc_mock.execute.return_value.data = [{"liked": False, "likes_count": 4}]
    social_service.supabase.rpc.return_value = rpc_mock
    
    res = await social_service.toggle_like("user1", "photo1")
    
    assert res["liked"] is False
    assert res["likes_count"] == 4


@pytest.mark.asyncio
async def test_toggle_like_photo_not_found(social_service):
    """Test liking a non-existent photo raises NotFoundError"""
    # Mock RPC to raise exception with P0002 error code
    rpc_mock = MagicMock()
    rpc_mock.execute.side_effect = Exception("P0002: Photo not found")
    social_service.supabase.rpc.return_value = rpc_mock
    
    with pytest.raises(NotFoundError) as exc_info:
        await social_service.toggle_like("user1", "nonexistent")
    
    assert exc_info.value.resource_type == "photo"
    assert exc_info.value.resource_id == "nonexistent"


@pytest.mark.asyncio
async def test_toggle_like_service_error(social_service):
    """Test toggle like handles service errors gracefully"""
    # Mock RPC to raise generic exception
    rpc_mock = MagicMock()
    rpc_mock.execute.side_effect = Exception("Connection timeout")
    social_service.supabase.rpc.return_value = rpc_mock
    
    with pytest.raises(ExternalServiceError) as exc_info:
        await social_service.toggle_like("user1", "photo1")
    
    assert exc_info.value.service == "Supabase"
    assert exc_info.value.retryable is True


@pytest.mark.asyncio
async def test_toggle_like_no_self_notification(social_service):
    """Test that users don't get notified when liking their own photo"""
    # Mock RPC response
    rpc_mock = MagicMock()
    rpc_mock.execute.return_value.data = [{"liked": True, "likes_count": 5}]
    social_service.supabase.rpc.return_value = rpc_mock
    
    # Mock photo owner to be same as liker
    photo_mock = MagicMock()
    photo_mock.execute.return_value.data = {"user_id": "user1", "location_name": "My Spot"}
    
    # Set up table mock
    table_mock = MagicMock()
    table_mock.select.return_value.eq.return_value.single.return_value = photo_mock
    social_service.supabase.table.return_value = table_mock
    
    await social_service.toggle_like("user1", "photo1")
    
    # Notification insert should NOT be called for self-like
    # The insert on notifications table should not happen
    insert_calls = [
        call for call in social_service.supabase.table.call_args_list 
        if call[0][0] == "notifications"
    ]
    
    # No notification should be inserted when liking own photo
    for call in table_mock.insert.call_args_list:
        if call and len(call[0]) > 0:
            notification_data = call[0][0]
            # If there's a notification insert, it shouldn't be for the same user
            assert notification_data.get("user_id") != "user1"


@pytest.mark.asyncio
async def test_add_comment(social_service):
    """Test adding a comment to a photo"""
    # Mock photo exists check
    photo_check_mock = MagicMock()
    photo_check_mock.execute.return_value.data = {"id": "photo1", "user_id": "owner1"}
    
    # Mock insert response
    insert_mock = MagicMock()
    insert_mock.execute.return_value.data = [{"id": "c1", "content": "meow", "user_id": "user1"}]
    
    # Mock user fetch for enrichment
    user_mock = MagicMock()
    user_mock.execute.return_value.data = {"name": "CatLover", "picture": "avatar.jpg"}
    
    # Set up chain of mocks
    table_mock = MagicMock()
    
    def table_router(table_name):
        mock = MagicMock()
        if table_name == "cat_photos":
            mock.select.return_value.eq.return_value.is_.return_value.single.return_value = photo_check_mock
        elif table_name == "photo_comments":
            mock.insert.return_value = insert_mock
        elif table_name == "users":
            mock.select.return_value.eq.return_value.single.return_value = user_mock
        elif table_name == "notifications":
            mock.insert.return_value.execute.return_value = MagicMock()
        return mock
    
    social_service.supabase.table.side_effect = table_router
    
    res = await social_service.add_comment("user1", "photo1", "meow")
    
    assert res["id"] == "c1"
    assert res["content"] == "meow"


@pytest.mark.asyncio
async def test_add_comment_photo_not_found(social_service):
    """Test adding comment to non-existent photo raises NotFoundError"""
    # Mock photo check returns None
    photo_check_mock = MagicMock()
    photo_check_mock.execute.return_value.data = None
    
    table_mock = MagicMock()
    table_mock.select.return_value.eq.return_value.is_.return_value.single.return_value = photo_check_mock
    social_service.supabase.table.return_value = table_mock
    
    with pytest.raises(NotFoundError) as exc_info:
        await social_service.add_comment("user1", "nonexistent", "meow")
    
    assert exc_info.value.resource_type == "photo"


@pytest.mark.asyncio
async def test_get_comments(social_service):
    """Test getting comments for a photo"""
    # Mock comments response with user data
    comments_mock = MagicMock()
    comments_mock.execute.return_value.data = [
        {
            "id": "c1",
            "content": "cute cat!",
            "user_id": "user1",
            "users": {"name": "Alice", "picture": "alice.jpg"}
        },
        {
            "id": "c2",
            "content": "adorable!",
            "user_id": "user2",
            "users": {"name": "Bob", "picture": None}
        }
    ]
    
    table_mock = MagicMock()
    table_mock.select.return_value.eq.return_value.order.return_value.limit.return_value = comments_mock
    social_service.supabase.table.return_value = table_mock
    
    res = await social_service.get_comments("photo1")
    
    assert len(res) == 2
    assert res[0]["user_name"] == "Alice"
    assert res[0]["user_picture"] == "alice.jpg"
    assert res[1]["user_name"] == "Bob"
    assert "users" not in res[0]  # Should be flattened


@pytest.mark.asyncio
async def test_delete_comment_success(social_service):
    """Test successfully deleting a comment"""
    delete_mock = MagicMock()
    delete_mock.execute.return_value.data = [{"id": "c1"}]
    
    table_mock = MagicMock()
    table_mock.delete.return_value.eq.return_value.eq.return_value = delete_mock
    social_service.supabase.table.return_value = table_mock
    
    result = await social_service.delete_comment("user1", "c1")
    
    assert result is True


@pytest.mark.asyncio
async def test_delete_comment_not_found_or_unauthorized(social_service):
    """Test deleting non-existent or unauthorized comment returns False"""
    delete_mock = MagicMock()
    delete_mock.execute.return_value.data = []  # No rows deleted
    
    table_mock = MagicMock()
    table_mock.delete.return_value.eq.return_value.eq.return_value = delete_mock
    social_service.supabase.table.return_value = table_mock
    
    result = await social_service.delete_comment("user1", "nonexistent")
    
    assert result is False
