from unittest.mock import AsyncMock

import httpx
import pytest

from app.utils.retry import retry_on_network_error


@pytest.mark.asyncio
async def test_retry_success_first_attempt():
    func = AsyncMock(return_value="success")
    result = await retry_on_network_error(func, "arg1", kwarg1="val1", initial_delay=0.001)

    assert result == "success"
    func.assert_called_once_with("arg1", kwarg1="val1")


@pytest.mark.asyncio
async def test_retry_success_after_failure():
    # Fails first time with ConnectError, succeeds second time
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise httpx.ConnectError("Device or resource busy")
        return "success"

    result = await retry_on_network_error(mock_func, initial_delay=0.001)

    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted_raises():
    # Fails every time
    async def mock_func():
        raise httpx.ConnectError("[Errno 16] Device or resource busy")

    with pytest.raises(httpx.ConnectError):
        await retry_on_network_error(mock_func, max_retries=3, initial_delay=0.001)


@pytest.mark.asyncio
async def test_no_retry_on_other_exceptions():
    # Standard ValueError should not be retried and should fail immediately
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        raise ValueError("Bad input")

    with pytest.raises(ValueError):
        await retry_on_network_error(mock_func, max_retries=3, initial_delay=0.001)

    assert call_count == 1
