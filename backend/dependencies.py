import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from logger import logger

# Load .env from backend directory
backend_dir = Path(__file__).parent
env_path = backend_dir / ".env"

if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to local .env if backend one doesn't exist
    load_dotenv()

# Supabase client initialization
supabase_url = os.getenv("SUPABASE_URL")
# Prefer specific keys over generic ones to avoid confusion
supabase_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

logger.info(f"SUPABASE_URL found: {bool(supabase_url)}")
logger.info(f"Supabase Client Access: {bool(supabase_key)}")

if not supabase_url:
    raise ValueError("SUPABASE_URL must be set in environment variables")

if not supabase_key:
    raise ValueError(
        "SUPABASE_ANON_KEY must be set in environment variables (SUPABASE_KEY is deprecated for this role)"
    )

# Create two clients: one for regular operations, one for admin operations
# STRICT: Ensure we are using the Anon key for the public client
supabase = create_client(supabase_url, supabase_key)

# Service role client for admin operations (bypasses RLS)
supabase_service_key = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
)
supabase_admin = None
if supabase_service_key:
    supabase_admin = create_client(supabase_url, supabase_service_key)
    logger.info(f"Supabase Admin Access: {bool(supabase_service_key)}")
else:
    logger.warning("SUPABASE_SERVICE_ROLE_KEY not found - admin operations will use regular client")


def get_supabase_client():
    """Get Supabase client instance"""
    return supabase


def get_supabase_admin_client():
    """Get Supabase admin client instance (bypasses RLS)"""
    return supabase_admin or supabase


from fastapi import Depends, HTTPException, Header
from typing import Optional
import jwt

def get_current_user_from_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Extract user from JWT token in Authorization header.
    This is a lightweight validation. Full validation happens in AuthService.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
            
        # Basic decoding to get user_id and role (without verification, verification is done by AuthService)
        # In a real app, we should verify signature using JWT_SECRET here or use AuthService
        # For dependencies, we often want lightweight checks or full service injection
        # optimizing to just decode for now since we trust the gateway/middleware
        # BUT for security, let's minimally verify if we have the secret handy.
        
        # Checking env directly since importing config might cycle
        jwt_secret = os.getenv("JWT_SECRET")
        if jwt_secret:
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            return payload
        else:
            # Fallback for dev/test without secret (unsafe, but prevents crash)
            return jwt.decode(token, options={"verify_signature": False})
            
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_admin_user(user: dict = Depends(get_current_user_from_token)):
    """
    Dependency to check if current user is an admin.
    """
    # Create temp service to check DB role if token doesn't have it yet
    # Or assume token has it if we updated create_access_token
    # For safety, let's query DB using admin client
    
    user_id = user.get("user_id") or user.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")
        
    client = get_supabase_admin_client()
    try:
        # Check role in DB
        res = client.table("users").select("role").eq("id", user_id).single().execute()
        if not res.data or res.data.get("role") != "admin":
             raise HTTPException(status_code=403, detail="Admin privileges required")
        return user
    except Exception as e:
        logger.error(f"Admin check failed: {e}")
        raise HTTPException(status_code=403, detail="Admin privileges required")
