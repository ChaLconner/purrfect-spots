"""
Tests for AsyncSupabaseClient
"""
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from utils.async_client import AsyncSupabaseClient


@pytest.fixture
def async_client():
    return AsyncSupabaseClient()


@pytest.mark.asyncio
async def test_rpc_success(async_client):
    """Test RPC call successfully"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [{"result": "success"}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        result = await async_client.rpc("test_func", {"p": 1})
        
        assert result == [{"result": "success"}]
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"] == {"p": 1}


@pytest.mark.asyncio
async def test_select_success(async_client):
    """Test SELECT call successfully"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1, "name": "test"}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        result = await async_client.select("test_table", filters={"id": "eq.1"})
        
        assert result == [{"id": 1, "name": "test"}]
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs["params"]["select"] == "*"
        assert kwargs["params"]["id"] == "eq.1"


@pytest.mark.asyncio
async def test_count_success(async_client):
    """Test COUNT using HEAD request"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.headers = {"Content-Range": "0-0/42"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.head", new_callable=AsyncMock) as mock_head:
        mock_head.return_value = mock_response
        
        result = await async_client.count("test_table")
        
        assert result == 42
        mock_head.assert_called_once()


@pytest.mark.asyncio
async def test_insert_success(async_client):
    """Test INSERT call successfully"""
    mock_data = {"name": "new"}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 201
    mock_response.json.return_value = [{"id": 2, **mock_data}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        result = await async_client.insert("test_table", mock_data)
        
        assert result == [{"id": 2, "name": "new"}]
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_update_success(async_client):
    """Test UPDATE call successfully"""
    mock_data = {"name": "updated"}
    mock_filters = {"id": "eq.2"}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 2, **mock_data}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.patch", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = mock_response
        
        result = await async_client.update("test_table", mock_data, mock_filters)
        
        assert result == [{"id": 2, "name": "updated"}]
        mock_patch.assert_called_once()


@pytest.mark.asyncio
async def test_delete_success(async_client):
    """Test DELETE call successfully"""
    mock_filters = {"id": "eq.2"}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 2}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = mock_response
        
        result = await async_client.delete("test_table", mock_filters)
        
        assert result == [{"id": 2}]
        mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_no_filters_raises(async_client):
    """Test DELETE without filters raises ValueError"""
    with pytest.raises(ValueError, match="Delete requires filters"):
        await async_client.delete("test_table", {})


@pytest.mark.asyncio
async def test_rpc_status_error(async_client):
    """Test RPC HTTP status error handling"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Err", request=MagicMock(), response=mock_response)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(httpx.HTTPStatusError):
            await async_client.rpc("test_func")

@pytest.mark.asyncio
async def test_select_status_error(async_client):
    """Test SELECT HTTP status error handling"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 404
    mock_response.text = "Not Found"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Err", request=MagicMock(), response=mock_response)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with pytest.raises(httpx.HTTPStatusError):
            await async_client.select("test_table")

@pytest.mark.asyncio
async def test_count_fallback(async_client):
    """Test COUNT fallback when HEAD fails"""
    with patch("httpx.AsyncClient.head", new_callable=AsyncMock) as mock_head:
        mock_head.side_effect = Exception("HEAD failed")
        
        # Should fallback to select
        with patch.object(async_client, "select", new_callable=AsyncMock) as mock_select:
            mock_select.return_value = [{"id": 1}, {"id": 2}]
            result = await async_client.count("test_table")
            assert result == 2

@pytest.mark.asyncio
async def test_count_total_failure(async_client):
    """Test COUNT total failure returns 0"""
    with patch("httpx.AsyncClient.head", new_callable=AsyncMock) as mock_head:
        mock_head.side_effect = Exception("HEAD failed")
        with patch.object(async_client, "select", new_callable=AsyncMock) as mock_select:
            mock_select.side_effect = Exception("SELECT failed")
            result = await async_client.count("test_table")
            assert result == 0

@pytest.mark.asyncio
async def test_insert_status_error(async_client):
    """Test INSERT HTTP status error handling"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Err", request=MagicMock(), response=mock_response)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(httpx.HTTPStatusError):
            await async_client.insert("test_table", {"a": 1})

@pytest.mark.asyncio
async def test_update_status_error(async_client):
    """Test UPDATE HTTP status error handling"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Err", request=MagicMock(), response=mock_response)

    with patch("httpx.AsyncClient.patch", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = mock_response
        with pytest.raises(httpx.HTTPStatusError):
            await async_client.update("test_table", {"a": 1}, {"id": "eq.1"})

@pytest.mark.asyncio
async def test_delete_status_error(async_client):
    """Test DELETE HTTP status error handling"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("Err", request=MagicMock(), response=mock_response)

    with patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = mock_response
        with pytest.raises(httpx.HTTPStatusError):
            await async_client.delete("test_table", {"id": "eq.1"})

@pytest.mark.asyncio
async def test_delete_no_content(async_client):
    """Test DELETE returns empty list on 204 No Content"""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 204
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = mock_response
        result = await async_client.delete("test_table", {"id": "eq.1"})
        assert result == []
