"""
Authentication middleware for protecting routes with Supabase Auth
"""
from fastapi import HTTPException, Depends, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from supabase import Client
import jwt
from jwt import PyJWTError
import os
import requests
from dependencies import get_supabase_client
from user_models.user import User


security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret")

# Supabase JWKS setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
if SUPABASE_URL:
    PROJECT_ID = SUPABASE_URL.split("//")[1].split(".")[0]
    JWKS_URL = f"https://{PROJECT_ID}.supabase.co/auth/v1/keys"
    
    try:
        jwks_response = requests.get(JWKS_URL)
        jwks = jwks_response.json() if jwks_response.status_code == 200 else None
    except Exception:
        jwks = None
else:
    jwks = None
    PROJECT_ID = None


def decode_supabase_token(token: str):
    """Decode Supabase JWT token using JWKS"""
    try:
        if not jwks:
            raise ValueError("JWKS not available")
            
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise ValueError("Token missing 'kid' in header")
            
        # Find the key with matching kid
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise ValueError(f"Key with kid '{kid}' not found in JWKS")
            
        # Convert JWK to public key
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        
        # Decode and verify token
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        return payload
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Supabase token: {str(e)}")


def decode_custom_token(token: str):
    """Decode custom JWT token (fallback)"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_from_header(authorization: str = Header(...)):
    """Get current user from Authorization header (Supabase style)"""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
            
        token = authorization.split(" ")[1]
        
        # Try Supabase token first
        try:
            payload = decode_supabase_token(token)
            return payload
        except HTTPException:
            # Fallback to custom token
            payload = decode_custom_token(token)
            return payload
            
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_current_user_from_credentials(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
):
    """Get current authenticated user using Supabase Auth (original function)"""
    token = credentials.credentials
    
    # Try Supabase token first
    try:
        payload = decode_supabase_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Try to get user from database
        try:
            result = supabase.table("users").select("*").eq("id", user_id).single().execute()
            if result.data:
                # Convert dict to User object
                return User(
                    id=result.data["id"],
                    email=result.data.get("email", ""),
                    name=result.data.get("name", ""),
                    picture=result.data.get("picture", ""),
                    bio=result.data.get("bio"),
                    created_at=result.data.get("created_at", "")
                )
        except Exception:
            pass
        
        # If user not found in database, return Supabase JWT payload data
        user_metadata = payload.get("user_metadata", {})
        app_metadata = payload.get("app_metadata", {})
        
        return User(
            id=user_id,
            email=payload.get("email", ""),
            name=user_metadata.get("name", user_metadata.get("full_name", "")),
            picture=user_metadata.get("avatar_url", user_metadata.get("picture", "")),
            bio=None,
            created_at=str(payload.get("iat", ""))
        )
        
        return user_data
        
    except HTTPException:
        # Fallback to custom token
        try:
            payload = decode_custom_token(token)
            user_id = payload.get("sub") or payload.get("user_id")

            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")

            # Try to get user from database
            try:
                result = supabase.table("users").select("*").eq("id", user_id).single().execute()
                if result.data:
                    # Convert dict to User object
                    return User(
                        id=result.data["id"],
                        email=result.data.get("email", ""),
                        name=result.data.get("name", ""),
                        picture=result.data.get("picture", ""),
                        bio=result.data.get("bio"),
                        created_at=result.data.get("created_at", "")
                    )
            except Exception:
                pass
            
            # If user not found in database, return custom JWT payload data
            return User(
                id=user_id,
                email=payload.get("email", ""),
                name=payload.get("name", ""),
                picture=payload.get("picture", ""),
                bio=None,
                created_at=str(payload.get("iat", ""))
            )
            
        except Exception:
            raise HTTPException(status_code=401, detail="Authentication failed")


def get_current_user(request: Request):
    """Get current user from request headers using JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = auth_header.split(" ")[1]
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET_KEY", os.getenv("JWT_SECRET", "your-secret")),
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return User(
            id=user_id, 
            email=payload.get("email", ""),
            name=payload.get("name", ""),
            picture=payload.get("picture", ""),
            bio=payload.get("bio"),
            created_at=payload.get("iat", "")
        )

    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as e:
        print(f"🛑 JWT Decode Error: {e}")
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
    except Exception as e:
        print(f"🛑 Unknown Auth Error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


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
