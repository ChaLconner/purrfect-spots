from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field

from config import config
from dependencies import get_supabase_client
from logger import logger
from middleware.auth_middleware import get_current_user
from services.auth_service import AuthService
from services.email_service import email_service
from user_models.user import UserResponse
from utils.rate_limiter import limiter


def get_client_info(request: Request):
    """Helper to get IP and User-Agent safely"""
    ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    # Check X-Forwarded-For if behind proxy
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
        
    return ip, user_agent


router = APIRouter(prefix="/auth", tags=["Manual Authentication"])


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: str = Field(..., min_length=1, description="Please enter first and last name")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


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
        secure=config.is_production(),
        samesite="lax",
        max_age=config.JWT_REFRESH_EXPIRATION_DAYS * 24 * 60 * 60,
    )


@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")
async def register(
    response: Response,
    request: Request,
    data: RegisterInput,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register new user with email and password"""
    try:
        if not data.name.strip():
             raise HTTPException(status_code=400, detail="Please enter first and last name")

        existing_user = auth_service.get_user_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="This email is already in use. Please use another email",
            )

        try:
            user = auth_service.create_user_with_password(
                data.email, data.password, data.name.strip()
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        ip, ua = get_client_info(request)
        access_token = auth_service.create_access_token(user["id"])
        refresh_token = auth_service.create_refresh_token(user["id"], ip, ua)

        set_refresh_cookie(response, refresh_token)

        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            picture=user.get("picture"),
            bio=user.get("bio"),
            created_at=user["created_at"],
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=500, detail="Registration failed. Please try again"
        )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    response: Response,
    request: Request,
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login with email and password"""
    try:
        user = auth_service.authenticate_user(req.email, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        ip, ua = get_client_info(request)
        access_token = auth_service.create_access_token(user["id"])
        refresh_token = auth_service.create_refresh_token(user["id"], ip, ua)

        set_refresh_cookie(response, refresh_token)

        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            picture=user.get("picture"),
            bio=user.get("bio"),
            created_at=user["created_at"],
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh-token")
async def refresh_token(
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using long-lived refresh token from HttpOnly cookie"""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    ip, ua = get_client_info(request)
    payload = await auth_service.verify_refresh_token(refresh_token, ip, ua)
    
    if not payload:
        response.delete_cookie("refresh_token")
        raise HTTPException(status_code=401, detail="Invalid, expired, or revoked refresh token")

    user_id = payload["user_id"]
    
    # Rotate token means we should revoke the OLD one to prevent reuse!
    old_jti = payload.get("jti")
    old_exp = payload.get("exp")
    if old_jti and old_exp:
        await auth_service.revoke_token(old_jti, user_id, datetime.fromtimestamp(old_exp, timezone.utc))

    new_access_token = auth_service.create_access_token(user_id)
    new_refresh_token = auth_service.create_refresh_token(user_id, ip, ua)

    set_refresh_cookie(response, new_refresh_token)

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user (clear refresh token cookie and revoke it)"""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            # We don't check IP/UA here because we want to allow logout even if IP changed
            payload = await auth_service.verify_refresh_token(refresh_token)
            if payload:
                 jti = payload.get("jti")
                 user_id = payload.get("user_id")
                 exp = payload.get("exp")
                 if jti and user_id and exp:
                     await auth_service.revoke_token(jti, user_id, datetime.fromtimestamp(exp, timezone.utc))
        except Exception as e:
            logger.warning(f"Logout cleanup failed (ignore): {e}")

    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    req: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Request password reset (generates token)"""
    try:
        token = auth_service.create_password_reset_token(req.email)
        if token:
            email_service.send_reset_email(req.email, token)

        return {
            "message": "If this email is registered, you will receive password reset instructions."
        }
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return {
            "message": "If this email is registered, you will receive password reset instructions."
        }


@router.post("/reset-password")
@limiter.limit("3/minute")
async def reset_password(
    request: Request,
    req: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Reset password using token"""
    success = auth_service.reset_password(req.token, req.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    return {"message": "Password updated successfully"}


@router.get("/me")
async def get_user(current_user=Depends(get_current_user)):
    """Get current user information"""
    return current_user
