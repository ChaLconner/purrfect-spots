"""
Authentication middleware for protecting routes with Supabase Auth
"""

import time
from datetime import UTC, datetime
from typing import Any, cast

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import config, normalize_single_line_env
from constants.admin_permissions import has_admin_access, normalize_permission_code, normalize_permissions
from logger import logger
from schemas.user import User
from services.token_service import get_token_service
from services.user.base_mixin import UserBaseMixin
from supabase import AClient
from utils.auth_utils import decode_token
from utils.security_alerts import (
    track_failed_permission_check,
    track_suspicious_user_agent,
)
from utils.supabase_client import (
    get_async_supabase_client,
)

security = HTTPBearer(auto_error=False)
USER_AUTH_CACHE_TTL = 300

# JWKS Cache
_jwks_cache: dict | None = None
_jwks_last_update: int = 0
JWKS_CACHE_TTL = 3600  # 1 hour


def get_user_auth_cache_key(user_id: str) -> str:
    """Build the Redis cache key used for authenticated user snapshots."""
    return f"user_auth_cache:{user_id}"


async def invalidate_user_auth_cache(user_id: str) -> None:
    """Invalidate the cached auth snapshot for a user."""
    from services.redis_service import redis_service

    await redis_service.delete(get_user_auth_cache_key(user_id))


def _assert_user_not_banned(user: User) -> User:
    """Reject requests for users whose account has been suspended."""
    if user.banned_at:
        raise HTTPException(status_code=403, detail="Account suspended")
    return user


