"""
Authentication routes for Google OAuth
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from supabase import Client
from ..services.auth_service import AuthService
from ..models.user import LoginResponse, UserResponse
from ..middleware.auth_middleware import get_current_user
from ..models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    token: str


def get_auth_service(supabase: Client = Depends()) -> AuthService:
    """Dependency to get AuthService instance"""
    return AuthService(supabase)


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


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout():
    """
    Logout user (client-side token removal)
    """
    return {"message": "Logged out successfully"}
