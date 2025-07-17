"""
Google OAuth authentication routes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from services.auth_service import AuthService
from user_models.user import LoginResponse, UserResponse
from middleware.auth_middleware import get_current_user
from dependencies import get_supabase_client

router = APIRouter(prefix="/auth", tags=["Google Authentication"])

class GoogleTokenRequest(BaseModel):
    token: str

class GoogleCodeExchangeRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str

def get_auth_service():
    return AuthService(get_supabase_client())

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
        print("🔥 GOOGLE EXCHANGE ERROR (ValueError):", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print("🔥 GOOGLE EXCHANGE ERROR (Exception):", e)
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

@router.post("/logout")
async def logout():
    """
    Logout user (client-side token removal)
    """
    return {"message": "Logged out successfully"}
