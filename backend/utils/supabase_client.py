import os
from typing import Any, cast

from gotrue._async.storage import AsyncMemoryStorage

from config import config, normalize_single_line_env
from logger import logger
from supabase import AClient, AClientOptions, Client, ClientOptions, acreate_client, create_client


def _resolve_supabase_service_key() -> str:
    """Resolve the service-role key from live environment first, then config cache."""
    env_value = normalize_single_line_env(os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))
    if env_value:
        return env_value
    return normalize_single_line_env(config.SUPABASE_SERVICE_KEY)


def has_supabase_service_role_key() -> bool:
    """Return True when a service-role key is currently available."""
    return bool(_resolve_supabase_service_key())


# Initialize Supabase clients
# Use a fail-soft approach for development/test environments
is_production = config.ENVIRONMENT.lower() == "production"

supabase_url = normalize_single_line_env(config.SUPABASE_URL)
supabase_key = normalize_single_line_env(config.SUPABASE_KEY)

if not supabase_url:
    if is_production:
        raise ValueError("SUPABASE_URL must be set in environment variables")
    # Default to localhost for development/testing if not specified
    supabase_url = "http://127.0.0.1:54321"

# Ensure no localhost in URL to prevent [Errno 99] IPv6 resolution issues
if "localhost" in supabase_url:
    supabase_url = supabase_url.replace("localhost", "127.0.0.1")

if not supabase_key:
    if is_production:
        raise ValueError("SUPABASE_KEY must be set in environment variables")
    # Use a dummy key for development/testing if not specified
    supabase_key = "dummy-anon-key"

# Shared client options for timeouts and connection pooling
# Using a shared http_client prevents [Errno 99] port exhaustion
client_options = ClientOptions(
    postgrest_client_timeout=30.0,
    storage_client_timeout=30.0,
)

async_client_options = AClientOptions(
    storage=cast(Any, AsyncMemoryStorage()),
    postgrest_client_timeout=30.0,
    storage_client_timeout=30.0,
)

# Synchronous clients (for legacy support and small tasks)
supabase: Client = create_client(supabase_url, supabase_key, options=client_options)

# Admin client
supabase_service_key = _resolve_supabase_service_key()
supabase_admin: Client | None = None
if supabase_service_key:
    supabase_admin = create_client(supabase_url, supabase_service_key, options=client_options)
    logger.info("Supabase Admin Access: Enabled")
else:
    logger.warning("SUPABASE_SERVICE_ROLE_KEY not found - admin operations will use regular client")


def get_supabase_client() -> Client:
    """Get synchronous Supabase client instance"""
    return supabase


def get_supabase_admin_client() -> Client:
    """Get synchronous Supabase admin client instance (bypasses RLS)"""
    return supabase_admin or supabase


# --- Async Clients ---

_async_supabase: AClient | None = None
_async_supabase_admin: AClient | None = None
_async_supabase_admin_key: str | None = None
_async_supabase_admin_state: dict[str, AClient | str | None] = {"client": None, "key": None}


async def get_async_supabase_client() -> AClient:
    """Get high-performance async Supabase client"""
    global _async_supabase  # noqa: PLW0603
    if _async_supabase is None:
        _async_supabase = await acreate_client(supabase_url, supabase_key, options=async_client_options)
    return _async_supabase


def reset_async_supabase_admin_client() -> None:
    """Drop the cached async admin client so the next request recreates it."""
    global _async_supabase_admin, _async_supabase_admin_key  # noqa: PLW0603
    _async_supabase_admin = None
    _async_supabase_admin_key = None
    _async_supabase_admin_state["client"] = None
    _async_supabase_admin_state["key"] = None


async def get_async_supabase_admin_client(force_refresh: bool = False) -> AClient:
    """Get high-performance async Supabase admin client (bypasses RLS)"""
    global _async_supabase_admin, _async_supabase_admin_key  # noqa: PLW0603
    service_key = _resolve_supabase_service_key()

    if force_refresh:
        reset_async_supabase_admin_client()

    cached_service_key = _async_supabase_admin_key or cast(str | None, _async_supabase_admin_state["key"])
    if _async_supabase_admin is None or cached_service_key != service_key:
        if not service_key:
            logger.error("SUPABASE_SERVICE_ROLE_KEY is missing! Admin client cannot bypass RLS.")
            if config.is_production():
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for admin operations")
            service_key = normalize_single_line_env(config.SUPABASE_KEY)  # Dev fallback

        _async_supabase_admin = await acreate_client(supabase_url, service_key, options=async_client_options)
        _async_supabase_admin_key = service_key
        _async_supabase_admin_state["client"] = _async_supabase_admin
        _async_supabase_admin_state["key"] = service_key
    return _async_supabase_admin
