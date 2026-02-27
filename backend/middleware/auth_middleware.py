"""
Authentication middleware for protecting routes with Supabase Auth
"""

import time
from datetime import UTC, datetime

import httpx
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import AClient

from config import config
from logger import logger
from services.token_service import get_token_service
from user_models.user import User
from utils.auth_utils import decode_token
from utils.supabase_client import (
    get_async_supabase_client,
)

security = HTTPBearer(auto_error=False)

# JWKS Cache
_jwks_cache: dict | None = None
_jwks_last_update: int = 0
JWKS_CACHE_TTL = 3600  # 1 hour


async def get_jwks() -> dict | None:
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


async def decode_supabase_token(token: str) -> dict:
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
        return jwt.decode(token, public_key, algorithms=["RS256"], audience="authenticated")  # type: ignore[arg-type]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Supabase token: {e!s}")


# decode_custom_token removed - replaced by utils.auth_utils.decode_token in _attempt_token_decoding


async def _is_token_revoked(jti: str) -> bool:
    """Check if token JTI is in blacklist using TokenService"""
    if not jti:
        return False

    try:
        token_service = await get_token_service()
        return await token_service.is_blacklisted(jti=jti)
    except Exception:
        # SECURITY: Fail closed for token revocation check
        # If we can't verify the token isn't revoked, we must reject it
        # This is a security-critical operation - better to block legitimate requests
        # than to allow revoked tokens to be used
        logger.error("Revocation status check failed. Denying request for security.")
        return True


async def _get_user_from_payload(payload: dict, source: str) -> User:
    """Helper to convert JWT payload to User object"""
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Try to get user from database (bypassing RLS)
    try:
        from utils.supabase_client import get_async_supabase_admin_client

        supabase_admin = await get_async_supabase_admin_client()
        # Fetch user with role and permissions
        query = "*, roles(name, role_permissions(permissions(code)))"
        result = await supabase_admin.table("users").select(query).eq("id", user_id).maybe_single().execute()

        if result and hasattr(result, "data") and result.data:
            data = result.data

            # Extract permissions from nested structure
            permissions = []
            role_name = data.get("role", "user")  # Default to legacy column

            role_data = data.get("roles")
            if role_data and isinstance(role_data, dict):
                if role_data.get("name"):
                    role_name = role_data.get("name")

                rps = role_data.get("role_permissions", [])
                for rp in rps:
                    perm = rp.get("permissions")
                    if perm and "code" in perm:
                        permissions.append(perm["code"])

            return User(
                id=data["id"],
                username=data.get("username"),
                email=data.get("email", ""),
                name=data.get("name"),
                picture=data.get("picture"),
                bio=data.get("bio"),
                is_pro=data.get("is_pro", False),
                stripe_customer_id=data.get("stripe_customer_id"),
                subscription_end_date=data.get("subscription_end_date"),
                cancel_at_period_end=data.get("cancel_at_period_end", False),
                treat_balance=data.get("treat_balance", 0),
                role=role_name,
                role_id=data.get("role_id"),
                permissions=permissions,
                created_at=data.get("created_at"),
                google_id=data.get("google_id"),
            )
    except Exception as e:
        # Fallback to payload data if DB lookup fails
        import traceback

        logger.error(f"Failed to fetch user from DB in middleware: {e}\nTraceback: {traceback.format_exc()}")
        logger.warning(f"Failed to fetch user from DB in middleware: {e}")

    # Common extraction for both sources
    iat = payload.get("iat")
    created_at = datetime.fromtimestamp(iat, UTC) if isinstance(iat, (int, float)) else None

    # Extract permissions from payload if available
    permissions = payload.get("permissions", [])

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
            google_id=user_metadata.get("provider_id")
            if payload.get("app_metadata", {}).get("provider") == "google"
            else None,
            permissions=permissions,
        )
    # custom
    return User(
        id=user_id,
        email=payload.get("email", ""),
        name=payload.get("name", ""),
        picture=payload.get("picture", ""),
        bio=payload.get("bio"),
        created_at=created_at,
        google_id=payload.get("google_id"),
        permissions=permissions,
        role=payload.get("role", "user"),
    )


from collections.abc import Awaitable, Callable


def require_permission(permission_code: str) -> Callable[[User], Awaitable[User]]:
    """Dependency factory to check for specific permission"""

    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        # 1. Direct permission check
        if permission_code in user.permissions:
            return user

        # 2. General admin permission or role check
        if "admin_access" in user.permissions or user.role.lower() in ("admin", "super_admin"):
            return user

        raise HTTPException(status_code=403, detail=f"Insufficient permissions. Required: {permission_code}")

    return permission_checker


