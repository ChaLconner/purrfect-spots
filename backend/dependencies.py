from typing import Optional

from fastapi import Depends, Header, HTTPException

from logger import logger
from utils.auth_utils import decode_token
from utils.supabase_client import get_supabase_admin_client, get_supabase_client

# Re-export for compatibility
__all__ = ["get_supabase_client", "get_supabase_admin_client", "get_current_user_from_token", "get_current_admin_user", "get_current_token"]


def get_current_user_from_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Extract and verify user from JWT token in Authorization header.
    Always verifies the JWT signature using JWT_SECRET.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # Parse the Authorization header
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    token = parts[1]

    try:
        return decode_token(token)
    except ValueError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected token validation error: {type(e).__name__}")
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """
    Extract the JWT token string from the Authorization header.
    Returns None if header is missing or invalid scheme.
    """
    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None


def get_current_admin_user(user: dict = Depends(get_current_user_from_token)) -> dict:
    """
    Dependency to check if current user is an admin.
    """
    # Optimization: Check JWT claim first
    if user.get("role") == "admin":
        return user

    # Fallback: Check role in DB (for older tokens or Supabase tokens without claim)
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
