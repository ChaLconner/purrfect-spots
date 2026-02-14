"""
Tests for admin routes
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from dependencies import get_current_admin_user, get_supabase_admin_client


class TestAdminRoutes:
    @pytest.fixture
    def admin_user(self):
        return {"id": "admin-123", "email": "admin@example.com", "role": "admin"}

    @pytest.fixture
    def override_admin(self, admin_user):
        """Override get_current_admin_user dependency"""
        app.dependency_overrides[get_current_admin_user] = lambda: admin_user
        yield
        app.dependency_overrides.pop(get_current_admin_user, None)

    def test_list_users_success(self, client, override_admin, mock_supabase_admin):
        """Test listing users as admin"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[
            {"id": "u1", "email": "u1@test.com", "name": "User 1"},
            {"id": "u2", "email": "u2@test.com", "name": "User 2"}
        ])
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.get("/api/v1/admin/users")
            
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["id"] == "u1"

    def test_list_users_search(self, client, override_admin, mock_supabase_admin):
        """Test listing users with search query"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[{"id": "u1", "name": "Search Result"}])
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.get("/api/v1/admin/users?search=test")
            
        assert response.status_code == 200
        mock_supabase_admin.or_.assert_called()

    def test_list_users_failure(self, client, override_admin, mock_supabase_admin):
        """Test list users failure handling"""
        mock_supabase_admin.execute.side_effect = Exception("DB Error")
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.get("/api/v1/admin/users")
            
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch users"

    def test_get_stats_success(self, client, override_admin, mock_supabase_admin):
        """Test getting system stats"""
        # Mock responses for different table calls
        # 1st call: users count
        # 2nd call: cat_photos count
        mock_res_users = MagicMock(count=100)
        mock_res_photos = MagicMock(count=500)
        
        mock_supabase_admin.execute.side_effect = [mock_res_users, mock_res_photos]
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.get("/api/v1/admin/stats")
            
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 100
        assert data["total_photos"] == 500
        assert "generated_at" in data

    def test_get_stats_failure(self, client, override_admin, mock_supabase_admin):
        """Test stats failure handling"""
        mock_supabase_admin.execute.side_effect = Exception("Stats error")
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.get("/api/v1/admin/stats")
            
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch stats"

    def test_delete_user_success(self, client, override_admin, mock_supabase_admin):
        """Test deleting a user"""
        user_id = "target-u1"
        # Mock user check (exists and not admin)
        mock_supabase_admin.execute.return_value = MagicMock(data={"id": user_id, "role": "user"})
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.delete(f"/api/v1/admin/users/{user_id}")
            
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        mock_supabase_admin.auth.admin.delete_user.assert_called_with(user_id)

    def test_delete_user_not_found(self, client, override_admin, mock_supabase_admin):
        """Test deleting non-existent user"""
        mock_supabase_admin.execute.return_value = MagicMock(data=None)
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.delete("/api/v1/admin/users/ghost")
            
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_delete_admin_forbidden(self, client, override_admin, mock_supabase_admin):
        """Test preventing deletion of another admin"""
        mock_supabase_admin.execute.return_value = MagicMock(data={"role": "admin"})
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.delete("/api/v1/admin/users/other-admin")
            
        assert response.status_code == 400
        assert "Cannot delete an admin user" in response.json()["detail"]

    def test_delete_user_exception(self, client, override_admin, mock_supabase_admin):
        """Test delete user exception handling"""
        mock_supabase_admin.execute.side_effect = Exception("Delete error")
        
        with patch("routes.admin.get_supabase_admin_client", return_value=mock_supabase_admin):
            response = client.delete("/api/v1/admin/users/err")
            
        assert response.status_code == 500
        assert "Failed to delete user" in response.json()["detail"]

    def test_unauthorized_access(self, client):
        """Test that non-authenticated (or non-admin) users cannot access admin routes"""
        # Note: app.dependency_overrides is NOT set here, 
        # but the real dependency will fail without token.
        # If we want to test specifically "authenticated as non-admin", 
        # we'd override it with a non-admin user.
        
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401 # get_current_user_from_token raises 401 if no header