async def _verify_via_supabase_api(token: str, supabase: AClient) -> dict | None:
    """Attempt direct verification via Supabase Auth API"""
    try:
        logger.debug("Attempting direct Supabase Auth verification...")
        user_res = await supabase.auth.get_user(token)
        if user_res and user_res.user:
            supabase_user = user_res.user
            logger.info("Authentication verified via direct Supabase Auth API")
            return {
                "sub": supabase_user.id,
                "user_id": supabase_user.id,
                "email": supabase_user.email,
                "user_metadata": supabase_user.user_metadata,
                "app_metadata": supabase_user.app_metadata,
                "iat": int(datetime.now(UTC).timestamp()),
            }
    except Exception as api_err:
        logger.debug("Direct Supabase verification failed: %s", api_err)
    return None


async def _attempt_token_decoding(token: str, supabase: AClient | None) -> tuple[dict, str]:
    """Try multiple strategies to key decode the token"""
    if not token:
        logger.warning("Authentication failed: No token provided in credentials")
        raise HTTPException(status_code=401, detail="Authentication failed: No token provided")

    # 1. Try Supabase JWT (Standard)
    try:
        payload = await decode_supabase_token(token)
        logger.info("Token decoded successfully using Supabase JWKS")
        return payload, "supabase"
    except (HTTPException, ValueError):
        logger.debug("Supabase token decoding attempted but failed")

    # 2. Try Standard JWT Decoding (Supabase Key or Custom Secret)
    try:
        # decode_token handles both config.SUPABASE_KEY and config.JWT_SECRET
        payload = decode_token(token)
        logger.info("Token decoded successfully using verify_token utility")

        # Determine source - if it has app_metadata it's likely Supabase
        source = "supabase" if "app_metadata" in payload else "custom"
        return payload, source
    except ValueError:
        logger.debug("Standard token verification failed")
    except Exception:
        logger.debug("Unexpected error during standard token verification")

    # 3. Try Direct API (Final Fallback)
    if supabase:
        api_payload = await _verify_via_supabase_api(token, supabase)
        if api_payload:
            logger.info("Token verified via direct Supabase Auth API")
            return api_payload, "supabase"

    logger.warning("All authentication verification methods failed for the provided token")
    raise HTTPException(status_code=401, detail="Authentication failed: Invalid or expired token")


async def _validate_token_security(payload: dict) -> None:
    """Run security checks on decoded token payload"""
    # 1. Check JTI Revocation (Blocklist)
    jti = payload.get("jti")
    if jti and await _is_token_revoked(jti):
        raise HTTPException(status_code=401, detail="Token revoked")

    # 2. Check Global User Invalidation
    user_id = payload.get("sub") or payload.get("user_id")
    iat = payload.get("iat")

    if user_id and iat:
        try:
            token_service = await get_token_service()
            issued_at = datetime.fromtimestamp(iat, UTC)
            if await token_service.is_user_invalidated(user_id, issued_at):
                raise HTTPException(status_code=401, detail="Session invalidated (Password changed)")
        except HTTPException:
            raise
        except Exception:
            logger.error("Failed to check user invalidation status")


async def _verify_and_decode_token(token: str, supabase: AClient | None = None) -> tuple[dict, str]:
    """Helper to verify and decode token, trying Supabase first then custom"""
    try:
        payload, source = await _attempt_token_decoding(token, supabase)

        if payload:
            await _validate_token_security(payload)

        return payload, source
    except HTTPException:
        raise
    except Exception:
        logger.error("Unexpected authentication verification error")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_current_user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: AClient = Depends(get_async_supabase_client),
) -> User:
    """Get current authenticated user using Supabase Auth"""
    if not credentials:
        logger.warning("Missing Authorization header in request (credentials is None)")
        raise HTTPException(status_code=401, detail="Authentication failed: No token provided")

    token = credentials.credentials
    if not token:
        logger.warning("Bearer token is empty in Authorization header")
        raise HTTPException(status_code=401, detail="Authentication failed: Empty token")

    payload, source = await _verify_and_decode_token(token, supabase)
    return await _get_user_from_payload(payload, source)


async def get_current_user(request: Request) -> User:
    """Get current user from request headers using JWT token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ")[1]
    payload, source = await _verify_and_decode_token(token)
    return await _get_user_from_payload(payload, source)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: AClient = Depends(get_async_supabase_client),
) -> User | None:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    try:
        return await get_current_user_from_credentials(credentials, supabase)
    except HTTPException:
        return None


async def get_current_user_from_header(request: Request) -> dict:
    """Get decoded token payload from request headers"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ")[1]
    supabase = await get_async_supabase_client()
    payload, _ = await _verify_and_decode_token(token, supabase)
    return payload
