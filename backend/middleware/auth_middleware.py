"""
Authentication middleware for protecting routes with Supabase Auth
"""
from fastapi import HTTPException, Depends, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from supabase import Client
import jwt
import os
import httpx
import time
from dependencies import get_supabase_client
from user_models.user import User

security = HTTPBearer()

# JWKS Cache
_jwks_cache = None
_jwks_last_update = 0
JWKS_CACHE_TTL = 3600  # 1 hour

async def get_jwks():
    """Lazily fetch and cache JWKS"""
    global _jwks_cache, _jwks_last_update
    
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        return None
        
    project_id = supabase_url.split("//")[1].split(".")[0]
    jwks_url = f"https://{project_id}.supabase.co/auth/v1/keys"
    
    current_time = time.time()
    if _jwks_cache and (current_time - _jwks_last_update < JWKS_CACHE_TTL):
        return _jwks_cache
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=5)
            if response.status_code == 200:
                _jwks_cache = response.json()
                _jwks_last_update = current_time
                return _jwks_cache
    except Exception:
        pass
    
    return _jwks_cache

async def decode_supabase_token(token: str):
    """Decode Supabase JWT token using JWKS"""
    try:
        jwks = await get_jwks()
        if not jwks:
            # If JWKS is not available, we can't verify Supabase tokens properly
            # But we might be in an environment without Supabase URL (unlikely but possible)
            raise ValueError("JWKS not available")
            
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise ValueError("Token missing 'kid' in header")
            
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise ValueError(f"Key with kid '{kid}' not found in JWKS")
            
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience="authenticated")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Supabase token: {str(e)}")

def decode_custom_token(token: str):
    """Decode custom JWT token (fallback)"""
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
         raise HTTPException(status_code=500, detail="Server misconfiguration: JWT_SECRET not set")
         
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def _get_user_from_payload(payload: dict, source: str) -> User:
    """Helper to convert JWT payload to User object"""
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Try to get user from database (bypassing RLS)
    try:
        from dependencies import get_supabase_admin_client
        supabase_admin = get_supabase_admin_client()
        result = supabase_admin.table("users").select("*").eq("id", user_id).single().execute()
        if result.data:
            return User(
                id=result.data["id"],
                email=result.data.get("email", ""),
                name=result.data.get("name", ""),
                picture=result.data.get("picture", ""),
                bio=result.data.get("bio"),
                created_at=result.data.get("created_at", "")
            )
    except Exception:
        # Fallback to payload data if DB lookup fails
        pass

    # Construct User from payload
    if source == "supabase":
        user_metadata = payload.get("user_metadata", {})
        return User(
            id=user_id,
            email=payload.get("email", ""),
            name=user_metadata.get("name", user_metadata.get("full_name", "")),
            picture=user_metadata.get("avatar_url", user_metadata.get("picture", "")),
            bio=None,
            created_at=str(payload.get("iat", ""))
        )
    else: # custom
        return User(
            id=user_id,
            email=payload.get("email", ""),
            name=payload.get("name", ""),
            picture=payload.get("picture", ""),
            bio=payload.get("bio"),
            created_at=payload.get("iat", "")
        )

async def _verify_and_decode_token(token: str) -> tuple[dict, str]:
    """Helper to verify and decode token, trying Supabase first then custom"""
    try:
        # Try Supabase token first
        payload = await decode_supabase_token(token)
        return payload, "supabase"
    except (HTTPException, ValueError):
        # Try custom token as fallback
        try:
            payload = decode_custom_token(token)
            return payload, "custom"
        except Exception:
            raise HTTPException(status_code=401, detail="Authentication failed")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_current_user_from_credentials(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
):
    """Get current authenticated user using Supabase Auth"""
    token = credentials.credentials
    payload, source = await _verify_and_decode_token(token)
    return _get_user_from_payload(payload, source)

async def get_current_user(request: Request):
    """Get current user from request headers using JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.split(" ")[1]
    payload, source = await _verify_and_decode_token(token)
    return _get_user_from_payload(payload, source)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase: Client = Depends(get_supabase_client)
):
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    try:
        return await get_current_user_from_credentials(credentials, supabase)
    except HTTPException:
        return None

async def get_current_user_from_header(request: Request):
    """Get decoded token payload from request headers"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.split(" ")[1]
    payload, _ = await _verify_and_decode_token(token)
    return payload
