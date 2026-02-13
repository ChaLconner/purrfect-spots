from supabase import Client, create_client

from config import config
from logger import logger

# Initialize Supabase clients
supabase_url = config.SUPABASE_URL
supabase_key = config.SUPABASE_KEY

if not supabase_url:
    raise ValueError("SUPABASE_URL must be set in environment variables")
if not supabase_key:
    raise ValueError("SUPABASE_KEY must be set in environment variables")

# Public client
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
    """Get Supabase client instance"""
    return supabase


def get_supabase_admin_client() -> Client:
    """Get Supabase admin client instance (bypasses RLS)"""
    return supabase_admin or supabase
