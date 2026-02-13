from unittest.mock import MagicMock, patch

import pytest


class TestGalleryServiceSecurity:
    """Security tests for GalleryService to ensure RLS compliance"""

    @pytest.fixture
    def gallery_service(self, mock_supabase, mock_supabase_admin):
        """Create GalleryService instance with mocked dependencies"""
        # We patch BOTH dependencies to ensure we catch where they are used
        with (
            patch("dependencies.get_supabase_client", return_value=mock_supabase),
            patch("dependencies.get_supabase_admin_client", return_value=mock_supabase_admin),
        ):
            from services.gallery_service import GalleryService

            return GalleryService(mock_supabase)

    def test_get_all_photos_uses_public_client(self, gallery_service, mock_supabase, mock_supabase_admin):
        """Verify get_all_photos uses standard client (enforcing RLS)"""

        # Setup return data
        mock_supabase.execute.return_value = MagicMock(data=[], count=0)

        # Act
        gallery_service.get_all_photos()

        # Assert
        # The public client SHOULD be called
        mock_supabase.table.assert_called_with("cat_photos")

        # The admin client SHOULD NOT be called for the query
        # (It might be called in __init__ for checks like fulltext support, but not for the main query)
        # To be precise, we check calls to table("cat_photos") specifically on admin

        # Check if Admin client was used for fetching photos
        # We assume strict compliance: Admin client should not touch cat_photos table for this read operation
        # Note: If _check_fulltext_support uses admin/public, that runs in __init__.
        # We reset mocks before action if needed, but let's check basic calls.

        for call in mock_supabase_admin.table.mock_calls:
            # We allow admin use for specific checks if necessary but not for main data fetch
            # But in our refactor we moved _check_fulltext_support to public client too (or kept it safe)
            # Actually I moved _check_fulltext_support to use public client too.
            # So Admin client should NOT be called at all for cat_photos in this lifecycle unless specifically needed.
            # However, imports might trigger things. Let's be specific.

            # If the call is table('cat_photos'), it's suspicious if it happened during get_all_photos
            args, _ = call
            if args and args[0] == "cat_photos":
                pytest.fail("GalleryService used Admin client to access cat_photos table!")

    def test_get_photo_by_id_uses_public_client(self, gallery_service, mock_supabase, mock_supabase_admin):
        """Verify get_photo_by_id uses standard client"""
        mock_supabase.execute.return_value = MagicMock(data={"id": "123"})

        gallery_service.get_photo_by_id("123")

        mock_supabase.table.assert_called_with("cat_photos")

        # Ensure admin client was not used for this query
        for call in mock_supabase_admin.table.mock_calls:
            args, _ = call
            if args and args[0] == "cat_photos":
                # We need to distinguish between init calls and method calls
                # Since we just instantiated service in fixture, init calls happened before this test function body
                # But Mock history persists? No, fixture creates new one.
                # Wait, __init__ runs inside fixture.
                # If __init__ uses admin client (it was refactored NOT to), then this fails.
                # My refactor moved _check_fulltext_support to use self.supabase.
                # So Admin client should be pristine regarding cat_photos table.
                pytest.fail("GalleryService used Admin client to access cat_photos table!")
