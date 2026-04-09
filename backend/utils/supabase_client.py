import httpx

from config import config
from logger import logger
from supabase import AClient, AClientOptions, Client, ClientOptions, acreate_client, create_client

# Internal HTTPX client pool for performance and to avoid [Errno 99] port exhaustion
_shared_httpx_client: httpx.AsyncClient | None = None


def get_shared_httpx_client() -> httpx.AsyncClient:
    global _shared_httpx_client
    if _shared_httpx_client is None:
        # Use a large enough pool and short keep-alives for serverless execution
        _shared_httpx_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            trust_env=False,
        )
    return _shared_httpx_client


# Initialize Supabase clients
# Use a fail-soft approach for development/test environments
is_production = config.ENVIRONMENT.lower() == "production"

supabase_url = config.SUPABASE_URL
supabase_key = config.SUPABASE_KEY

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

# Shared client options for timeouts
client_options = ClientOptions(
    postgrest_client_timeout=30.0,
    storage_client_timeout=30.0,
)

async_client_options = AClientOptions(
    postgrest_client_timeout=30.0,
    storage_client_timeout=30.0,
)

# Synchronous clients (for legacy support and small tasks)
supabase: Client = create_client(supabase_url, supabase_key, options=client_options)

# Admin client
supabase_service_key = config.SUPABASE_SERVICE_KEY
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


async def get_async_supabase_client() -> AClient:
    """Get high-performance async Supabase client"""
    global _async_supabase
    if _async_supabase is None:
        _async_supabase = await acreate_client(supabase_url, supabase_key, options=async_client_options)
    return _async_supabase


async def get_async_supabase_admin_client() -> AClient:
    """Get high-performance async Supabase admin client (bypasses RLS)"""
    global _async_supabase_admin
    if _async_supabase_admin is None:
        service_key = config.SUPABASE_SERVICE_KEY
        if not service_key:
            logger.error("SUPABASE_SERVICE_ROLE_KEY is missing! Admin client cannot bypass RLS.")
            if config.is_production():
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for admin operations")
            service_key = config.SUPABASE_KEY  # Dev fallback

        _async_supabase_admin = await acreate_client(supabase_url, service_key, options=async_client_options)
    return _async_supabase_admin
