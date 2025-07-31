"""
Dependencies module for shared dependencies across the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Try multiple paths for .env file
current_dir = Path(__file__).parent
env_paths = [
    current_dir / '.env',
    current_dir.parent / '.env',
    Path('.env'),
    Path('backend/.env')
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    load_dotenv()  # fallback

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is not set")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is not set")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client():
    """Get Supabase client instance"""
    return supabase
