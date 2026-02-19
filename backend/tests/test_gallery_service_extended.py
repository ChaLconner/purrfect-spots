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

        with patch("dependencies.get_supabase_admin_client", return_value=mock_supabase_admin):
            with patch("services.search_service.SearchService._check_fulltext_support", return_value=True):
                service = GalleryService(mock_supabase)
                service._admin_client_lazy = mock_supabase_admin
                return service

    def test_check_fulltext_support_true(self, mock_supabase):
        # Setup mock for successful execution
        mock_supabase.execute.return_value = MagicMock(data=[{"search_vector": ""}])

        with patch("dependencies.get_supabase_admin_client", return_value=MagicMock()):
            service = GalleryService(mock_supabase)
            assert service._fulltext_available is True

    def test_check_fulltext_support_false(self, mock_supabase):
        # Setup mock for failure
        mock_supabase.execute.side_effect = Exception("Column missing")

        with patch("dependencies.get_supabase_admin_client", return_value=MagicMock()):
            service = GalleryService(mock_supabase)
            assert service._fulltext_available is False

    async def test_fulltext_search_rpc_success(self, gallery_service, mock_supabase):
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[{"id": "1", "score": 0.9}])

        results = await gallery_service.search_photos(query="cat", use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "1"
        mock_supabase.rpc.assert_called()

    async def test_fulltext_search_rpc_fail_fallback_direct(self, gallery_service, mock_supabase):
        # RPC fails, should fallback to textSearch
        mock_supabase.rpc.side_effect = Exception("RPC missing")
        mock_supabase.text_search.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": "2"}]
        )

        results = await gallery_service.search_photos(query="cat", use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "2"
        mock_supabase.text_search.assert_called()

    async def test_fulltext_search_filtering(self, gallery_service, mock_supabase):
        # Test client side filtering for RPC path
        mock_supabase.rpc.return_value.execute.return_value = MagicMock(
            data=[{"id": "1", "tags": ["orange", "cute"]}, {"id": "2", "tags": ["black"]}]
        )

        results = await gallery_service.search_photos(query="cat", tags=["orange"], use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "1"

    async def test_fulltext_all_fail_fallback_ilike(self, gallery_service, mock_supabase):
        # RPC fails, Direct fails -> Fallback to ILIKE

        # We need to simulate failure ONLY inside _fulltext_search
        # gallery_service.search_photos calls _fulltext_search

        with patch.object(gallery_service, "search_service"):
            # We need to mock the search_service instance attached to gallery_service
            # But the fixture already patches SearchService class.
            # The instance `gallery_service.search_service` is a Mock (from fixture)
            # So looking at `gallery_service.search_photos` -> calls `await to_thread(search_service.search_photos)`

            # Actually, `search_service` is ALREADY a mock from the fixture logic?
            # In fixture we did `with patch("services.search_service.SearchService._check_fulltext_support", ...)`
            # We did NOT patch the entire class in the FINAL version of fixture.
            # So `gallery_service.search_service` is a REAL `SearchService` instance (with patched `_check_fulltext_support`).

            # So `patch.object(gallery_service.search_service, "_fulltext_search", side_effect=Exception("FT fail"))` is better.
            pass

        # Since we use real SearchService (mostly), we can patch its method.
        # But wait, `search_photos` runs in `to_thread`. Patching might be tricky across threads if not carefully done?
        # Usually `patch` works fine.

        with patch.object(gallery_service.search_service, "_fulltext_search", side_effect=Exception("FT fail")):
            mock_supabase.or_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
                data=[{"id": "3"}]
            )

            # Should catch exception and call _ilike_search
            results = await gallery_service.search_photos(query="cat", use_fulltext=True)
            assert len(results) == 1
            assert results[0]["id"] == "3"

    async def test_get_nearby_photos_bbox(self, gallery_service, mock_async_supabase):
        # Feature flag disabled by default or we can mock it
        with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=False):
            mock_async_supabase.select = AsyncMock(return_value=[{"id": "loc1"}])

            results = await gallery_service.get_nearby_photos(10.0, 20.0, radius_km=5)
            assert len(results) == 1
            assert results[0]["id"] == "loc1"

    async def test_get_nearby_photos_postgis(self, gallery_service, mock_async_supabase):
        with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=True):
            # Explicitly set return value for this specific test
            mock_async_supabase.rpc = AsyncMock(return_value=[{"id": "loc2"}])

            results = await gallery_service.get_nearby_photos(10.0, 20.0, radius_km=5)
            assert len(results) == 1
            assert results[0]["id"] == "loc2"
            mock_async_supabase.rpc.assert_called_with(
                "search_nearby_photos", {"lat": 10.0, "lng": 20.0, "radius_meters": 5000.0, "result_limit": 50}
            )

    async def test_get_nearby_photos_postgis_fail(self, gallery_service, mock_async_supabase):
        with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=True):
            mock_async_supabase.rpc = AsyncMock(side_effect=Exception("PostGIS error"))
            mock_async_supabase.select = AsyncMock(return_value=[{"id": "bbox_fallback"}])

            results = await gallery_service.get_nearby_photos(10.0, 20.0)
            assert len(results) == 1
            assert results[0]["id"] == "bbox_fallback"

    async def test_get_photo_by_id_found(self, gallery_service, mock_async_supabase):
        mock_async_supabase.select = AsyncMock(return_value=[{"id": "p1"}])

        photo = await gallery_service.get_photo_by_id("p1")
        assert photo["id"] == "p1"

    async def test_get_photo_by_id_not_found_rows(self, gallery_service, mock_async_supabase):
        mock_async_supabase.select = AsyncMock(return_value=[])

        photo = await gallery_service.get_photo_by_id("p1")
        assert photo is None

    async def test_get_photo_by_id_error(self, gallery_service, mock_async_supabase):
        mock_async_supabase.select = AsyncMock(side_effect=Exception("DB connection fail"))

        with pytest.raises(Exception, match="Failed to fetch photo p1"):
            await gallery_service.get_photo_by_id("p1")
