import os
import uuid

import pytest
from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Check for Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

@pytest.mark.skipif(
    not SUPABASE_URL or not SUPABASE_SERVICE_KEY,
    reason="Supabase credentials not found in environment"
)
class TestSocialLikesIntegration:
    """Integration tests for social features (likes) using real database"""

    @pytest.fixture(scope="class")
    def supabase(self):
        """Create a Supabase client with service role for admin access"""
        return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    @pytest.fixture(scope="class")
    def test_user(self, supabase: Client):
        """Get or create a test user"""
        # Try to find an existing user first to avoid cluttering auth.users
        # Note: listing users requires admin privileges which service_key has
        users = supabase.auth.admin.list_users()
        if users and len(users) > 0:
            return users[0]
        
        # If no user, create one
        email = f"test_{uuid.uuid4()}@example.com"
        password = "testpassword123"
        user = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        return user

    @pytest.fixture(scope="class")
    def test_photo(self, supabase: Client, test_user):
        """Create a test photo record"""
        photo_id = str(uuid.uuid4())
        user_id = test_user.id
        
        print(f"Creating test photo {photo_id} for user {user_id}")
        
        # Insert directly into cat_photos
        # Note: We need to ensure minimal required fields are present
        data = {
            "id": photo_id,
            "user_id": user_id,
            "image_url": "https://example.com/test-cat.jpg",
            "location_name": "Test Location",
            "latitude": 0.0,
            "longitude": 0.0,
            "description": "Integration test photo",
            "likes_count": 0 # Explicitly start at 0
        }
        
        res = supabase.table("cat_photos").insert(data).execute()
        created_photo = res.data[0]
        
        yield created_photo
        
        # Cleanup
        print(f"Cleaning up test photo {photo_id}")
        supabase.table("cat_photos").delete().eq("id", photo_id).execute()

    def test_toggle_like_flow(self, supabase: Client, test_user, test_photo):
        """
        Test the full like/unlike flow:
        1. Verify initial state (0 likes)
        2. Toggle Like (Expect: liked=True, count=1)
        3. Verify persistence
        4. Toggle Like again (Expect: liked=False, count=0)
        5. Verify persistence
        """
        user_id = test_user.id
        photo_id = test_photo["id"]

        print(f"Testing toggle like for user {user_id} on photo {photo_id}")

        # 1. Verify initial state
        # fetch directly from DB to be sure
        res = supabase.table("cat_photos").select("likes_count").eq("id", photo_id).single().execute()
        assert res.data["likes_count"] == 0, "Initial likes count should be 0"

        # 2. Toggle Like (Like)
        # Call the RPC function directly
        ret = supabase.rpc("toggle_photo_like", {"p_user_id": user_id, "p_photo_id": photo_id}).execute()
        
        # Check RPC return
        assert len(ret.data) > 0, "RPC should return data"
        result = ret.data[0]
        assert result["liked"] is True, "Should be liked"
        assert result["likes_count"] == 1, "Count should be 1"

        # 3. Verify persistence in photo_likes table
        like_entry = supabase.table("photo_likes").select("*").eq("user_id", user_id).eq("photo_id", photo_id).execute()
        assert len(like_entry.data) == 1, "Like entry should exist in photo_likes"

        # Verify persistence in cat_photos table (trigger check)
        photo_entry = supabase.table("cat_photos").select("likes_count").eq("id", photo_id).single().execute()
        assert photo_entry.data["likes_count"] == 1, "Trigger should update likes_count in cat_photos"

        # 4. Toggle Like again (Unlike)
        ret = supabase.rpc("toggle_photo_like", {"p_user_id": user_id, "p_photo_id": photo_id}).execute()
        
        # Check RPC return
        assert len(ret.data) > 0
        result = ret.data[0]
        assert result["liked"] is False, "Should be unliked"
        assert result["likes_count"] == 0, "Count should be 0"

        # 5. Verify persistence
        like_entry = supabase.table("photo_likes").select("*").eq("user_id", user_id).eq("photo_id", photo_id).execute()
        assert len(like_entry.data) == 0, "Like entry should be removed"

        photo_entry = supabase.table("cat_photos").select("likes_count").eq("id", photo_id).single().execute()
        assert photo_entry.data["likes_count"] == 0, "Trigger should decrement likes_count"

    def test_toggle_like_nonexistent_photo(self, supabase: Client, test_user):
        """Test toggling like on a non-existent photo"""
        user_id = test_user.id
        fake_photo_id = str(uuid.uuid4())

        # Expect an error
        with pytest.raises(Exception) as excinfo:
            supabase.rpc("toggle_photo_like", {"p_user_id": user_id, "p_photo_id": fake_photo_id}).execute()
        
        # Supabase-py raises postgrest.exceptions.APIError, but generic Exception catch works
        assert "Photo not found" in str(excinfo.value) or "P0002" in str(excinfo.value), \
            f"Should raise Photo not found error, got: {str(excinfo.value)}"
