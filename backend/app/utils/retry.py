import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import httpx
from sqlalchemy.exc import OperationalError

from app.compat import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


async def retry_on_network_error(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    **kwargs: Any,
) -> T:
    """Execute async function with exponential backoff retry on connection errors."""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            err_msg = str(e)
            is_conn_err = isinstance(
                e, (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError, httpx.RequestError)
            )
            is_db_conn_err = isinstance(e, OperationalError)
            is_busy_err = "Device or resource busy" in err_msg or "[Errno 16]" in err_msg

            if (is_conn_err or is_db_conn_err or is_busy_err) and attempt < max_retries - 1:
                logger.warning(
                    "Network connection error, retrying call...",
                    error=err_msg,
                    attempt=attempt + 1,
                    next_retry_delay=delay,
                )
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise
    raise RuntimeError("Unreachable")
