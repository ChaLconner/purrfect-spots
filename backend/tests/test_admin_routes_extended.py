"""
Extended tests for admin routes including role management and audit logs
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dependencies import (
    get_admin_gallery_service,
    get_notification_service,
)
from main import app
from middleware.auth_middleware import get_current_user
from user_models.user import User


class TestAdminRoutesExtended:
    @pytest.fixture(autouse=True)
    def make_supabase_async(self, mock_supabase_admin):
        """Ensure execute is an AsyncMock for async calls"""
        mock_supabase_admin.execute = AsyncMock()
        return mock_supabase_admin

    @pytest.fixture
    def admin_user_with_permissions(self):
        """Return a user with all necessary admin permissions"""
        return User(
            id="admin-123",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["users:read", "users:update", "roles:read", "system:audit_logs"],
        )

    @pytest.fixture
    def override_current_user(self, admin_user_with_permissions):
        """Override get_current_user dependency"""
        # We override the dependency that require_permission uses
        app.dependency_overrides[get_current_user] = lambda: admin_user_with_permissions
        yield
        app.dependency_overrides.pop(get_current_user, None)

    def test_list_roles_success(self, client, override_current_user, mock_supabase_admin):
        """Test listing roles"""
        mock_supabase_admin.execute.return_value = MagicMock(
            data=[{"id": "r1", "name": "Admin"}, {"id": "r2", "name": "User"}]
        )

        with patch(
            "routes.admin.users.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.get("/api/v1/admin/roles")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Admin"

    def test_update_user_role_success(self, client, override_current_user, mock_supabase_admin):
        """Test updating user role"""
        user_id = "00000000-0000-4000-a000-000000000001"
        role_id = "00000000-0000-4000-a000-000000000002"

        # Mock role check
        mock_role_res = MagicMock(data={"name": "Moderator"})
        # Mock update result
        mock_update_res = MagicMock(data=[{"id": user_id, "role": "Moderator", "role_id": role_id}])

        # Configure side effects for sequential calls
        # 1. roles check
        # 2. update user
        # 3. insert audit log
        mock_supabase_admin.execute.side_effect = [
            mock_role_res,  # Role check
            mock_update_res,  # Update user
            MagicMock(),  # Audit log
        ]

        with patch(
            "routes.admin.users.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.put(f"/api/v1/admin/users/{user_id}/role", json={"role_id": role_id})

        assert response.status_code == 200
        assert response.json()["role"] == "Moderator"

        # Verify calls
        # We can inspect the mock calls to ensure correct table names were used
        # mocked_client.table("roles")...
        # mocked_client.table("users").update(...)
        # mocked_client.table("audit_logs").insert(...)

    def test_update_user_role_not_found(self, client, override_current_user, mock_supabase_admin):
        """Test updating role for non-existent user"""
        user_id = "00000000-0000-4000-a000-000000000999"
        role_id = "00000000-0000-4000-a000-000000000002"

        # Mock role exists
        mock_role_res = MagicMock(data={"name": "Moderator"})
        # Mock user update returns empty (user not found)
        mock_update_res = MagicMock(data=[])

        mock_supabase_admin.execute.side_effect = [mock_role_res, mock_update_res]

        with patch(
            "routes.admin.users.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.put(f"/api/v1/admin/users/{user_id}/role", json={"role_id": role_id})

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_update_user_role_invalid_role(self, client, override_current_user, mock_supabase_admin):
        """Test updating with invalid role id"""
        user_id = "00000000-0000-4000-a000-000000000001"
        role_id = "00000000-0000-4000-a000-000000000888"

        # Mock role not found
        mock_role_res = MagicMock(data=None)

        mock_supabase_admin.execute.return_value = mock_role_res

        with patch(
            "routes.admin.users.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.put(f"/api/v1/admin/users/{user_id}/role", json={"role_id": role_id})

        assert response.status_code == 404
        assert response.json()["detail"] == "Role not found"

    def test_list_audit_logs_success(self, client, override_current_user, mock_supabase_admin):
        """Test listing audit logs"""
        mock_supabase_admin.execute.return_value = MagicMock(
            data=[{"id": "log-1", "action": "UPDATE_ROLE", "users": {"email": "admin@example.com", "name": "Admin"}}]
        )

        with patch(
            "routes.admin.audit.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.get("/api/v1/admin/audit-logs")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["action"] == "UPDATE_ROLE"


class TestAdminContentRoutes:
    @pytest.fixture(autouse=True)
    def make_supabase_async(self, mock_supabase_admin):
        """Ensure execute is an AsyncMock for async calls"""
        mock_supabase_admin.execute = AsyncMock()
        return mock_supabase_admin

    @pytest.fixture
    def admin_user(self):
        return User(
            id="00000000-0000-0000-0000-000000000000",
            email="admin@example.com",
            name="Admin User",
            role="admin",
            permissions=["content:read", "content:delete"],
        )

    @pytest.fixture
    def override_admin(self, admin_user):
        """Override internal authentication dependencies"""
        app.dependency_overrides[get_current_user] = lambda: admin_user
        yield
        app.dependency_overrides.pop(get_current_user, None)

    def test_list_photos_success(self, client, override_admin, mock_supabase_admin):
        """Test listing photos as admin"""
        photo_id = "00000000-0000-0000-0000-000000000001"
        mock_data = [
            {"id": photo_id, "image_url": "http://img/1.jpg", "users": {"email": "u1@test.com", "name": "User 1"}}
        ]

        mock_supabase_admin.execute.return_value = MagicMock(data=mock_data)

        with patch(
            "routes.admin.content.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.get("/api/v1/admin/photos")

        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == photo_id

    def test_list_photos_search(self, client, override_admin, mock_supabase_admin):
        """Test searching photos"""
        mock_supabase_admin.execute.return_value = MagicMock(data=[])

        with patch(
            "routes.admin.content.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.get("/api/v1/admin/photos?search=cat")

        assert response.status_code == 200

    def test_delete_photo_success(self, client, override_admin, mock_supabase_admin):
        """Test deleting a photo"""
        photo_id = "00000000-0000-0000-0000-000000000001"
        user_id = "00000000-0000-0000-0000-000000000002"
        # 1. Get photo details
        mock_supabase_admin.execute.return_value = MagicMock(
            data={"id": photo_id, "image_url": "http://img.jpg", "user_id": user_id}
        )

        mock_gallery_service = MagicMock()
        mock_notification_service = MagicMock()

        app.dependency_overrides[get_admin_gallery_service] = lambda: mock_gallery_service
        app.dependency_overrides[get_notification_service] = lambda: mock_notification_service

        try:
            with patch(
                "routes.admin.content.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ):
                response = client.delete(f"/api/v1/admin/photos/{photo_id}")
        finally:
            app.dependency_overrides.pop(get_admin_gallery_service, None)
            app.dependency_overrides.pop(get_notification_service, None)

        assert response.status_code == 200
        assert "deletion scheduled" in response.json()["message"]

    def test_delete_photo_not_found(self, client, override_admin, mock_supabase_admin):
        """Test deleting non-existent photo"""
        # Return none for photo check
        mock_supabase_admin.execute.return_value = MagicMock(data=None)

        with patch(
            "routes.admin.content.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.delete("/api/v1/admin/photos/00000000-0000-0000-0000-000000000999")

        assert response.status_code == 404

    def test_list_reports_success(self, client, override_admin, mock_supabase_admin):
        """Test listing reports"""
        mock_data = [
            {
                "id": "00000000-0000-0000-0000-000000000003",
                "status": "pending",
                "reporter": {"email": "reporter@test.com"},
                "photo": {"image_url": "http://img.jpg"},
            }
        ]
        mock_supabase_admin.execute.return_value = MagicMock(data=mock_data)

        with patch(
            "routes.admin.reports.get_async_supabase_admin_client",
            new_callable=AsyncMock,
            return_value=mock_supabase_admin,
        ):
            response = client.get("/api/v1/admin/reports")

        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    def test_update_report_success(self, client, override_admin, mock_supabase_admin):
        """Test updating report status"""
        report_id = "00000000-0000-0000-0000-000000000003"
        user_id = "00000000-0000-0000-0000-000000000002"
        update_data = {"status": "resolved", "resolution_notes": "Done"}

        # Mock update result
        mock_supabase_admin.execute.return_value = MagicMock(
            data=[{"id": report_id, "status": "resolved", "reporter_id": user_id}]
        )

        mock_notification_service = MagicMock()
        app.dependency_overrides[get_notification_service] = lambda: mock_notification_service

        try:
            with patch(
                "routes.admin.reports.get_async_supabase_admin_client",
                new_callable=AsyncMock,
                return_value=mock_supabase_admin,
            ):
                response = client.put(f"/api/v1/admin/reports/{report_id}", json=update_data)
        finally:
            app.dependency_overrides.pop(get_notification_service, None)

        assert response.status_code == 200
        assert response.json()["status"] == "resolved"
