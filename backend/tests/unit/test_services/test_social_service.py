from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from exceptions import NotFoundError
from services.social_service import SocialService


@pytest.fixture
def social_service():
    # Pass a dummy sync client because __init__ still requires it
    return SocialService(MagicMock())


@pytest.mark.asyncio
async def test_toggle_like_insert(social_service):
    """Test liking a photo (insert new like)"""
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute = AsyncMock(return_value=MagicMock(data=[{"liked": True, "likes_count": 5}]))

    with patch("utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = mock_sb

        with (
            patch("utils.cache.invalidate_user_cache", new_callable=AsyncMock),
            patch("utils.cache.invalidate_gallery_cache", new_callable=AsyncMock),
        ):
            res = await social_service.toggle_like("user1", "photo1", jwt_token="token")

            assert res["liked"] is True
            assert res["likes_count"] == 5
            mock_sb.rpc.assert_called_with("toggle_photo_like", {"p_user_id": "user1", "p_photo_id": "photo1"})


@pytest.mark.asyncio
async def test_toggle_like_photo_not_found(social_service):
    """Test liking a non-existent photo raises NotFoundError"""
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute = AsyncMock(side_effect=Exception("P0002: Photo not found"))

    with patch("utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = mock_sb

        with pytest.raises(NotFoundError) as exc_info:
            await social_service.toggle_like("user1", "nonexistent")

        assert exc_info.value.resource_type == "photo"


@pytest.mark.asyncio
async def test_add_comment(social_service):
    """Test adding a comment to a photo"""
    mock_sb = MagicMock()
    # Mock chain: .table().select().eq().is_().limit().execute() OR .table().select().eq().limit().execute()
    # Let's make every method return the same builder and just set execute on it
    builder = MagicMock()
    mock_sb.table.return_value = builder
    builder.select.return_value = builder
    builder.eq.return_value = builder
    builder.is_.return_value = builder
    builder.limit.return_value = builder
    builder.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[{"id": "photo1", "user_id": "owner1"}]),  # Photo check
            MagicMock(data=[{"name": "CatLover", "picture": "avatar.jpg"}]),  # User info fetch
        ]
    )

    # Mock insert
    admin_mock = MagicMock()
    admin_mock.table.return_value.insert.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[{"id": "c1", "content": "meow", "user_id": "user1"}])
    )

    social_service.supabase = mock_sb
    social_service.notification_service.create_notification = AsyncMock()

    with patch("utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = admin_mock

        res = await social_service.add_comment("user1", "photo1", "meow", jwt_token="token")

        assert res["id"] == "c1"
        assert res["content"] == "meow"
        assert res["user_name"] == "CatLover"


@pytest.mark.asyncio
async def test_add_comment_photo_not_found(social_service):
    """Test adding comment to non-existent photo raises NotFoundError"""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.is_.return_value.limit.return_value.execute = (
        AsyncMock(return_value=MagicMock(data=[]))
    )
    social_service.supabase = mock_sb

    with pytest.raises(NotFoundError):
        await social_service.add_comment("user1", "nonexistent", "meow")


@pytest.mark.asyncio
async def test_get_comments(social_service):
    """Test getting comments for a photo"""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = (
        AsyncMock(
            return_value=MagicMock(
                data=[
                    {
                        "id": "c1",
                        "content": "cute",
                        "user_id": "user1",
                        "users": {"name": "Alice", "picture": "alice.jpg"},
                    }
                ]
            )
        )
    )
    social_service.supabase = mock_sb

    res = await social_service.get_comments("photo1")

    assert len(res) == 1
    assert res[0]["user_name"] == "Alice"


@pytest.mark.asyncio
async def test_delete_comment_success(social_service):
    """Test successfully deleting a comment"""
    mock_admin = MagicMock()
    mock_admin.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute = AsyncMock(
        return_value=MagicMock(data=[{"id": "c1"}])
    )

    with patch("utils.supabase_client.get_async_supabase_admin_client", new_callable=AsyncMock) as mock_get_admin:
        mock_get_admin.return_value = mock_admin

        result = await social_service.delete_comment("user1", "c1", jwt_token="token")

        assert result is True
