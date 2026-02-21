from typing import Optional

from supabase import AClient, Client, acreate_client, create_client

from config import config
from logger import logger

# Initialize Supabase clients
supabase_url = config.SUPABASE_URL
supabase_key = config.SUPABASE_KEY

if not supabase_url:
    raise ValueError("SUPABASE_URL must be set in environment variables")
if not supabase_key:
    raise ValueError("SUPABASE_KEY must be set in environment variables")

# Synchronous clients (for legacy support and small tasks)
supabase: Client = create_client(supabase_url, supabase_key)

# Admin client
supabase_service_key = config.SUPABASE_SERVICE_KEY
supabase_admin: Client | None = None
if supabase_service_key:
    supabase_admin = create_client(supabase_url, supabase_service_key)
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

_async_supabase: Optional[AClient] = None
_async_supabase_admin: Optional[AClient] = None


async def get_async_supabase_client() -> AClient:
    """Get high-performance async Supabase client"""
    global _async_supabase
    if _async_supabase is None:
        _async_supabase = await acreate_client(supabase_url, supabase_key)
    return _async_supabase


async def get_async_supabase_admin_client() -> AClient:
    """Get high-performance async Supabase admin client (bypasses RLS)"""
    global _async_supabase_admin
    if _async_supabase_admin is None:
        service_key = config.SUPABASE_SERVICE_KEY or config.SUPABASE_KEY
        _async_supabase_admin = await acreate_client(supabase_url, service_key)
    return _async_supabase_admin
