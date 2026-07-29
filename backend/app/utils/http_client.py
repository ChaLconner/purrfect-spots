import httpx

# Internal HTTPX client pool for performance and to avoid [Errno 99] port exhaustion
# This is a singleton instance shared across the entire application.
_shared_httpx_client: httpx.AsyncClient | None = None


def get_shared_httpx_client() -> httpx.AsyncClient:
    """
    Get or create a shared httpx.AsyncClient instance.
    This helps in connection pooling and prevents socket leaks (Errno 99).
    """
    global _shared_httpx_client
    if _shared_httpx_client is None:
        # Use a large enough pool and short keep-alives for serverless execution.
        # Limits:
        # - max_connections: Total concurrent connections
        # - max_keepalive_connections: Connections to keep open in the pool
        _shared_httpx_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            trust_env=False,  # Performance boost: skip searching for system proxies
        )
    return _shared_httpx_client


async def close_shared_httpx_client() -> None:
    """
    Close the shared client pool. Should be called on application shutdown.
    """
    global _shared_httpx_client
    if _shared_httpx_client is not None:
        await _shared_httpx_client.aclose()
        _shared_httpx_client = None
