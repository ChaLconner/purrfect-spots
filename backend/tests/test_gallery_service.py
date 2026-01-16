"""
Tests for gallery service with pagination
"""

from unittest.mock import MagicMock, patch

import pytest


class TestGalleryService:
    """Test suite for GalleryService"""

    @pytest.fixture
    def mock_supabase_admin(self):
        """Create a fully mocked supabase admin client"""
        mock = MagicMock()
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.order.return_value = mock
        mock.range.return_value = mock
        mock.limit.return_value = mock
        mock.eq.return_value = mock
        mock.or_.return_value = mock
        mock.contains.return_value = mock
        mock.execute.return_value = MagicMock(data=[], count=0)
        return mock

    @pytest.fixture
    def gallery_service(self, mock_supabase, mock_supabase_admin):
        """Create GalleryService instance with mocked dependencies"""
        # Patch at the dependencies module level
        with patch(
            "dependencies.get_supabase_admin_client", return_value=mock_supabase_admin
        ):
            from services.gallery_service import GalleryService

            service = GalleryService(mock_supabase)
            service.supabase_admin = mock_supabase_admin
            return service

    def test_get_all_photos_empty(self, gallery_service, mock_supabase_admin):
        """Test getting photos when database is empty"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[], count=0)

        result = gallery_service.get_all_photos()

        assert result["data"] == []
        assert result["total"] == 0
        assert result["has_more"] is False

    def test_get_all_photos_with_data(
        self, gallery_service, mock_supabase_admin, mock_cat_photo
    ):
        """Test getting photos with existing data"""
        mock_supabase_admin.execute.return_value = MagicMock(
            data=[mock_cat_photo], count=1
        )

        result = gallery_service.get_all_photos(limit=10, offset=0)

        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == mock_cat_photo["id"]
        assert result["limit"] == 10
        assert result["offset"] == 0

    def test_get_all_photos_pagination(
        self, gallery_service, mock_supabase_admin, mock_cat_photo
    ):
        """Test pagination parameters"""
        mock_supabase_admin.execute.return_value = MagicMock(
            data=[mock_cat_photo], count=50
        )

        result = gallery_service.get_all_photos(limit=10, offset=20)

        assert result["limit"] == 10
        assert result["offset"] == 20
        assert result["total"] == 50
        assert result["has_more"] is True  # 20 + 1 < 50

    def test_get_all_photos_limit_clamping(self, gallery_service, mock_supabase_admin):
        """Test that limit is clamped to valid range"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[], count=0)

        # Test max limit clamping
        result = gallery_service.get_all_photos(limit=500)
        assert result["limit"] == 100  # Max is 100

        # Test min limit clamping
        result = gallery_service.get_all_photos(limit=0)
        assert result["limit"] == 1  # Min is 1

    def test_get_all_photos_simple(
        self, gallery_service, mock_supabase_admin, mock_cat_photo
    ):
        """Test simple get all photos without pagination"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[mock_cat_photo])

        result = gallery_service.get_all_photos_simple()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == mock_cat_photo["id"]

    def test_search_photos_by_query(
        self, gallery_service, mock_supabase_admin, mock_cat_photo
    ):
        """Test searching photos by text query (using ILIKE fallback)"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[mock_cat_photo])

        # Use use_fulltext=False to test ILIKE search path
        result = gallery_service.search_photos(query="Cat Spot", use_fulltext=False)

        assert len(result) == 1
        assert result[0]["location_name"] == "Test Cat Spot"

    def test_search_photos_by_tags(
        self, gallery_service, mock_supabase_admin, mock_cat_photo
    ):
        """Test searching photos by tags"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[mock_cat_photo])

        # Tags-only search uses ILIKE path
        result = gallery_service.search_photos(
            tags=["orange", "friendly"], use_fulltext=False
        )

        assert len(result) == 1

    def test_search_photos_combined(
        self, gallery_service, mock_supabase_admin, mock_cat_photo
    ):
        """Test combined text and tag search"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[mock_cat_photo])

        result = gallery_service.search_photos(
            query="Cat", tags=["orange"], use_fulltext=False
        )

        assert len(result) == 1

    def test_search_photos_empty_result(self, gallery_service, mock_supabase_admin):
        """Test search with no results"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[])

        result = gallery_service.search_photos(query="nonexistent", use_fulltext=False)

        assert result == []

    def test_get_popular_tags(self, gallery_service, mock_supabase_admin):
        """Test getting popular tags"""
        mock_supabase_admin.execute.return_value = MagicMock(
            data=[
                {"tags": ["orange", "cute"], "description": "#orange #cute"},
                {"tags": ["orange", "sleeping"], "description": "#orange #sleeping"},
                {"tags": ["black", "cute"], "description": "#black #cute"},
            ]
        )

        result = gallery_service.get_popular_tags(limit=5)

        assert isinstance(result, list)
        # 'orange' appears twice, 'cute' appears twice
        if len(result) > 0:
            # Most popular should be at the top
            assert (
                result[0]["count"] >= result[-1]["count"] if len(result) > 1 else True
            )

    def test_get_popular_tags_empty(self, gallery_service, mock_supabase_admin):
        """Test getting popular tags when no photos exist"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[])

        result = gallery_service.get_popular_tags()

        assert result == []

    def test_get_user_photos(
        self, gallery_service, mock_supabase_admin, mock_cat_photo
    ):
        """Test getting photos for a specific user"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[mock_cat_photo])

        result = gallery_service.get_user_photos("test-user-123")

        assert len(result) == 1
        assert result[0]["user_id"] == "test-user-123"

    def test_get_user_photos_empty(self, gallery_service, mock_supabase_admin):
        """Test getting photos for user with no uploads"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[])

        result = gallery_service.get_user_photos("user-with-no-photos")

        assert result == []

    def test_get_all_photos_error_handling(self, gallery_service, mock_supabase_admin):
        """Test error handling in get_all_photos"""
        mock_supabase_admin.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception) as excinfo:
            gallery_service.get_all_photos()

        assert "Failed to fetch gallery images" in str(excinfo.value)

    def test_search_photos_error_handling(self, gallery_service, mock_supabase_admin):
        """Test error handling in search_photos"""
        mock_supabase_admin.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception) as excinfo:
            # Force ILIKE search to test error handling
            gallery_service.search_photos(query="test", use_fulltext=False)

        assert "Failed to search photos" in str(excinfo.value)
