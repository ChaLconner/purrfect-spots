from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from config import config
from dependencies import get_supabase_client
from limiter import auth_limiter as limiter
from logger import logger
from middleware.auth_middleware import get_current_user
from schemas.auth import (
    ForgotPasswordRequest,
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
from utils.auth_utils import get_client_info, set_refresh_cookie

router = APIRouter(prefix="/auth", tags=["Manual Authentication"])


def get_auth_service():
    return AuthService(get_supabase_client())


@router.post("/register", response_model=LoginResponse)
@limiter.limit("5/minute")
async def register(
    response: Response,
    request: Request,
    data: RegisterInput,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register new user with email and password, then send OTP for verification"""
    try:
        if not data.name.strip():
            raise HTTPException(status_code=400, detail="Please enter first and last name")
            
        from utils.security import sanitize_text
        sanitized_name = sanitize_text(data.name.strip(), max_length=100)

        # Create user via Supabase Auth (without email confirmation)
        try:
            user_data = auth_service.create_user_with_password(data.email, data.password, sanitized_name)
        except Exception as e:
            logger.error(f"Registration error detail: {e}")
            error_msg = str(e)
            if "already registered" in error_msg.lower() or "unique constraint" in error_msg.lower():
                raise HTTPException(status_code=400, detail="Email already in use")
            raise HTTPException(status_code=400, detail=error_msg)

        # Generate and send OTP
        otp_service = get_otp_service()
        otp_code, expires_at = await otp_service.create_otp(data.email)

        # Send OTP via email
        email_sent = email_service.send_otp_email(data.email, otp_code)

        if not email_sent:
            logger.warning(f"Failed to send OTP email to {data.email}")

        from utils.security import log_security_event

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
        logger.error(f"Registration failed: {e}")
        from utils.security import log_security_event

        log_security_event("register_failed", details={"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again")


@router.post("/verify-otp")
@limiter.limit("10/minute")
async def verify_otp(
    response: Response,
    request: Request,
    req: VerifyOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Verify email using 6-digit OTP code"""
    try:
        otp_service = get_otp_service()
        result = await otp_service.verify_otp(req.email, req.otp)

        if not result["success"]:
            from utils.security import log_security_event

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
            logger.error(f"Failed to confirm email after OTP verification: {req.email}")
            raise HTTPException(status_code=500, detail="Email verification failed. Please try again.")

        # Get user data and create session
        user_data = auth_service.get_user_by_email_unverified(req.email)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = user_data["id"]
        ip, ua = get_client_info(request)

        # Create tokens
        access_token = auth_service.create_access_token(
            user_id, {"email": user_data["email"], "name": user_data["name"], "picture": user_data.get("picture", "")}
        )
        refresh_token = auth_service.create_refresh_token(user_id, ip, ua)

        set_refresh_cookie(response, refresh_token)

        from utils.security import log_security_event

        log_security_event("otp_verification_success", user_id=user_id, details={"ip": ip}, severity="INFO")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"],
                picture=user_data.get("picture", ""),
                bio=None,
                created_at=user_data["created_at"],
            ),
            "message": "Email verified successfully!",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed. Please try again.")


@router.post("/resend-otp")
@limiter.limit("3/minute")
async def resend_otp(
    request: Request,
    req: ResendOTPRequest,
):
    """Resend verification OTP code"""
    try:
        otp_service = get_otp_service()

        # Check cooldown
        can_resend, seconds_remaining = await otp_service.can_resend_otp(req.email)
        if not can_resend:
            raise HTTPException(
                status_code=429, detail=f"Please wait {seconds_remaining} seconds before requesting a new code."
            )

        # Generate new OTP
        otp_code, expires_at = await otp_service.create_otp(req.email)

        # Send OTP via email
        email_sent = email_service.send_otp_email(req.email, otp_code)

        if not email_sent:
            logger.warning(f"Failed to resend OTP email to {req.email}")

        from utils.security import log_security_event

        log_security_event("otp_resend", details={"email": req.email}, severity="INFO")

        return {"message": "Verification code sent. Please check your email.", "expires_at": expires_at}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend OTP error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification code. Please try again.")


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    response: Response,
    request: Request,
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login with email and password via Supabase Auth"""
    try:
        user_data = auth_service.authenticate_user(req.email, req.password)
        if not user_data:
            from utils.security import log_security_event

            log_security_event("login_failed_invalid_credentials", details={"email": req.email}, severity="WARNING")
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # user_data now contains data from Supabase, but we want our own tokens
        user_id = user_data["id"]
        ip, ua = get_client_info(request)

        access_token = auth_service.create_access_token(user_id, user_data)
        refresh_token = auth_service.create_refresh_token(user_id, ip, ua)

        set_refresh_cookie(response, refresh_token)

        user_response = UserResponse(
            id=user_id,
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data.get("picture"),
            bio=user_data.get("bio"),
            created_at=user_data["created_at"],
        )

        from utils.security import log_security_event

        log_security_event("login_success", user_id=user_id, details={"ip": ip, "ua": ua}, severity="INFO")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        from utils.security import log_security_event

        log_security_event("login_error", details={"email": req.email, "error": str(e)}, severity="ERROR")
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
        # Return 200 with null token to avoid console errors only if it's a silent refresh
        # But we don't know if it's silent or not.
        # Best practice for SPA: Return 200 OK with authenticated=False or no token
        return {"access_token": None, "token_type": None, "message": "No active session"}

    ip, ua = get_client_info(request)
    payload = await auth_service.verify_refresh_token(refresh_token, ip, ua)

    if not payload:
        response.delete_cookie("refresh_token")
        # Same here - soft fail
        return {"access_token": None, "token_type": None, "message": "Session expired"}

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
async def logout(response: Response, request: Request, auth_service: AuthService = Depends(get_auth_service)):
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
    """Request password reset (via Supabase Auth)"""
    try:
        # Supabase sends the email automatically
        await auth_service.create_password_reset_token(req.email)
        return {"message": "If this email is registered, you will receive password reset instructions."}
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return {"message": "If this email is registered, you will receive password reset instructions."}


@router.post("/reset-password")
@limiter.limit("3/minute")
async def reset_password(
    request: Request,
    req: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
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
):
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

        # 2. Get User Profile (to ensure we have name/picture)
        db_user = auth_service.get_user_by_id(user_id)
        if not db_user:
            # Sync might be needed if handle_new_user trigger hasn't fired yet?
            # It should have fired on insert.
            # If not found, maybe just use auth data?
            pass

        name = db_user.name if db_user else user.user.user_metadata.get("name", "")
        picture = db_user.picture if db_user else user.user.user_metadata.get("avatar_url", "")

        # 3. Create Custom Tokens
        ip, ua = get_client_info(request)
        new_access_token = auth_service.create_access_token(user_id, {"email": email, "name": name, "picture": picture})
        new_refresh_token = auth_service.create_refresh_token(user_id, ip, ua)

        # 4. Set Cookie
        set_refresh_cookie(response, new_refresh_token)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "user": UserResponse(
                id=user_id,
                email=email,
                name=name,
                picture=picture,
                bio=db_user.bio if db_user else None,
                created_at=db_user.created_at if db_user else datetime.now(timezone.utc),
            ),
        }
    except Exception as e:
        logger.error(f"Session exchange failed: {e}")
        raise HTTPException(status_code=401, detail="Session verification failed")


@router.get("/me")
async def get_user(current_user=Depends(get_current_user)):
    """Get current user information"""
    return current_user
