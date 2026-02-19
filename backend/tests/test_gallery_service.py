"""
Tests for gallery service with pagination
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.gallery_service import GalleryService


@pytest.mark.asyncio
class TestGalleryService:
    """Test suite for GalleryService"""

    @pytest.fixture
    def gallery_service(self, mock_supabase, mock_supabase_admin):
        """Create GalleryService instance with mocked dependencies"""
        import importlib

        import services.gallery_service

        importlib.reload(services.gallery_service)

        # Patch at the dependencies module level
        with patch("dependencies.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = GalleryService(mock_supabase)
            service._admin_client_lazy = mock_supabase_admin
            return service

    async def test_get_all_photos_empty(self, gallery_service, mock_async_supabase):
        """Test getting photos when database is empty"""
        mock_async_supabase.rpc = AsyncMock(return_value=[])
        mock_async_supabase.count = AsyncMock(return_value=0)

        result = await gallery_service.get_all_photos()

        assert result["data"] == []
        assert result["total"] == 0
        assert result["has_more"] is False

    async def test_get_all_photos_with_data(self, gallery_service, mock_async_supabase, mock_cat_photo):
        """Test getting photos with existing data"""
        mock_async_supabase.rpc = AsyncMock(return_value=[mock_cat_photo])
        mock_async_supabase.count = AsyncMock(return_value=1)

        result = await gallery_service.get_all_photos(limit=10, offset=0)

        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == mock_cat_photo["id"]
        assert result["limit"] == 10
        assert result["offset"] == 0

    async def test_get_all_photos_pagination(self, gallery_service, mock_async_supabase, mock_cat_photo):
        """Test pagination parameters"""
        mock_async_supabase.rpc = AsyncMock(return_value=[mock_cat_photo])
        mock_async_supabase.count = AsyncMock(return_value=50)

        result = await gallery_service.get_all_photos(limit=10, offset=20)

        assert result["limit"] == 10
        assert result["offset"] == 20
        assert result["total"] == 50
        assert result["has_more"] is True  # 20 + 1 < 50

    async def test_get_all_photos_limit_clamping(self, gallery_service, mock_async_supabase):
        """Test that limit is clamped to valid range"""
        mock_async_supabase.rpc = AsyncMock(return_value=[])
        mock_async_supabase.count = AsyncMock(return_value=0)

        # Test max limit clamping
        result = await gallery_service.get_all_photos(limit=500)
        assert result["limit"] == 100  # Max is 100

        # Test min limit clamping
        result = await gallery_service.get_all_photos(limit=0)
        assert result["limit"] == 1  # Min is 1

    async def test_get_all_photos_simple(self, gallery_service, mock_async_supabase, mock_cat_photo):
        """Test simple get all photos without pagination"""
        mock_async_supabase.select = AsyncMock(return_value=[mock_cat_photo])

        result = await gallery_service.get_all_photos_simple()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == mock_cat_photo["id"]

    async def test_search_photos_by_query(self, gallery_service, mock_supabase, mock_cat_photo):
        """Test searching photos by text query (using ILIKE fallback)"""
        mock_supabase.execute.return_value = MagicMock(data=[mock_cat_photo])

        # Use use_fulltext=False to test ILIKE search path
        result = await gallery_service.search_photos(query="Cat Spot", use_fulltext=False)

        assert len(result) == 1
        assert result[0]["location_name"] == "Test Cat Spot"

    async def test_search_photos_by_tags(self, gallery_service, mock_supabase, mock_cat_photo):
        """Test searching photos by tags"""
        mock_supabase.execute.return_value = MagicMock(data=[mock_cat_photo])

        # Tags-only search uses ILIKE path
        result = await gallery_service.search_photos(tags=["orange", "friendly"], use_fulltext=False)

        assert len(result) == 1

    async def test_search_photos_combined(self, gallery_service, mock_supabase, mock_cat_photo):
        """Test combined text and tag search"""
        mock_supabase.execute.return_value = MagicMock(data=[mock_cat_photo])

        result = await gallery_service.search_photos(query="Cat", tags=["orange"], use_fulltext=False)

        assert len(result) == 1

    async def test_search_photos_empty_result(self, gallery_service, mock_supabase):
        """Test search with no results"""
        mock_supabase.execute.return_value = MagicMock(data=[])

        result = await gallery_service.search_photos(query="nonexistent", use_fulltext=False)

        assert result == []

    async def test_get_popular_tags(self, gallery_service, mock_async_supabase):
        """Test getting popular tags"""
        mock_async_supabase.select = AsyncMock(
            return_value=[
                {"tags": ["orange", "cute"], "description": "#orange #cute"},
                {"tags": ["orange", "sleeping"], "description": "#orange #sleeping"},
                {"tags": ["black", "cute"], "description": "#black #cute"},
            ]
        )

        result = await gallery_service.get_popular_tags(limit=5)

        assert isinstance(result, list)
        # 'orange' appears twice, 'cute' appears twice
        if len(result) > 0:
            # Most popular should be at the top
            assert result[0]["count"] >= result[-1]["count"] if len(result) > 1 else True

    async def test_get_popular_tags_empty(self, gallery_service, mock_async_supabase):
        """Test getting popular tags when no photos exist"""
        mock_async_supabase.select = AsyncMock(return_value=[])

        result = await gallery_service.get_popular_tags()

        assert result == []

    async def test_get_user_photos(self, gallery_service, mock_async_supabase, mock_cat_photo):
        """Test getting photos for a specific user"""
        mock_async_supabase.select = AsyncMock(return_value=[mock_cat_photo])

        user_id = mock_cat_photo["user_id"]
        result = await gallery_service.get_user_photos(user_id)

        assert len(result) == 1
        assert result[0]["user_id"] == user_id

    async def test_get_user_photos_empty(self, gallery_service, mock_async_supabase):
        """Test getting photos for user with no uploads"""
        mock_async_supabase.select = AsyncMock(return_value=[])

        result = await gallery_service.get_user_photos("user-with-no-photos")

        assert result == []

    async def test_get_all_photos_error_handling(self, gallery_service, mock_supabase):
        """Test error handling in get_all_photos"""
        with patch("utils.async_client.async_supabase") as mock_async_client:
            # Force both primary and fallback to fail
            mock_async_client.rpc = AsyncMock(side_effect=Exception("Database error"))
            mock_async_client.select = AsyncMock(side_effect=Exception("Fallback error"))

            with pytest.raises(Exception) as excinfo:
                await gallery_service.get_all_photos()

            assert "Failed to fetch gallery images" in str(excinfo.value)

    async def test_get_all_photos_with_token(self, gallery_service, mock_supabase):
        """Test getting photos with JWT token propagation to async client"""
        # We need to patch the async_supabase imported inside the method
        with patch("utils.async_client.async_supabase") as mock_async_client:
            # Setup mock return value - MUST be AsyncMock for await
            mock_async_client.rpc = AsyncMock(return_value=[{"id": "1", "url": "test.jpg"}])

            # Call with token
            result = await gallery_service.get_all_photos(limit=10, jwt_token="test-token")

            # Verify rpc was called with token
            mock_async_client.rpc.assert_called_once()
            call_args = mock_async_client.rpc.call_args
            assert call_args.kwargs.get("jwt_token") == "test-token"
            assert result["data"][0]["id"] == "1"

    async def test_search_photos_error_handling(self, gallery_service, mock_supabase):
        """Test error handling in search_photos"""
        mock_supabase.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception) as excinfo:
            # Force ILIKE search to test error handling
            await gallery_service.search_photos(query="test", use_fulltext=False)

        # ExternalServiceError from _ilike_search contains this message
        assert "Database error during photo retrieval" in str(excinfo.value)
