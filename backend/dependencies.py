"""
Dependencies module for shared dependencies across the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client
from fastapi import HTTPException

# Try multiple paths for .env file
current_dir = Path(__file__).parent
env_paths = [
    current_dir / '.env',
    current_dir.parent / '.env',
    Path('.env'),
    Path('backend/.env')
]

print(f"🔍 Current working directory: {os.getcwd()}")
print(f"🔍 Script directory: {current_dir}")

env_loaded = False
for env_path in env_paths:
    print(f"🔍 Trying .env path: {env_path}")
    if env_path.exists():
        print(f"🔍 Found .env at: {env_path}")
        load_dotenv(env_path)
        env_loaded = True
        break

if not env_loaded:
    print("🔥 No .env file found, trying default load_dotenv()")
    load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Debug: Print environment variables
print(f"🔍 SUPABASE_URL: {SUPABASE_URL}")
print(f"🔍 SUPABASE_KEY: {'*' * len(SUPABASE_KEY) if SUPABASE_KEY else 'NOT SET'}")

# Manual fallback for debugging
if not SUPABASE_URL:
    print("🔥 Environment variables not loaded, trying manual approach...")
    SUPABASE_URL = "https://poubdfhpujvqrkbcdzmc.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvdWJkZmhwdWp2cXJrYmNkem1jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2Mzk4NjMsImV4cCI6MjA2NzIxNTg2M30.iikgVLLwd3EZUnBmsSaf6qab3VOjvVFSxxdPz3Q9ZPY"
    print(f"🔍 Using manual values - SUPABASE_URL: {SUPABASE_URL}")

# Check if required environment variables are set
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is not set")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is not set")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase_client():
    """Get Supabase client instance"""
    return supabase
