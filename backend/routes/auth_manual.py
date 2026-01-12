from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from pydantic import BaseModel, EmailStr
import re
from services.auth_service import AuthService
from services.email_service import email_service
from dependencies import get_supabase_client
from middleware.auth_middleware import get_current_user
from user_models.user import UserResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import config

# Get limiter from main app state (or creating a new instance if needed, but better to share)
# In this architecture, usually better to import the shared limiter instance
from utils.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["Manual Authentication"])

class RegisterInput(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    # refresh_token removed from body for security

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

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

@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")
async def register(response: Response, request: Request, data: RegisterInput, auth_service: AuthService = Depends(get_auth_service)):
    """
    Register new user with email and password
    """
    try:
        # Basic validation
        # Enhanced validation
        if len(data.password) < 8:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 8 characters long"
            )
        
        if not re.search(r"\d", data.password):
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least one number"
            )

        if not data.name.strip():
            raise HTTPException(
                status_code=400,
                detail="Please enter first and last name"
            )
            
        # Check uniqueness via service (optimized)
        existing_user = auth_service.get_user_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=400, 
                detail="This email is already in use. Please use another email"
            )
        
        # Create user
        try:
            user = auth_service.create_user_with_password(data.email, data.password, data.name.strip())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        # 🎫 Generate tokens
        access_token = auth_service.create_access_token(user["id"])
        refresh_token = auth_service.create_refresh_token(user["id"])
        
        # Set HttpOnly cookie
        set_refresh_cookie(response, refresh_token)

        # 🛠 Map user -> UserResponse schema
        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            picture=user.get("picture"),
            bio=user.get("bio"),
            created_at=user["created_at"]
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Registration failed. Please try again"
        )

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(response: Response, request: Request, req: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Login with email and password
    """
    try:
        user = auth_service.authenticate_user(req.email, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        
        access_token = auth_service.create_access_token(user["id"])
        refresh_token = auth_service.create_refresh_token(user["id"])
        
        # Set HttpOnly cookie
        set_refresh_cookie(response, refresh_token)
        
        # 🛠 Map user -> UserResponse schema
        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            picture=user.get("picture"),
            bio=user.get("bio"),
            created_at=user["created_at"]
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )

@router.post("/refresh-token")
async def refresh_token(response: Response, request: Request, auth_service: AuthService = Depends(get_auth_service)):
    """
    Refresh access token using long-lived refresh token from HttpOnly cookie
    """
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    user_id = auth_service.verify_refresh_token(refresh_token)
    if not user_id:
        # Clear invalid cookie
        response.delete_cookie("refresh_token")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    new_access_token = auth_service.create_access_token(user_id)
    
    # Optionally rotate refresh token here
    # new_refresh_token = auth_service.create_refresh_token(user_id)
    # set_refresh_cookie(response, new_refresh_token)
    
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(response: Response):
    """
    Logout user (clear refresh token cookie)
    """
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, req: ForgotPasswordRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Request password reset (generates token)
    """
    try:
        token = auth_service.create_password_reset_token(req.email)
        
        # Send email if token exists (email is registered)
        if token:
            # This sends real email if SMTP configured, or logs to console if not
            email_service.send_reset_email(req.email, token)
        
        # Always return success to prevent account enumeration
        return {"message": "If this email is registered, you will receive password reset instructions."}
    except Exception as e:
        # Log error but return generic success message
        print(f"Forgot password error: {e}")
        return {"message": "If this email is registered, you will receive password reset instructions."}

@router.post("/reset-password")
@limiter.limit("3/minute")
async def reset_password(request: Request, req: ResetPasswordRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Reset password using token
    """
    success = auth_service.reset_password(req.token, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    return {"message": "Password updated successfully"}


@router.get("/me")
async def get_user(current_user = Depends(get_current_user)):
    """
    Get current user information (simple version)
    """
    return current_user
