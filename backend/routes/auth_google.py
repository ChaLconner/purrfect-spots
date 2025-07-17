"""
Google OAuth authentication routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Header
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

def get_auth_service():
    return AuthService(get_supabase_client())

@router.get("/google/login")
async def google_login_redirect():
    """
    Redirect to Google OAuth login page
    """
    try:
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google Client ID not configured"
            )
        
        # Default redirect URI (frontend callback)
        redirect_uri = "http://localhost:5173/auth/callback"
        
        # OAuth parameters (without PKCE for simple redirect)
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
        
        print(f"🔍 Redirecting to Google OAuth: {auth_url}")
        
        return RedirectResponse(url=auth_url, status_code=302)
        
    except Exception as e:
        print(f"🔥 Error redirecting to Google login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to redirect to Google login: {str(e)}"
        )

@router.post("/google", response_model=LoginResponse)
async def google_login(
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
        
        # Create access token
        access_token = auth_service.create_access_token(user.id)
        
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
    request: GoogleCodeExchangeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Exchange Google authorization code for tokens (Modern OAuth 2.0 flow)
    """
    try:
        login_response = await auth_service.exchange_google_code(
            code=request.code,
            code_verifier=request.code_verifier,
            redirect_uri=request.redirect_uri
        )
        
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
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code exchange failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        picture=current_user.get("picture"),
        bio=current_user.get("bio"),
        created_at=current_user["created_at"]
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
        
        # Use service role for direct DB access
        res = supabase.table("users").upsert(data, on_conflict="id").execute()
        
        if hasattr(res, 'data') and res.data:
            return {"message": "User synced", "data": res.data}
        else:
            return {"message": "User sync completed", "data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/logout")
async def logout():
    """
    Logout user (client-side token removal)
    """
    return {"message": "Logged out successfully"}
