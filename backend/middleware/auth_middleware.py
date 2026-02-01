"""
Authentication middleware for protecting routes with Supabase Auth
"""

import os
import time
from datetime import datetime, timezone

import httpx
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from config import config
from dependencies import get_supabase_admin_client, get_supabase_client
from logger import logger
from services.token_service import get_token_service
from user_models.user import User

security = HTTPBearer()

# JWKS Cache
_jwks_cache: dict | None = None
_jwks_last_update: int = 0
JWKS_CACHE_TTL = 3600  # 1 hour


async def get_jwks():
    """Lazily fetch and cache JWKS"""
    global _jwks_cache, _jwks_last_update

    supabase_url = config.SUPABASE_URL
    if not supabase_url:
        return None

    try:
        project_id = supabase_url.split("//")[1].split(".")[0]
        jwks_url = f"https://{project_id}.supabase.co/auth/v1/keys"
    except IndexError:
        return None

    current_time = time.time()
    if _jwks_cache and (current_time - _jwks_last_update < JWKS_CACHE_TTL):
        return _jwks_cache

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=5)
            if response.status_code == 200:
                _jwks_cache = response.json()
                _jwks_last_update = int(current_time)
                return _jwks_cache
    except Exception as e:
        logger.warning("Failed to refresh JWKS cache: %s", e)

    return _jwks_cache


async def decode_supabase_token(token: str):
    """Decode Supabase JWT token using JWKS"""
    try:
        jwks = await get_jwks()
        if not jwks:
            raise ValueError("JWKS not available")

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise ValueError("Token missing 'kid' in header")

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise ValueError(f"Key with kid '{kid}' not found in JWKS")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(token, public_key, algorithms=["RS256"], audience="authenticated")  # type: ignore[arg-type]
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Supabase token: {e!s}")


def decode_custom_token(token: str):
    """Decode custom JWT token (fallback) - Sync part"""
    jwt_secret = config.JWT_SECRET
    if not jwt_secret:
        raise HTTPException(status_code=500, detail="Server misconfiguration: JWT_SECRET not set")

    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def _is_token_revoked(jti: str) -> bool:
    """Check if token JTI is in blacklist using TokenService"""
    if not jti:
        return False

    try:
        token_service = await get_token_service()
        return await token_service.is_blacklisted(jti=jti)
    except Exception as e:
        # SECURITY: Fail closed for token revocation check
        # If we can't verify the token isn't revoked, we must reject it
        # This is a security-critical operation - better to block legitimate requests
        # than to allow revoked tokens to be used
        logger.error("Token revocation check failed: %s. Rejecting token for security.", e)
        return True


def _get_user_from_payload(payload: dict, source: str) -> User:
    """Helper to convert JWT payload to User object"""
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Try to get user from database (bypassing RLS)
    try:
        supabase_admin = get_supabase_admin_client()
        result = supabase_admin.table("users").select("*").eq("id", user_id).single().execute()
        if result.data:
            data = result.data
            return User(
                id=data["id"],
                email=data.get("email", ""),
                name=data.get("name", ""),
                picture=data.get("picture", ""),
                bio=data.get("bio"),
                created_at=data.get("created_at", ""),
            )
    except Exception:
        # Fallback to payload data if DB lookup fails
        logger.warning("Failed to fetch user from DB in middleware")

    # Common extraction for both sources
    iat = payload.get("iat")
    created_at = datetime.fromtimestamp(iat, timezone.utc) if isinstance(iat, (int, float)) else None

    # Construct User from payload
    if source == "supabase":
        user_metadata = payload.get("user_metadata", {})
        return User(
            id=user_id,
            email=payload.get("email", ""),
            name=user_metadata.get("name", user_metadata.get("full_name", "")),
            picture=user_metadata.get("avatar_url", user_metadata.get("picture", "")),
            bio=None,
            created_at=created_at,
        )
    else:  # custom
        return User(
            id=user_id,
            email=payload.get("email", ""),
            name=payload.get("name", ""),
            picture=payload.get("picture", ""),
            bio=payload.get("bio"),
            created_at=created_at,
        )


async def _verify_and_decode_token(token: str, supabase: Client | None = None) -> tuple[dict, str]:
    """Helper to verify and decode token, trying Supabase first then custom"""
    payload = None
    source = "unknown"

    try:
        # Try Supabase token first
        payload = await decode_supabase_token(token)
        source = "supabase"
    except (HTTPException, ValueError) as supabase_error:
        # Try custom token as fallback
        try:
            payload = decode_custom_token(token)
            source = "custom"
        except HTTPException as http_exc:
            logger.warning("Custom authentication check unsuccessful (Status Code: %d)", http_exc.status_code)
            raise
        except Exception:
            logger.debug("Custom authentication check unsuccessful")

            # FINAL FALLBACK: Try Supabase API directly if we have a client
            if supabase:
                try:
                    logger.debug("Attempting direct Supabase Auth verification...")
                    user_res = supabase.auth.get_user(token)
                    if user_res and user_res.user:
                        supabase_user = user_res.user
                        payload = {
                            "sub": supabase_user.id,
                            "user_id": supabase_user.id,
                            "email": supabase_user.email,
                            "user_metadata": supabase_user.user_metadata,
                            "app_metadata": supabase_user.app_metadata,
                            "iat": int(datetime.now(timezone.utc).timestamp()),
                        }
                        source = "supabase"
                        logger.info("Authentication verified via direct Supabase Auth API")
                        return payload, source
                except Exception as api_err:
                    logger.debug("Direct Supabase verification failed: %s", api_err)

            logger.warning("All authentication verification methods failed")
            raise HTTPException(status_code=401, detail="Authentication failed: Invalid or expired token")
    except Exception:
        logger.error("Unexpected authentication verification error")
        raise HTTPException(status_code=401, detail="Authentication failed")

    # Common Security Checks (Revocation & Invalidation)
    if payload:
        # 1. Check JTI Revocation (Blocklist)
        jti = payload.get("jti")
        if jti and await _is_token_revoked(jti):
            raise HTTPException(status_code=401, detail="Token revoked")

        # 2. Check Global User Invalidation (e.g. Password Reset)
        user_id = payload.get("sub") or payload.get("user_id")
        iat = payload.get("iat")
        if user_id and iat:
            try:
                token_service = await get_token_service()
                # Ensure iat is datetime
                issued_at = datetime.fromtimestamp(iat, timezone.utc)
                if await token_service.is_user_invalidated(user_id, issued_at):
                    raise HTTPException(status_code=401, detail="Session invalidated (Password changed)")
            except HTTPException:
                raise
            except Exception:
                # Log but verify open? checking service might fail
                # Ideally fail closed for high security
                logger.error("Failed to check user invalidation status")

    return payload, source


async def get_current_user_from_credentials(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client),
):
    """Get current authenticated user using Supabase Auth"""
    token = credentials.credentials
    payload, source = await _verify_and_decode_token(token, supabase)
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
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: Client = Depends(get_supabase_client),
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
    payload, _ = await _verify_and_decode_token(token, get_supabase_client())
    return payload
