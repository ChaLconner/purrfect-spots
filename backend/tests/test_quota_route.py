from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.fixture
async def client():
    """Create test client using AsyncClient"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestQuotaRoute:
    """Test quota endpoint functionality"""

    async def test_quota_requires_authentication(self, client):
        """Test that quota endpoint requires authentication"""
        response = await client.get("/api/v1/upload/quota")

        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]

    async def test_get_quota_success(self, client, mock_user):
        """Test successful quota retrieval"""
        from dependencies import get_quota_service
        from middleware.auth_middleware import get_current_user

        # Mock QuotaService
        mock_quota_service = MagicMock()
        mock_quota_service.get_user_quota_status = AsyncMock(
            return_value={"used": 2, "limit": 5, "remaining": 3, "is_pro": False}
        )

        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_quota_service] = lambda: mock_quota_service

        response = await client.get("/api/v1/upload/quota")

        # Clean up overrides
        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["used"] == 2
        assert data["limit"] == 5
        assert data["remaining"] == 3
        assert data["is_pro"] is False

        mock_quota_service.get_user_quota_status.assert_called_once_with(str(mock_user.id), mock_user.is_pro)

    async def test_get_quota_error_handling(self, client, mock_user):
        """Test quota retrieval error handling"""
        from dependencies import get_quota_service
        from middleware.auth_middleware import get_current_user

        # Mock QuotaService to raise exception
        mock_quota_service = MagicMock()
        # Use an exception that might happen in production
        mock_quota_service.get_user_quota_status = AsyncMock(side_effect=Exception("Database error"))

        # Override dependencies
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_quota_service] = lambda: mock_quota_service

        # FastAPI might raise the exception directly in tests depending on configuration
        # but usually it returns a 500 response
        try:
            response = await client.get("/api/v1/upload/quota")
            assert response.status_code == 500
        except Exception as e:
            assert str(e) == "Database error"
        finally:
            # Clean up overrides
            app.dependency_overrides = {}