async def get_jwks() -> dict | None:
    """Lazily fetch and cache JWKS"""
    global _jwks_cache, _jwks_last_update

    supabase_url = normalize_single_line_env(config.SUPABASE_URL)
    if not supabase_url:
        return None

    base_url = supabase_url.rstrip("/")
    jwks_urls = (
        f"{base_url}/auth/v1/.well-known/jwks.json",
        f"{base_url}/auth/v1/keys",
    )

    current_time = time.time()
    if _jwks_cache and (current_time - _jwks_last_update < JWKS_CACHE_TTL):
        return _jwks_cache

    from utils.http_client import get_shared_httpx_client

    try:
        client = get_shared_httpx_client()
        # Some Supabase deployments still expect the anon key on JWKS requests.
        apikey = normalize_single_line_env(config.SUPABASE_KEY)
        headers = {"apikey": apikey} if apikey else {}
        last_response = None
        for jwks_url in jwks_urls:
            response = await client.get(jwks_url, headers=headers, timeout=5)
            last_response = response
            if response.status_code == 200:
                _jwks_cache = response.json()
                _jwks_last_update = int(current_time)
                return _jwks_cache
        if last_response is not None:
            logger.warning(
                "JWKS fetch failed for %s with status %d: %s",
                jwks_urls[-1],
                last_response.status_code,
                last_response.text[:100],
            )
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
        return jwt.decode(token, cast(Any, public_key), algorithms=["RS256"], audience="authenticated")
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

    # Try Redis Cache first
    from services.redis_service import redis_service

    cache_key = get_user_auth_cache_key(user_id)
    cached_data = await redis_service.get(cache_key)
    if cached_data:
        cached_user = User(**cached_data)
        cached_user.permissions = normalize_permissions(cached_user.permissions)
        return _assert_user_not_banned(cached_user)

    # Try to get user from database (bypassing RLS)
    try:
        from utils.supabase_client import get_async_supabase_admin_client

        supabase_admin = await get_async_supabase_admin_client()
        # Fetch user with role and permissions
        query = "*, roles(name, role_permissions(permissions(code)))"
        result = await supabase_admin.table("users").select(query).eq("id", user_id).maybe_single().execute()

        if result is not None and hasattr(result, "error") and result.error:
            logger.error(f"Supabase auth query error for user {user_id}: {result.error}")
            # If we get a permission denied here, it means supabase_admin isn't actually an admin
            if "permission denied" in str(result.error).lower():
                logger.warning("Supabase admin client received permission denied - check service role key")
            raise HTTPException(status_code=401, detail="User database sync failure")

        if result and hasattr(result, "data") and result.data:
            data = cast(dict[str, Any], result.data)

            # Extract permissions from nested structure
            permissions_set = set()
            role_name = cast(str, data.get("role", "user"))  # Default to legacy column

            role_data = data.get("roles")
            role_dict = UserBaseMixin._extract_role_dict(role_data)
            if role_dict:
                if role_dict.get("name"):
                    role_name = cast(str, role_dict.get("name"))

                rps = cast(list[dict[str, Any]], role_dict.get("role_permissions", []))
                for rp in rps:
                    perm = cast(dict[str, Any], rp.get("permissions"))
                    if perm and isinstance(perm, dict) and "code" in perm:
                        permission_code = normalize_permission_code(cast(str, perm["code"]))
                        if permission_code:
                            permissions_set.add(permission_code)

            from utils.datetime_utils import from_iso as parse_iso8601

            user_obj = User(
                id=cast(str, data["id"]),
                username=cast(str, data.get("username")),
                email=cast(str, data.get("email", "")),
                name=cast(str, data.get("name")),
                picture=cast(str, data.get("picture")),
                bio=cast(str, data.get("bio")),
                is_pro=cast(bool, data.get("is_pro", False)),
                stripe_customer_id=cast(str, data.get("stripe_customer_id")),
                subscription_end_date=parse_iso8601(cast(str, data.get("subscription_end_date")))
                if data.get("subscription_end_date")
                else None,
                cancel_at_period_end=cast(bool, data.get("cancel_at_period_end", False)),
                treat_balance=cast(int, data.get("treat_balance", 0)),
                role=role_name,
                role_id=cast(str, data.get("role_id")),
                permissions=list(permissions_set),
                created_at=parse_iso8601(cast(str, data.get("created_at"))) if data.get("created_at") else None,
                google_id=cast(str, data.get("google_id")),
                banned_at=parse_iso8601(cast(str, data.get("banned_at"))) if data.get("banned_at") else None,
            )

            # Save to Redis
            await redis_service.set(cache_key, user_obj.model_dump(), expire=USER_AUTH_CACHE_TTL)

            return _assert_user_not_banned(user_obj)

        logger.warning(f"User {user_id} not found or permission denied in auth query")
        raise HTTPException(status_code=401, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        # SECURITY: Remove permissive fallback during DB lookup failure.
        # If the database is unreachable, we cannot verify the user's current
        # ban status, roles, or permissions safely. Relying on JWT payload
        # data alone is risky if permissions were revoked after token issuance.
        from logger import sanitize_log_value

        logger.error(
            "Critical: Database lookup failed for user %s in auth middleware: %s", sanitize_log_value(user_id), e
        )
        # Fail with 503 (Service Unavailable) to indicate temporary DB issue
        raise HTTPException(
            status_code=503, detail="Authentication service temporarily unavailable. Please try again later."
        )


def require_permission(permission_code: str) -> Any:
    """Dependency factory to check for specific permission"""
    required_permission = normalize_permission_code(permission_code) or permission_code

    async def permission_checker(request: Request, user: User = Depends(get_current_user)) -> User:
        user_permissions = set(normalize_permissions(user.permissions))

        # 1. Direct permission check
        if required_permission in user_permissions:
            return user

        # 2. General admin permission or role check
        if has_admin_access(user.role, user_permissions):
            return user

        # SECURITY: Track failed permission checks for alerting
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        track_failed_permission_check(
            user_id=user.id,
            required_permission=required_permission,
            ip_address=ip_address,
            endpoint=str(request.url.path),
        )

        # Track suspicious user agents
        track_suspicious_user_agent(user_agent, ip_address)

        raise HTTPException(status_code=403, detail=f"Insufficient permissions. Required: {required_permission}")

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
        logger.debug("Token decoded successfully using Supabase JWKS")
        return payload, "supabase"
    except (HTTPException, ValueError):
        logger.debug("Supabase token decoding attempted but failed")

    # 2. Try Standard JWT Decoding (Supabase Key or Custom Secret)
    try:
        # decode_token handles both config.SUPABASE_KEY and config.JWT_SECRET
        payload = decode_token(token)
        logger.debug("Token decoded successfully using verify_token utility")

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
        except Exception as exc:
            logger.error("User invalidation check failed. Denying request for security: %s", exc)
            raise HTTPException(
                status_code=503,
                detail="Authentication service temporarily unavailable. Please try again later.",
            )


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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: AClient = Depends(get_async_supabase_client),
) -> User:
    """Get current authenticated user using Supabase Auth or JWT token."""
    if not credentials:
        logger.warning("Missing Authorization header in request")
        raise HTTPException(status_code=401, detail="Authentication failed: No token provided")

    token = credentials.credentials
    if not token:
        logger.warning("Bearer token is empty in Authorization header")
        raise HTTPException(status_code=401, detail="Authentication failed: Empty token")

    payload, source = await _verify_and_decode_token(token, supabase)
    return await _get_user_from_payload(payload, source)


# Alias for backward compatibility and to support widespread use in routes
get_current_user_from_credentials = get_current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    supabase: AClient = Depends(get_async_supabase_client),
) -> User | None:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None


async def get_current_user_from_header(request: Request) -> dict:
    """Get decoded token payload from request headers (legacy/low-level)."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ")[1]
    supabase = await get_async_supabase_client()
    payload, _ = await _verify_and_decode_token(token, supabase)
    return payload
