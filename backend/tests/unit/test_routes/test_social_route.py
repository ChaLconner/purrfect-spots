from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from dependencies import get_current_token, get_social_service
from main import app
from middleware.auth_middleware import get_current_user_from_credentials


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client using AsyncClient."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:  # NOSONAR python:S5332 - test base URL
        yield ac


class TestSocialRoute:
    @pytest.fixture
    def mock_social_service(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_comments_accepts_uuid_ids(self, client, mock_social_service):
        """Comment lists should serialize UUID-backed IDs as strings."""
        comment = {
            "id": uuid4(),
            "user_id": uuid4(),
            "photo_id": uuid4(),
            "content": "meow",
            "created_at": "2026-04-15T17:24:00Z",
            "user_name": "Cat Lover",
            "user_picture": "https://example.com/avatar.jpg",
            "user_is_pro": True,
        }
        mock_social_service.get_comments = AsyncMock(return_value=[comment])

        app.dependency_overrides[get_social_service] = lambda: mock_social_service

        response = await client.get(f"/api/v1/social/photos/{comment['photo_id']}/comments")

        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data[0]["id"] == str(comment["id"])
        assert data[0]["user_id"] == str(comment["user_id"])
        assert data[0]["photo_id"] == str(comment["photo_id"])

    @pytest.mark.asyncio
    async def test_update_comment_accepts_uuid_ids(self, client, mock_user, mock_social_service):
        """Comment updates should serialize UUID-backed IDs as strings."""
        comment = {
            "id": uuid4(),
            "user_id": uuid4(),
            "photo_id": uuid4(),
            "content": "updated meow",
            "created_at": "2026-04-15T17:24:00Z",
            "updated_at": "2026-04-15T17:25:00Z",
            "user_name": "Cat Lover",
            "user_picture": "https://example.com/avatar.jpg",
            "user_is_pro": False,
        }
        mock_social_service.update_comment = AsyncMock(return_value=comment)

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_social_service] = lambda: mock_social_service
        app.dependency_overrides[get_current_token] = lambda: "test-token"

        response = await client.put(
            f"/api/v1/social/comments/{comment['id']}",
            json={"content": "updated meow"},
        )

        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(comment["id"])
        assert data["user_id"] == str(comment["user_id"])
        assert data["photo_id"] == str(comment["photo_id"])
