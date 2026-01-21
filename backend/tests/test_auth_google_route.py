"""
Tests for Google Authentication routes
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import app

# We don't import get_auth_service for override, we patch the service class
# from routes.auth_google import get_auth_service
from middleware.auth_middleware import get_current_user_from_header


class TestGoogleAuthRoutes:
    """Test suite for Google Auth Routes"""

    @pytest.fixture
    def mock_user_response(self):
        from datetime import datetime
        from types import SimpleNamespace

        return SimpleNamespace(
            id="user123",
            email="test@example.com",
            name="Test User",
            picture="pic.jpg",
            bio="Bio",
            created_at=datetime(2024, 1, 1),
        )

    @pytest.fixture
    def mock_login_response_obj(self, mock_user_response):
        resp = MagicMock()
        resp.access_token = "access"
        resp.refresh_token = "refresh"
        resp.token_type = "bearer"
        # The service returns a Pydantic model or object with 'user' attribute
        resp.user = mock_user_response
        return resp

    def test_google_login_redirect(self, client):
        """Test redirect to Google login"""
        with patch("routes.auth_google.config") as mock_config:
            mock_config.get_allowed_origins.return_value = ["http://localhost:5173"]

            with patch("os.getenv", return_value="google_id"):
                response = client.get("/api/v1/auth/google/login", follow_redirects=False)
                assert response.status_code == 302
                assert "accounts.google.com" in response.headers["location"]

    def test_google_login(self, client, mock_user_response):
        """Test Google login with token"""
        with patch("routes.auth_google.AuthService") as MockServiceClass:
            # Configure instance
            mock_service = MockServiceClass.return_value
            mock_service.verify_google_token.return_value = {"email": "test@example.com"}
            mock_service.create_or_get_user.return_value = mock_user_response
            mock_service.create_access_token.return_value = "mock_access_token"
            mock_service.create_refresh_token.return_value = "mock_refresh_token"

            # Need to patch config for cookie setting
            with patch("routes.auth_google.config") as mock_config:
                mock_config.JWT_REFRESH_EXPIRATION_DAYS = 7
                mock_config.is_production.return_value = False

                payload = {"token": "google_token"}
                response = client.post("/api/v1/auth/google", json=payload)

                assert response.status_code == 200, f"Response: {response.text}"
                assert response.json()["access_token"] == "mock_access_token"

    def test_google_exchange_code(self, client, mock_login_response_obj):
        """Test exchange code for tokens"""
        with patch("routes.auth_google.AuthService") as MockServiceClass:
            mock_service = MockServiceClass.return_value
            mock_service.exchange_google_code = AsyncMock(return_value=mock_login_response_obj)

            with patch("routes.auth_google.config") as mock_config:
                mock_config.get_allowed_origins.return_value = ["http://localhost:5173"]
                mock_config.JWT_REFRESH_EXPIRATION_DAYS = 7
                mock_config.is_production.return_value = False

                payload = {
                    "code": "auth_code",
                    "code_verifier": "verifier",
                    "redirect_uri": "http://localhost:5173/auth/callback",
                }
                response = client.post("/api/v1/auth/google/exchange", json=payload)

                assert response.status_code == 200, f"Response: {response.text}"
                assert response.json()["access_token"] == "access"

    def test_sync_user_data(self, client):
        """Test user sync endpoint"""
        mock_jwt_payload = {
            "sub": "user123",
            "email": "test@example.com",
            "user_metadata": {"full_name": "Test User", "avatar_url": "p.jpg"},
            "app_metadata": {"provider": "google"},
        }

        mock_supabase_admin = MagicMock()
        mock_res = MagicMock()
        mock_res.data = [{"id": "user123"}]
        mock_supabase_admin.table().upsert().execute.return_value = mock_res

        with patch("dependencies.get_supabase_admin_client", return_value=mock_supabase_admin):
            app.dependency_overrides[get_current_user_from_header] = lambda: mock_jwt_payload

            response = client.post("/api/v1/auth/sync-user")

            assert response.status_code == 200
            assert response.json()["message"] == "User synced"

        app.dependency_overrides = {}

    def test_logout(self, client):
        """Test logout endpoint"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
