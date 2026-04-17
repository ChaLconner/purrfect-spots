"""
Tests for Supabase client wrappers.
"""

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import utils.supabase_client as sc


def test_get_supabase_client() -> None:
    """Test standard client retrieval"""
    mock_client = MagicMock(name="supabase-client")

    with (
        patch("utils.supabase_client.supabase", None),
        patch("utils.supabase_client._supabase_key", None),
        patch("utils.supabase_client._resolve_supabase_url", return_value="http://127.0.0.1:54321"),
        patch("utils.supabase_client._resolve_supabase_anon_key", return_value="test-anon-key"),
        patch("utils.supabase_client.create_client", return_value=mock_client) as mock_create,
    ):
        client = sc.get_supabase_client()
        cached_client = sc.get_supabase_client()
        assert sc.supabase is mock_client

    assert client is mock_client
    assert cached_client is mock_client
    mock_create.assert_called_once()


def test_get_supabase_admin_client() -> None:
    """Test admin client retrieval"""
    mock_admin_client = MagicMock(name="supabase-admin-client")

    with (
        patch("utils.supabase_client.supabase_admin", None),
        patch("utils.supabase_client._supabase_admin_key", None),
        patch("utils.supabase_client._resolve_supabase_url", return_value="http://127.0.0.1:54321"),
        patch("utils.supabase_client._resolve_supabase_service_key", return_value="test-service-role-key"),
        patch("utils.supabase_client.create_client", return_value=mock_admin_client) as mock_create,
    ):
        client = sc.get_supabase_admin_client()
        cached_client = sc.get_supabase_admin_client()
        assert sc.supabase_admin is mock_admin_client

    assert client is mock_admin_client
    assert cached_client is mock_admin_client
    mock_create.assert_called_once()


def test_async_client_options_use_async_storage() -> None:
    """Async Supabase clients must use async-compatible session storage."""
    storage = cast(Any, sc.async_client_options.storage)
    assert callable(getattr(storage, "get_item", None))
    assert callable(getattr(storage, "set_item", None))
    assert callable(getattr(storage, "remove_item", None))


@pytest.mark.asyncio
async def test_get_async_supabase_client():
    """Test async client retrieval and initialization"""
    # Reset the global state to force initialization
    with (
        patch("utils.supabase_client._async_supabase", None),
        patch("utils.supabase_client.acreate_client", new_callable=AsyncMock) as mock_ac,
    ):
        mock_ac.return_value = MagicMock()
        client = await sc.get_async_supabase_client()
        assert client is not None
        mock_ac.assert_called_once()

        # Second call should use cached client
        client2 = await sc.get_async_supabase_client()
        assert client2 == client
        assert mock_ac.call_count == 1


@pytest.mark.asyncio
async def test_get_async_supabase_admin_client():
    """Test async admin client retrieval and initialization"""
    # Reset the global state to force initialization
    with (
        patch("utils.supabase_client._async_supabase_admin", None),
        patch("utils.supabase_client._async_supabase_admin_key", None),
        patch("utils.supabase_client.acreate_client", new_callable=AsyncMock) as mock_ac,
    ):
        mock_ac.return_value = MagicMock()
        client = await sc.get_async_supabase_admin_client()
        assert client is not None
        mock_ac.assert_called_once()

        # Second call should use cached client
        client2 = await sc.get_async_supabase_admin_client()
        assert client2 == client
        assert mock_ac.call_count == 1


@pytest.mark.asyncio
async def test_get_async_supabase_admin_client_recreates_when_service_key_changes():
    """Admin client should refresh when the live service-role key changes."""
    first_client = MagicMock(name="first")
    second_client = MagicMock(name="second")

    with (
        patch("utils.supabase_client._async_supabase_admin", None),
        patch("utils.supabase_client._async_supabase_admin_key", None),
        patch("utils.supabase_client.acreate_client", new_callable=AsyncMock) as mock_ac,
        patch("utils.supabase_client._resolve_supabase_service_key", side_effect=["key-one", "key-two"]),
    ):
        mock_ac.side_effect = [first_client, second_client]

        client = await sc.get_async_supabase_admin_client()
        refreshed_client = await sc.get_async_supabase_admin_client()

        assert client == first_client
        assert refreshed_client == second_client
        assert mock_ac.call_count == 2
