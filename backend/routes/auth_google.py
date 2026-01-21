"""
Google OAuth authentication routes
"""

import os
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from config import config
from dependencies import get_supabase_client
from logger import logger
from middleware.auth_middleware import get_current_user, get_current_user_from_header
from services.auth_service import AuthService
from user_models.user import LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Google Authentication"])


class GoogleTokenRequest(BaseModel):
    token: str


class GoogleCodeExchangeRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str


def get_auth_service():
    return AuthService(get_supabase_client())


def get_client_info(request: Request):
    """Helper to get IP and User-Agent safely"""
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")

    # Check X-Forwarded-For if behind proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()

    return ip, user_agent


def set_refresh_cookie(response: Response, refresh_token: str):
    """Helper to set secure refresh token cookie"""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=config.is_production(),
        samesite="lax",
        max_age=config.JWT_REFRESH_EXPIRATION_DAYS * 24 * 60 * 60,
    )


@router.get("/google/login")
async def google_login_redirect():
    """Redirect to Google OAuth login page with PKCE support"""
    try:
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Client ID not configured",
            )

        allowed_origins = config.get_allowed_origins()

        # Priority: localhost:5173 -> First allowed origin -> fallback
        origin = "http://localhost:5173"
        if allowed_origins:
            origin = allowed_origins[0]
            for cors_origin in allowed_origins:
                if "localhost:5173" in cors_origin:
                    origin = cors_origin
                    break

        redirect_uri = f"{origin}/auth/callback"

        oauth_params = {
            "client_id": google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }

        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(oauth_params)}"
        return RedirectResponse(url=auth_url, status_code=302)

    except Exception as e:
        logger.error(f"Failed to redirect to Google login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to redirect to Google login: {e!s}",
        )


@router.post("/google", response_model=LoginResponse)
async def google_login(
    response: Response,
    request: Request,
    token_data: GoogleTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login with Google OAuth token"""
    try:
        user_data = auth_service.verify_google_token(token_data.token)
        user = auth_service.create_or_get_user(user_data)

        ip, ua = get_client_info(request)
        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id, ip, ua)

        set_refresh_cookie(response, refresh_token)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
                bio=user.bio,
                created_at=user.created_at,
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Google Login failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


@router.post("/google/exchange", response_model=LoginResponse)
async def google_exchange_code(
    response: Response,
    request: Request,
    exchange_data: GoogleCodeExchangeRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Exchange Google authorization code for tokens (PKCE OAuth 2.0 flow)"""
    try:
        if not exchange_data.code:
            raise ValueError("Authorization code is required")
        if not exchange_data.code_verifier:
            raise ValueError("Code verifier is required")
        if not exchange_data.redirect_uri:
            raise ValueError("Redirect URI is required")

        # Validate redirect URI against allowed origins
        allowed_origins = config.get_allowed_origins()
        redirect_origin = None

        logger.debug(f"Auth Exchange Debug: Received redirect_uri={exchange_data.redirect_uri}")

        # Check if the redirect URI matches any allowed origin + /auth/callback
        expected_redirects = []
        for origin in allowed_origins:
            expected = f"{origin.rstrip('/')}/auth/callback"
            expected_redirects.append(expected)
            if exchange_data.redirect_uri == expected:
                redirect_origin = origin
                break

        # Fallback for production domains not in CORS
        if not redirect_origin and exchange_data.redirect_uri.endswith("/auth/callback"):
            uri_parts = exchange_data.redirect_uri.split("/")
            if len(uri_parts) >= 3:
                origin = "/".join(uri_parts[:3])
                allowed_production_domains = [
                    "http://localhost:5173",
                    "https://localhost:5173",
                    "https://purrfect-spots.vercel.app",
                ]
                if origin in allowed_production_domains:
                    redirect_origin = origin
                    logger.debug(f"Auth Exchange Debug: Matched production domain={origin}")

        if not redirect_origin:
            logger.warning(f"Invalid redirect URI: {exchange_data.redirect_uri}. Expected: {expected_redirects}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect URI",
            )

        ip, ua = get_client_info(request)
        login_response = await auth_service.exchange_google_code(
            code=exchange_data.code,
            code_verifier=exchange_data.code_verifier,
            redirect_uri=exchange_data.redirect_uri,
            ip=ip,
            user_agent=ua,
        )

        if login_response.refresh_token:
            set_refresh_cookie(response, login_response.refresh_token)

        return LoginResponse(
            access_token=login_response.access_token,
            token_type=login_response.token_type,
            user=UserResponse(
                id=login_response.user.id,
                email=login_response.user.email,
                name=login_response.user.name,
                picture=login_response.user.picture,
                bio=login_response.user.bio,
                created_at=login_response.user.created_at,
            ),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Google Exchange failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code exchange failed",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        bio=current_user.bio,
        created_at=current_user.created_at,
    )


@router.post("/sync-user")
async def sync_user_data(user=Depends(get_current_user_from_header), supabase=Depends(get_supabase_client)):
    """Insert/Upsert user into Supabase Table from JWT payload (Supabase Auth compatible)"""
    try:
        from dependencies import get_supabase_admin_client

        supabase_admin = get_supabase_admin_client()

        user_id = user["sub"]
        email = user.get("email")
        user_metadata = user.get("user_metadata", {})
        app_metadata = user.get("app_metadata", {})

        name = user_metadata.get("name") or user_metadata.get("full_name") or user.get("name", "")
        picture = user_metadata.get("avatar_url") or user_metadata.get("picture") or user.get("picture", "")

        google_id = None
        provider = app_metadata.get("provider", "")
        if provider == "google":
            google_id = user_metadata.get("provider_id")
        elif user.get("google_id"):
            google_id = user.get("google_id")

        data = {
            "id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "google_id": google_id,
        }

        res = supabase_admin.table("users").upsert(data, on_conflict="id").execute()
        return {"message": "User synced", "data": res.data if hasattr(res, "data") else data}

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {e!s}")
