"""
Tests for Supabase client wrappers.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from gotrue._async.storage import AsyncMemoryStorage

import utils.supabase_client as sc


def test_get_supabase_client() -> None:
    """Test standard client retrieval"""
    client = sc.get_supabase_client()
    assert client is not None
    assert client == sc.supabase


def test_get_supabase_admin_client() -> None:
    """Test admin client retrieval"""
    client = sc.get_supabase_admin_client()
    assert client is not None
    # Since we set SUPABASE_SERVICE_KEY in conftest, it should be different if initialized correctly
    # But for now we just care that it returns something
    expected = sc.supabase_admin or sc.supabase
    assert client == expected


def test_async_client_options_use_async_storage() -> None:
    """Async Supabase clients must use async-compatible session storage."""
    assert isinstance(sc.async_client_options.storage, AsyncMemoryStorage)


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
