
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.social_service import SocialService
from exceptions import ExternalServiceError, NotFoundError

@pytest.fixture
def social_service():
    # Pass a dummy sync client because __init__ still requires it
    return SocialService(MagicMock())

@pytest.mark.asyncio
async def test_toggle_like_insert(social_service):
    """Test liking a photo (insert new like)"""
    with patch("utils.async_client.async_supabase") as mock_async:
        mock_async.rpc = AsyncMock(return_value=[{"liked": True, "likes_count": 5}])
        
        with patch("utils.cache.invalidate_user_cache", new_callable=AsyncMock), \
             patch("utils.cache.invalidate_gallery_cache", new_callable=AsyncMock):
            
            res = await social_service.toggle_like("user1", "photo1", jwt_token="token")
            
            assert res["liked"] is True
            assert res["likes_count"] == 5
            mock_async.rpc.assert_called_with(
                "toggle_photo_like",
                {"p_user_id": "user1", "p_photo_id": "photo1"},
                jwt_token="token"
            )

@pytest.mark.asyncio
async def test_toggle_like_photo_not_found(social_service):
    """Test liking a non-existent photo raises NotFoundError"""
    with patch("utils.async_client.async_supabase") as mock_async:
        # Mock generic exception that contains P0002
        mock_async.rpc = AsyncMock(side_effect=Exception("P0002: Photo not found"))
        
        with pytest.raises(NotFoundError) as exc_info:
            await social_service.toggle_like("user1", "nonexistent")
        
        assert exc_info.value.resource_type == "photo"

@pytest.mark.asyncio
async def test_add_comment(social_service):
    """Test adding a comment to a photo"""
    with patch("utils.async_client.async_supabase") as mock_async:
        # Mock photo check (select)
        # First call is select cat_photos
        mock_async.select = AsyncMock(side_effect=[
            [{"id": "photo1", "user_id": "owner1"}],  # Photo check
            [{"name": "CatLover", "picture": "avatar.jpg"}] # User info fetch
        ])
        
        # Mock insert
        mock_async.insert = AsyncMock(return_value=[{"id": "c1", "content": "meow", "user_id": "user1"}])
        
        # Mock notification service (initialized in __init__)
        social_service.notification_service.create_notification = AsyncMock()
        
        res = await social_service.add_comment("user1", "photo1", "meow", jwt_token="token")
        
        assert res["id"] == "c1"
        assert res["content"] == "meow"
        assert res["user_name"] == "CatLover"
        
        mock_async.insert.assert_called_once()
        # verify args if needed

@pytest.mark.asyncio
async def test_add_comment_photo_not_found(social_service):
    """Test adding comment to non-existent photo raises NotFoundError"""
    with patch("utils.async_client.async_supabase") as mock_async:
        # Photo check returns empty list
        mock_async.select = AsyncMock(return_value=[])
        
        with pytest.raises(NotFoundError):
            await social_service.add_comment("user1", "nonexistent", "meow")

@pytest.mark.asyncio
async def test_get_comments(social_service):
    """Test getting comments for a photo"""
    with patch("utils.async_client.async_supabase") as mock_async:
        mock_async.select = AsyncMock(return_value=[
            {
                "id": "c1",
                "content": "cute",
                "user_id": "user1",
                "users": {"name": "Alice", "picture": "alice.jpg"}
            }
        ])
        
        res = await social_service.get_comments("photo1")
        
        assert len(res) == 1
        assert res[0]["user_name"] == "Alice"

@pytest.mark.asyncio
async def test_delete_comment_success(social_service):
    """Test successfully deleting a comment"""
    with patch("utils.async_client.async_supabase") as mock_async:
        mock_async.delete = AsyncMock(return_value=[{"id": "c1"}])
        
        result = await social_service.delete_comment("user1", "c1", jwt_token="token")
        
        assert result is True
        mock_async.delete.assert_called_with(
            table="photo_comments",
            filters={"id": "eq.c1", "user_id": "eq.user1"},
            jwt_token="token"
        )
