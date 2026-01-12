"""
Google OAuth authentication routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Header, Response, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from services.auth_service import AuthService
from user_models.user import LoginResponse, UserResponse
from middleware.auth_middleware import get_current_user, get_current_user_from_header
from dependencies import get_supabase_client
import os
from urllib.parse import urlencode

router = APIRouter(prefix="/auth", tags=["Google Authentication"])

class GoogleTokenRequest(BaseModel):
    token: str

class GoogleCodeExchangeRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str

from config import config

def get_auth_service():
    return AuthService(get_supabase_client())

def set_refresh_cookie(response: Response, refresh_token: str):
    """Helper to set secure refresh token cookie"""
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=config.is_production(),  # Secure only in production (HTTPS)
        samesite="lax",
        max_age=config.JWT_REFRESH_EXPIRATION_DAYS * 24 * 60 * 60
    )

@router.get("/google/login")
async def google_login_redirect():
    """
    Redirect to Google OAuth login page with PKCE support
    """
    try:
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Client ID not configured"
            )
        
        # Get the allowed origins from CORS configuration
        allowed_origins = config.get_allowed_origins()
             
        # Determine the origin to use for the redirect URI
        # Priority: 
        # 1. First origin containing "localhost:5173" (for dev convenience)
        # 2. First origin in the list
        origin = allowed_origins[0] if allowed_origins else "http://localhost:5173"
        for cors_origin in allowed_origins:
            if "localhost:5173" in cors_origin:
                origin = cors_origin
                break
                
        redirect_uri = f"{origin}/auth/callback"
        
        # OAuth parameters without PKCE (frontend will handle PKCE)
        oauth_params = {
            'client_id': google_client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid email profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        # Create authorization URL
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(oauth_params)}"
        
        return RedirectResponse(url=auth_url, status_code=302)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to redirect to Google login: {str(e)}"
        )

@router.post("/google", response_model=LoginResponse)
async def google_login(
    response: Response,
    request: GoogleTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with Google OAuth token
    """
    try:
        # Verify Google token
        user_data = auth_service.verify_google_token(request.token)
        
        # Create or get user from database
        user = auth_service.create_or_get_user(user_data)
        
        # Create tokens
        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)
        
        # Set HttpOnly cookie
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
                created_at=user.created_at
            )
            # refresh_token=refresh_token # Removed for security
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/google/exchange", response_model=LoginResponse)
async def google_exchange_code(
    response: Response,
    request: GoogleCodeExchangeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Exchange Google authorization code for tokens (PKCE OAuth 2.0 flow)
    """
    try:
        # Validate request parameters
        if not request.code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )
        
        if not request.code_verifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code verifier is required for PKCE flow"
            )
        
        if not request.redirect_uri:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Redirect URI is required"
            )
        
        # Validate redirect URI against allowed origins
        # Validate redirect URI against allowed origins
        allowed_origins = config.get_allowed_origins()
        redirect_origin = None
        
        # Debug logging
        print(f"Auth Exchange Debug: Received redirect_uri={request.redirect_uri}")
        print(f"Auth Exchange Debug: Allowed origins={allowed_origins}")
        
        # Check if the redirect URI matches any allowed origin + /auth/callback
        expected_redirects = []
        for origin in allowed_origins:
            expected = f"{origin.rstrip('/')}/auth/callback"
            expected_redirects.append(expected)
            if request.redirect_uri == expected:
                redirect_origin = origin
                break
        
        # Also check for production domains that might not be in CORS_ORIGINS
        if not redirect_origin and request.redirect_uri.endswith("/auth/callback"):
            # Extract origin from redirect_uri
            uri_parts = request.redirect_uri.split("/")
            if len(uri_parts) >= 3:
                origin = "/".join(uri_parts[:3])  # https://domain.com or http://localhost:5173
                # Allow only specific domains
                allowed_production_domains = [
                    "http://localhost:5173",
                    "https://localhost:5173",
                    "https://purrfect-spots.vercel.app"
                ]
                if origin in allowed_production_domains:
                    redirect_origin = origin
                    print(f"Auth Exchange Debug: Matched production domain={origin}")
        
        if not redirect_origin:
            print(f"Auth Exchange Debug: No match found. Expected one of: {expected_redirects}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid redirect URI: {request.redirect_uri}. Expected one of: {', '.join(expected_redirects)}"
            )
        
        login_response = await auth_service.exchange_google_code(
            code=request.code,
            code_verifier=request.code_verifier,
            redirect_uri=request.redirect_uri
        )
        
        # Extract refresh token and set cookie
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
                created_at=login_response.user.created_at
            )
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code exchange failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        bio=current_user.bio,
        created_at=current_user.created_at
    )

@router.post("/sync-user")
async def sync_user_data(
    user = Depends(get_current_user_from_header),
    supabase = Depends(get_supabase_client)
):
    """
    Insert/Upsert user into Supabase Table from JWT payload (Supabase Auth compatible)
    """
    try:
        # Import admin client for user sync operations
        from dependencies import get_supabase_admin_client
        supabase_admin = get_supabase_admin_client()
        
        # Extract user data from Supabase JWT payload
        user_id = user["sub"]
        email = user.get("email")
        
        # Handle both Supabase and custom token formats
        user_metadata = user.get("user_metadata", {})
        app_metadata = user.get("app_metadata", {})
        
        # Get name and picture from user_metadata (Supabase standard)
        name = user_metadata.get("name") or user_metadata.get("full_name") or user.get("name", "")
        picture = user_metadata.get("avatar_url") or user_metadata.get("picture") or user.get("picture", "")
        
        # Get Google provider ID if available
        google_id = None
        provider = app_metadata.get("provider", "")
        if provider == "google":
            google_id = user_metadata.get("provider_id")
        elif user.get("google_id"):  # Fallback for custom tokens
            google_id = user.get("google_id")

        # Upsert user data
        data = {
            "id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "google_id": google_id,
        }
        
        # Use admin client for direct DB access (bypasses RLS)
        res = supabase_admin.table("users").upsert(data, on_conflict="id").execute()
        
        if hasattr(res, 'data') and res.data:
            return {"message": "User synced", "data": res.data}
        else:
            return {"message": "User sync completed", "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/logout")
async def logout(response: Response):
    """
    Logout user (client-side token removal + clear cookie)
    """
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}
