import pytest
from unittest.mock import MagicMock, patch
from services.gallery_service import GalleryService

class TestGalleryServiceExtended:
    
    @pytest.fixture
    def mock_supabase_admin(self):
        mock = MagicMock()
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.order.return_value = mock
        mock.range.return_value = mock
        mock.limit.return_value = mock
        mock.eq.return_value = mock
        mock.or_.return_value = mock
        mock.contains.return_value = mock
        mock.rpc.return_value = mock
        mock.textSearch.return_value = mock
        mock.not_.return_value = mock
        mock.is_.return_value = mock
        mock.gte.return_value = mock
        mock.lte.return_value = mock
        mock.single.return_value = mock
        mock.execute.return_value = MagicMock(data=[], count=0)
        return mock

    @pytest.fixture
    def mock_supabase(self):
        return MagicMock()

    @pytest.fixture
    def gallery_service(self, mock_supabase, mock_supabase_admin):
        # We need to ensure _check_fulltext_support doesn't crash or return expected value
        # It calls mock_supabase_admin.table()...
        
        with patch("dependencies.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = GalleryService(mock_supabase)
            service.supabase_admin = mock_supabase_admin
            # Force enable fulltext for tests unless specified
            service._fulltext_available = True
            return service

    def test_check_fulltext_support_true(self, mock_supabase, mock_supabase_admin):
        # Setup mock for successful execution
        mock_supabase_admin.execute.return_value = MagicMock(data=[{"search_vector": ""}])
        
        with patch("dependencies.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = GalleryService(mock_supabase)
            assert service._fulltext_available is True

    def test_check_fulltext_support_false(self, mock_supabase, mock_supabase_admin):
        # Setup mock for failure
        mock_supabase_admin.execute.side_effect = Exception("Column missing")
        
        with patch("dependencies.get_supabase_admin_client", return_value=mock_supabase_admin):
            service = GalleryService(mock_supabase)
            assert service._fulltext_available is False

    def test_fulltext_search_rpc_success(self, gallery_service, mock_supabase_admin):
        mock_supabase_admin.rpc.return_value.execute.return_value = MagicMock(data=[{"id": "1", "score": 0.9}])
        
        results = gallery_service.search_photos(query="cat", use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "1"
        mock_supabase_admin.rpc.assert_called()

    def test_fulltext_search_rpc_fail_fallback_direct(self, gallery_service, mock_supabase_admin):
        # RPC fails, should fallback to textSearch
        mock_supabase_admin.rpc.side_effect = Exception("RPC missing")
        mock_supabase_admin.textSearch.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "2"}])
        
        results = gallery_service.search_photos(query="cat", use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "2"
        mock_supabase_admin.textSearch.assert_called()

    def test_fulltext_search_filtering(self, gallery_service, mock_supabase_admin):
        # Test client side filtering for RPC path
        mock_supabase_admin.rpc.return_value.execute.return_value = MagicMock(data=[
            {"id": "1", "tags": ["orange", "cute"]},
            {"id": "2", "tags": ["black"]}
        ])
        
        results = gallery_service.search_photos(query="cat", tags=["orange"], use_fulltext=True)
        assert len(results) == 1
        assert results[0]["id"] == "1"

    def test_fulltext_all_fail_fallback_ilike(self, gallery_service, mock_supabase_admin):
        # RPC fails, Direct fails -> Fallback to ILIKE
        
        # We need to simulate failure ONLY inside _fulltext_search
        # gallery_service.search_photos calls _fulltext_search
        
        with patch.object(gallery_service, "_fulltext_search", side_effect=Exception("FT fail")):
            mock_supabase_admin.or_.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "3"}])
            
            # Should catch exception and call _ilike_search
            results = gallery_service.search_photos(query="cat", use_fulltext=True)
            assert len(results) == 1
            assert results[0]["id"] == "3"

    def test_get_nearby_photos_bbox(self, gallery_service, mock_supabase_admin):
         # Feature flag disabled by default or we can mock it
         with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=False):
             mock_supabase_admin.execute.return_value = MagicMock(data=[{"id": "loc1"}])
             
             results = gallery_service.get_nearby_photos(10.0, 20.0, radius_km=5)
             assert len(results) == 1
             mock_supabase_admin.gte.assert_called() # lat/lng filters

    def test_get_nearby_photos_postgis(self, gallery_service, mock_supabase_admin):
        with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=True):
            mock_supabase_admin.rpc.return_value.execute.return_value = MagicMock(data=[{"id": "loc2"}])
            
            results = gallery_service.get_nearby_photos(10.0, 20.0, radius_km=5)
            assert len(results) == 1
            assert results[0]["id"] == "loc2"
            mock_supabase_admin.rpc.assert_called_with(
                "search_nearby_photos",
                {"lat": 10.0, "lng": 20.0, "radius_meters": 5000.0, "result_limit": 50}
            )

    def test_get_nearby_photos_postgis_fail(self, gallery_service, mock_supabase_admin):
        with patch("services.feature_flags.FeatureFlagService.is_enabled", return_value=True):
            mock_supabase_admin.rpc.side_effect = Exception("PostGIS error")
            mock_supabase_admin.execute.return_value = MagicMock(data=[{"id": "bbox_fallback"}])
            
            results = gallery_service.get_nearby_photos(10.0, 20.0)
            assert len(results) == 1
            assert results[0]["id"] == "bbox_fallback"

    def test_get_photo_by_id_found(self, gallery_service, mock_supabase_admin):
        mock_supabase_admin.single.return_value.execute.return_value = MagicMock(data={"id": "p1"})
        
        photo = gallery_service.get_photo_by_id("p1")
        assert photo["id"] == "p1"

    def test_get_photo_by_id_not_found_rows(self, gallery_service, mock_supabase_admin):
        # Supabase raises exception when single() returns no rows
        mock_supabase_admin.single.return_value.execute.side_effect = Exception("JSON object requested, multiple (or no) rows returned")
        
        photo = gallery_service.get_photo_by_id("p1")
        assert photo is None

    def test_get_photo_by_id_error(self, gallery_service, mock_supabase_admin):
        mock_supabase_admin.single.return_value.execute.side_effect = Exception("DB connection fail")
        
        with pytest.raises(Exception):
            gallery_service.get_photo_by_id("p1")
