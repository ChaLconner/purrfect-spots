import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load .env from backend directory
backend_dir = Path(__file__).parent
env_path = backend_dir / '.env'

if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to local .env if backend one doesn't exist
    load_dotenv()

# Supabase client initialization
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

print(f"🔍 Debug: SUPABASE_URL found: {bool(supabase_url)}")
print(f"🔍 Debug: SUPABASE_KEY found: {bool(supabase_key)}")
print(f"🔍 Debug: SUPABASE_ANON_KEY found: {bool(os.getenv('SUPABASE_ANON_KEY'))}")

if not supabase_url:
    raise ValueError("SUPABASE_URL must be set in environment variables")

if not supabase_key:
    raise ValueError("SUPABASE_KEY or SUPABASE_ANON_KEY must be set in environment variables")

# Create two clients: one for regular operations, one for admin operations
supabase = create_client(supabase_url, supabase_key)

# Service role client for admin operations (bypasses RLS)
supabase_service_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
supabase_admin = None
if supabase_service_key:
    supabase_admin = create_client(supabase_url, supabase_service_key)
    print(f"🔍 Debug: SUPABASE_SERVICE_KEY found: {bool(supabase_service_key)}")
else:
    print("⚠️ Warning: SUPABASE_SECRET_KEY not found - admin operations will use regular client")

def get_supabase_client():
    """Get Supabase client instance"""
    return supabase

def get_supabase_admin_client():
    """Get Supabase admin client instance (bypasses RLS)"""
    return supabase_admin or supabase