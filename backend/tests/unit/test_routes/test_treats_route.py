from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from dependencies import get_treats_service
from main import app
from middleware.auth_middleware import get_current_user_from_credentials


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client using AsyncClient."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:  # NOSONAR python:S5332 - test base URL
        yield ac


class TestTreatsRoute:
    @pytest.fixture
    def mock_treats_service(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_get_leaderboard_accepts_uuid_ids(self, client, mock_treats_service):
        """Leaderboard responses should serialize UUID-backed IDs as strings."""
        leaderboard_entry = {
            "id": uuid4(),
            "name": "Admin User",
            "username": "admincat",
            "picture": "https://example.com/admin.jpg",
            "total_treats_received": 99,
        }
        mock_treats_service.get_leaderboard = AsyncMock(return_value=[leaderboard_entry])

        app.dependency_overrides[get_treats_service] = lambda: mock_treats_service

        response = await client.get("/api/v1/treats/leaderboard?period=all_time")

        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(leaderboard_entry["id"])

    @pytest.mark.asyncio
    async def test_get_balance_accepts_uuid_transaction_ids(self, client, mock_user, mock_treats_service):
        """Balance responses should serialize UUID-backed transaction IDs as strings."""
        transaction = {
            "id": uuid4(),
            "amount": 5,
            "transaction_type": "give",
            "created_at": "2026-04-15T16:00:00Z",
            "photo_id": uuid4(),
            "from_user_id": uuid4(),
            "to_user_id": uuid4(),
        }
        mock_treats_service.get_balance = AsyncMock(
            return_value={
                "balance": 42,
                "recent_transactions": [transaction],
            }
        )

        app.dependency_overrides[get_current_user_from_credentials] = lambda: mock_user
        app.dependency_overrides[get_treats_service] = lambda: mock_treats_service

        response = await client.get("/api/v1/treats/balance")

        app.dependency_overrides = {}

        assert response.status_code == 200
        data = response.json()
        assert data["recent_transactions"][0]["id"] == str(transaction["id"])
        assert data["recent_transactions"][0]["photo_id"] == str(transaction["photo_id"])
        assert data["recent_transactions"][0]["from_user_id"] == str(transaction["from_user_id"])
        assert data["recent_transactions"][0]["to_user_id"] == str(transaction["to_user_id"])
