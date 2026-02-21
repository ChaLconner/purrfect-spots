from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.gallery_service import GalleryService


@pytest.mark.asyncio
@pytest.fixture(autouse=True)
async def clear_test_cache():
    """Clear the cache before each test to prevent cross-test contamination"""
    from utils.cache import memory_cache

    memory_cache.clear()
    yield
    memory_cache.clear()


class TestGalleryServiceExtended:
    @pytest.fixture
    def gallery_service(self, mock_supabase, mock_supabase_admin):
        # We need to ensure _check_fulltext_support doesn't crash or return expected value

        # It calls mock_supabase_admin.table()...

        with patch("dependencies.get_async_supabase_admin_client", return_value=mock_supabase_admin):
            with patch("services.search_service.SearchService._check_fulltext_support", return_value=True):
                service = GalleryService(mock_supabase)
                service._admin_client_lazy = mock_supabase_admin
                return service

    async def test_check_fulltext_support_true(self, mock_supabase):
        # Setup mock for successful execution
        mock_supabase.execute.return_value = MagicMock(data=[{"search_vector": ""}])

        with patch("dependencies.get_async_supabase_admin_client", return_value=MagicMock()) as mock_admin_getter:
            # Need to ensure the admin client returned also supports chainable execute
            admin_client = mock_admin_getter.return_value
            # Configure chain
            admin_client.table.return_value.select.return_value.limit.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{"search_vector": ""}])
            )

            service = GalleryService(mock_supabase)
            assert await service._fulltext_available is True

    async def test_check_fulltext_support_false(self, mock_supabase):
        # Setup mock for failure
        mock_supabase.execute.side_effect = Exception("Column missing")

        with patch("dependencies.get_async_supabase_admin_client", return_value=MagicMock()) as mock_admin_getter:
            admin_client = mock_admin_getter.return_value
            admin_client.table.return_value.select.return_value.limit.return_value.execute = AsyncMock(
                side_effect=Exception("Column missing")
            )

            service = GalleryService(mock_supabase)
            assert await service._fulltext_available is False

    async def test_fulltext_search_rpc_success(self, gallery_service, mock_supabase):
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[{"id": "1", "score": 0.9}])

        results = await gallery_service.search_photos(query="cat", use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "1"
        mock_supabase.rpc.assert_called()

    async def test_fulltext_search_rpc_fail_fallback_direct(self, gallery_service, mock_supabase):
        # RPC fails, should fallback to textSearch
        # Use separate mock for RPC to avoid polluting global execute
        rpc_mock = MagicMock()
        rpc_mock.execute = AsyncMock(side_effect=Exception("RPC missing"))
        mock_supabase.rpc.return_value = rpc_mock

        # Make textSearch succeed (on main mock)
        # Note: chain is long, but execute return value is what matters if it reaches there
        mock_supabase.execute.return_value = MagicMock(data=[{"id": "2"}])

        results = await gallery_service.search_photos(query="cat", use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "2"

    async def test_fulltext_search_filtering(self, gallery_service, mock_supabase):
        # Test client side filtering for RPC path
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[{"id": "1", "tags": ["orange", "cute"]}, {"id": "2", "tags": ["black"]}]
        )

        results = await gallery_service.search_photos(query="cat", tags=["orange"], use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "1"

    async def test_fulltext_all_fail_fallback_ilike(self, gallery_service, mock_supabase):
        # Patch SearchService._fulltext_search to simulate fulltext failure
        from services.search_service import SearchService

        with patch.object(SearchService, "_fulltext_search", side_effect=Exception("FT fail")):
            # ILIKE should succeed (on main mock)
            mock_supabase.execute.return_value = MagicMock(data=[{"id": "3"}])

            results = await gallery_service.search_photos(query="cat", use_fulltext=True)
            assert len(results) == 1
            assert results[0]["id"] == "3"

    async def test_get_nearby_photos_bbox(self, gallery_service, mock_supabase):
        # Feature flag disabled - must use AsyncMock for awaited check
        with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=False):
            # bbox search uses standard select
            mock_supabase.execute.return_value = MagicMock(data=[{"id": "loc1"}])

            # Use different coordinates to avoid cache hits if autouse fixture fails
            results = await gallery_service.get_nearby_photos(11.0, 21.0, radius_km=5)
            assert len(results) == 1
            assert results[0]["id"] == "loc1"

    async def test_get_nearby_photos_postgis(self, gallery_service, mock_supabase):
        with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=True):
            # Explicitly set return value for this specific test
            rpc_mock = MagicMock()
            rpc_mock.execute = AsyncMock(return_value=MagicMock(data=[{"id": "loc2"}]))
            mock_supabase.rpc.return_value = rpc_mock

            # Use unique coords
            results = await gallery_service.get_nearby_photos(12.0, 22.0, radius_km=5)
            assert len(results) == 1
            assert results[0]["id"] == "loc2"

    async def test_get_nearby_photos_postgis_fail(self, gallery_service, mock_supabase):
        with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=True):
            # Use isolated RPC mock
            rpc_mock = MagicMock()
            rpc_mock.execute = AsyncMock(side_effect=Exception("PostGIS error"))
            mock_supabase.rpc.return_value = rpc_mock

            # Fallback bbox Uses table execute - should succeed
            mock_supabase.execute.return_value = MagicMock(data=[{"id": "bbox_fallback"}])

            results = await gallery_service.get_nearby_photos(10.0, 20.0)
            assert len(results) == 1
            assert results[0]["id"] == "bbox_fallback"

    async def test_get_photo_by_id_found(self, gallery_service, mock_supabase):
        mock_supabase.execute.return_value = MagicMock(data=[{"id": "p1"}])

        photo = await gallery_service.get_photo_by_id("p1")
        assert photo["id"] == "p1"

    async def test_get_photo_by_id_not_found_rows(self, gallery_service, mock_supabase):
        mock_supabase.execute.return_value = MagicMock(data=[])

        photo = await gallery_service.get_photo_by_id("p1")
        assert photo is None

    async def test_get_photo_by_id_error(self, gallery_service, mock_supabase):
        mock_supabase.execute.side_effect = Exception("DB connection fail")

        with pytest.raises(Exception, match="Failed to fetch photo p1"):
            await gallery_service.get_photo_by_id("p1")
