"""
Authentication routes for both Manual (Email/Password) and Google OAuth
"""

import os
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from config import config
from dependencies import get_supabase_admin_client, get_supabase_client
from limiter import auth_limiter as limiter
from logger import logger
from middleware.auth_middleware import get_current_user, get_current_user_from_header
from schemas.auth import (
    ForgotPasswordRequest,
    GoogleCodeExchangeRequest,
    GoogleTokenRequest,
    LoginRequest,
    LoginResponse,
    RegisterInput,
    ResendOTPRequest,
    ResetPasswordRequest,
    SessionExchangeRequest,
    VerifyOTPRequest,
)
from services.auth_service import AuthService
from services.email_service import email_service
from services.otp_service import get_otp_service
from user_models.user import UserResponse
from utils.auth_response_utils import create_login_response
from utils.auth_utils import get_client_info, set_refresh_cookie
from utils.security import log_security_event, sanitize_text

router = APIRouter(prefix="/auth", tags=["Authentication"])





# --- Dependency ---
def get_auth_service() -> AuthService:
    return AuthService(get_supabase_client())


# ==========================================
# Manual Authentication Routes
# ==========================================


@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")
async def register(
    response: Response,  # noqa: ARG001
    request: Request,  # noqa: ARG001
    data: RegisterInput,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse | dict:
    """Register new user with email and password, then send OTP for verification"""
    try:
        if not data.name.strip():
            raise HTTPException(status_code=400, detail="Please enter first and last name")

        sanitized_name = sanitize_text(data.name.strip(), max_length=100)

        try:
            auth_service.create_user_with_password(data.email, data.password, sanitized_name)
        except Exception as e:
            logger.error("Registration processing error")
            error_msg = str(e)
            if "already registered" in error_msg.lower() or "unique constraint" in error_msg.lower():
                raise HTTPException(status_code=400, detail="Email already in use")
            raise HTTPException(status_code=400, detail=error_msg)

        # Generate and send OTP
        otp_service = get_otp_service()
        otp_code, _ = otp_service.create_otp(data.email)

        # Send OTP via email
        email_sent = email_service.send_otp_email(data.email, otp_code)

        if not email_sent:
            logger.warning("Failed to send OTP email to %s", data.email)

        log_security_event("register_otp_sent", details={"email": data.email}, severity="INFO")

        return {
            "access_token": None,
            "token_type": None,
            "user": None,
            "message": "Registration successful. Please check your email for the verification code.",
            "requires_verification": True,
            "email": data.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed")
        log_security_event("register_failed", details={"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again")


@router.post("/verify-otp")
@limiter.limit("10/minute")
async def verify_otp(
    response: Response,
    request: Request,
    req: VerifyOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse | dict:
    """Verify email using 6-digit OTP code"""
    try:
        otp_service = get_otp_service()
        result = await otp_service.verify_otp(req.email, req.otp)

        if not result["success"]:
            log_security_event(
                "otp_verification_failed",
                details={
                    "email": req.email,
                    "error": result.get("error"),
                    "attempts_remaining": result.get("attempts_remaining", 0),
                },
                severity="WARNING",
            )
            raise HTTPException(status_code=400, detail=result["error"])

        # OTP verified - confirm user email in Supabase
        email_confirmed = auth_service.confirm_user_email(req.email)
        if not email_confirmed:
            logger.error("Failed to confirm email after OTP verification: %s", req.email)
            raise HTTPException(status_code=500, detail="Email verification failed. Please try again.")

        # Get user data and create session
        user_data = auth_service.get_user_by_email_unverified(req.email)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        return create_login_response(auth_service, user_data.copy(), request, response)

    except HTTPException:
        raise
    except Exception:
        logger.error("OTP verification error")
        raise HTTPException(status_code=500, detail="Verification failed. Please try again.")


@router.post("/resend-otp")
@limiter.limit("3/minute")
async def resend_otp(
    request: Request,  # noqa: ARG001
    req: ResendOTPRequest,
    response: Response,  # noqa: ARG001
) -> dict:
    """Resend verification OTP code"""
    try:
        otp_service = get_otp_service()

        # Check cooldown
        can_resend, seconds_remaining = otp_service.can_resend_otp(req.email)
        if not can_resend:
            raise HTTPException(
                status_code=429, detail=f"Please wait {seconds_remaining} seconds before requesting a new code."
            )

        # Generate new OTP
        otp_code, expires_at = otp_service.create_otp(req.email)

        # Send OTP via email
        email_sent = email_service.send_otp_email(req.email, otp_code)

        if not email_sent:
            logger.warning("Failed to resend OTP email to %s", req.email)

        log_security_event("otp_resend", details={"email": req.email}, severity="INFO")

        return {"message": "Verification code sent. Please check your email.", "expires_at": expires_at}

    except HTTPException:
        raise
    except Exception:
        logger.error("Resend OTP error")
        raise HTTPException(status_code=500, detail="Failed to send verification code. Please try again.")


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    response: Response,
    request: Request,
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Login with email and password via Supabase Auth"""
    try:
        user_data = auth_service.authenticate_user(req.email, req.password)
        if not user_data:
            log_security_event("login_failed_invalid_credentials", details={"email": req.email}, severity="WARNING")
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # user_data now contains data from Supabase, but we want our own tokens
        return create_login_response(auth_service, user_data, request, response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error")
        log_security_event("login_error", details={"email": req.email, "error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh-token")
async def refresh_token(
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Refresh access token using long-lived refresh token from HttpOnly cookie"""
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        # Return 200 with null token to avoid console errors only if it's a silent refresh
        return {"access_token": None, "token_type": None, "message": "No active session"}

    ip, ua = get_client_info(request)
    payload = await auth_service.verify_refresh_token(refresh_token, ip, ua)

    if not payload:
        response.delete_cookie("refresh_token")
        return {"access_token": None, "token_type": None, "message": "Session expired"}

    user_id = payload["user_id"]
    
    # Fetch user data FIRST to maintain role and permissions
    user_obj = auth_service.get_user_by_id(user_id)
    if not user_obj:
        response.delete_cookie("refresh_token")
        return {"access_token": None, "token_type": None, "message": "User not found"}

    # Rotate token means we should revoke the OLD one to prevent reuse!
    old_jti = payload.get("jti")
    old_exp = payload.get("exp")
    if old_jti and old_exp:
        await auth_service.revoke_token(old_jti, user_id, datetime.fromtimestamp(old_exp, timezone.utc))

    new_access_token = auth_service.create_access_token(user_id, role=user_obj.role)
    new_refresh_token = auth_service.create_refresh_token(user_id, ip, ua)

    set_refresh_cookie(response, new_refresh_token)

    # Convert to safe response format (exclude password_hash)
    user_response = UserResponse(
        id=user_obj.id,
            email=user_obj.email,
            name=user_obj.name,
            picture=user_obj.picture,
            bio=user_obj.bio,
            created_at=user_obj.created_at,
            google_id=user_obj.google_id,
        )

    return {"access_token": new_access_token, "token_type": "bearer", "user": user_response}


@router.post("/logout")
async def logout(response: Response, request: Request, auth_service: AuthService = Depends(get_auth_service)) -> dict:
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
        except Exception:
            logger.warning("Logout cleanup failed (ignore)")

    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,  # noqa: ARG001
    req: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Request password reset (via Supabase Auth)"""
    try:
        auth_service.create_password_reset_token(req.email)
        return {"message": "If this email is registered, you will receive password reset instructions."}
    except Exception:
        logger.error("Forgot password processing failed")
        return {"message": "If this email is registered, you will receive password reset instructions."}


@router.post("/reset-password")
@limiter.limit("3/minute")
async def reset_password(
    request: Request,  # noqa: ARG001
    req: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Reset password using token"""
    try:
        success = await auth_service.reset_password(req.token, req.new_password)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Password updated successfully"}


@router.post("/session-exchange", response_model=LoginResponse)
@limiter.limit("10/minute")
async def exchange_session(
    response: Response,
    request: Request,
    req: SessionExchangeRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    Exchange Supabase Session (from email verification redirect) for Backend Session.
    Validates the Supabase token and issues our own secure HttpOnly cookies.
    """
    try:
        # 1. Verify Supabase Token
        user = auth_service.supabase.auth.get_user(req.access_token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid Supabase session")

        user_id = user.user.id
        email = user.user.email
        # ... (rest of function body remains conceptually same, just adding type hints)

        # 2. Get User Profile (to ensure we have name/picture)
        db_user = auth_service.get_user_by_id(user_id)

        name = db_user.name if db_user else user.user.user_metadata.get("name", "")
        picture = db_user.picture if db_user else user.user.user_metadata.get("avatar_url", "")

        # 3. Create Custom Tokens
        # Prepare a user dict from the pieces we have
        user_data = {
            "id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "bio": db_user.bio if db_user else None,
            "created_at": db_user.created_at if db_user else datetime.now(timezone.utc),
        }

        return create_login_response(auth_service, user_data, request, response)
    except Exception:
        logger.error("Session exchange failed")
        raise HTTPException(status_code=401, detail="Session verification failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current user information (unified from bot manual and google auth)"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        bio=current_user.bio,
        created_at=current_user.created_at,
        google_id=current_user.google_id,
    )


# ==========================================
# Google Authentication Routes
# ==========================================


@router.get("/google/login")
async def google_login_redirect() -> RedirectResponse:
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
) -> LoginResponse:
    """Login with Google OAuth token"""
    try:
        user_data = auth_service.verify_google_token(token_data.token)
        user = auth_service.create_or_get_user(user_data)

        return create_login_response(auth_service, user, request, response)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Google Login failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


def _validate_google_redirect_uri(redirect_uri: str) -> bool:
    """Validate the redirect URI against allowed origins"""
    allowed_origins = config.get_allowed_origins()

    # Check if the redirect URI matches any allowed origin + /auth/callback
    for origin in allowed_origins:
        expected = f"{origin.rstrip('/')}/auth/callback"
        if redirect_uri == expected:
            return True

    # Fallback for production domains not in CORS (e.g. valid subdomains)
    if redirect_uri.endswith("/auth/callback"):
        uri_parts = redirect_uri.split("/")
        if len(uri_parts) >= 3:
            origin = "/".join(uri_parts[:3])
            allowed_production_domains = [
                "http://localhost:5173",
                "https://localhost:5173",
                "https://purrfect-spots.vercel.app",
                "https://purrfectspots.xyz",
                "https://www.purrfectspots.xyz",
            ]
            if origin in allowed_production_domains:
                logger.debug(f"Auth Exchange Debug: Matched production domain={origin}")
                return True

    return False


@router.post("/google/exchange", response_model=LoginResponse)
async def google_exchange_code(
    response: Response,
    request: Request,
    exchange_data: GoogleCodeExchangeRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Exchange Google authorization code for tokens (PKCE OAuth 2.0 flow)"""
    try:
        if not exchange_data.code:
            raise ValueError("Authorization code is required")
        if not exchange_data.code_verifier:
            raise ValueError("Code verifier is required")
        if not exchange_data.redirect_uri:
            raise ValueError("Redirect URI is required")

        logger.debug(f"Auth Exchange Debug: Received redirect_uri={exchange_data.redirect_uri}")

        if not _validate_google_redirect_uri(exchange_data.redirect_uri):
            logger.warning(f"Invalid redirect URI: {exchange_data.redirect_uri}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect URI",
            )

        # Exchange code for tokens
        # Pass IP and User-Agent for fingerprinting
        ip, ua = get_client_info(request)
        login_response = await auth_service.exchange_google_code(
            exchange_data.code, exchange_data.code_verifier, exchange_data.redirect_uri, ip, ua
        )

        # Set refresh token in HttpOnly cookie
        if login_response.refresh_token:
            set_refresh_cookie(response, login_response.refresh_token)

        return login_response

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


@router.post("/sync-user")
async def sync_user_data(user: dict = Depends(get_current_user_from_header)) -> dict:
    """Insert/Upsert user into Supabase Table from JWT payload (Supabase Auth compatible)"""
    try:
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

        # Use admin client to ensure we can update users table
        supabase_admin = get_supabase_admin_client()
        res = supabase_admin.table("users").upsert(data, on_conflict="id").execute()
        return {"message": "User synced", "data": res.data if hasattr(res, "data") else data}

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {e!s}")
