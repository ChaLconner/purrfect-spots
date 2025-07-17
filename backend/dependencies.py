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

# Debug Google OAuth credentials
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
print(f"🔍 GOOGLE_CLIENT_ID: {'✅ Found' if google_client_id else '❌ Not found'}")
print(f"🔍 GOOGLE_CLIENT_SECRET: {'✅ Found' if google_client_secret else '❌ Not found'}")
if google_client_id:
    print(f"🔍 GOOGLE_CLIENT_ID starts with: {google_client_id[:20]}...")
if google_client_secret:
    print(f"🔍 GOOGLE_CLIENT_SECRET starts with: {google_client_secret[:20]}...")

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
    # ใช้ SERVICE ROLE KEY แทน anon key สำหรับ backend operations
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvdWJkZmhwdWp2cXJrYmNkem1jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTYzOTg2MywiZXhwIjoyMDY3MjE1ODYzfQ.mZiDaLZe8z-6QAhm-dWl5xQ-6vGeFaCQFh8kuWw4QY4"
    print(f"🔍 Using service role key for backend operations")

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
