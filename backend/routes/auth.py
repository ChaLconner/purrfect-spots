"""
Authentication routes for both Manual (Email/Password) and Google OAuth
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from config import config
from dependencies import get_auth_service, get_otp_service
from limiter import auth_limiter, forgot_password_limiter
from logger import logger, sanitize_log_value
from middleware.auth_middleware import get_current_user, get_current_user_from_header, invalidate_user_auth_cache
from schemas.auth import (
    ForgotPasswordRequest,
    GoogleCodeExchangeRequest,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    PasswordResetResponse,
    RegisterInput,
    ResendOTPRequest,
    ResendOTPResponse,
    ResetPasswordRequest,
    SessionExchangeRequest,
    SyncUserResponse,
    VerifyOTPRequest,
)
from schemas.user import User, UserResponse
from services.auth_service import AuthService
from services.email_service import email_service
from services.otp_service import OTPService
from services.password_service import password_service
from utils.auth_response_utils import create_login_response
from utils.auth_utils import get_client_info, set_refresh_cookie
from utils.exceptions import ConflictError
from utils.security import log_security_event, sanitize_text

router = APIRouter(prefix="/auth", tags=["Authentication"])


# AuthService is now imported from dependencies


def _ensure_user_not_banned(user: User | dict[str, Any] | Any) -> None:
    """Block token issuance for suspended accounts."""
    banned_at = user.get("banned_at") if isinstance(user, dict) else getattr(user, "banned_at", None)
    if banned_at:
        raise HTTPException(status_code=403, detail="Account suspended")


async def _invalidate_auth_cache_for_user(user: User | dict[str, Any] | Any) -> None:
    """Clear stale auth snapshots before issuing fresh session data."""
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    if not user_id:
        return
    await invalidate_user_auth_cache(str(user_id))


# ==========================================
# Manual Authentication Routes
# ==========================================


from typing import Annotated


@router.post("/register", response_model=LoginResponse)
@auth_limiter.limit("5/minute")
async def register(
    response: Response,  # noqa: ARG001
    request: Request,  # noqa: ARG001
    data: RegisterInput,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    otp_service: Annotated[OTPService, Depends(get_otp_service)],
) -> LoginResponse:
    """
    Register new user with email and password, then send OTP for verification.
    """
    try:
        if not data.name.strip():
            raise HTTPException(status_code=400, detail="Please enter first and last name")

        is_valid, password_error = await password_service.validate_new_password(data.password, check_breach=False)
        if not is_valid:
            raise HTTPException(
                status_code=400, detail=password_error or "Password does not meet security requirements"
            )

        sanitized_name = sanitize_text(data.name.strip(), max_length=100)

        try:
            await auth_service.create_user_with_password(data.email, data.password, sanitized_name)
        except ConflictError as e:
            # Re-raise conflict for existing registered users
            logger.warning("Registration attempt for existing email: %s", data.email)
            raise HTTPException(status_code=409, detail="This email is already registered") from e
        except Exception as e:
            logger.error("Registration processing error: %s", e)
            error_msg = str(e)
            if "already registered" in error_msg.lower() or "unique constraint" in error_msg.lower():
                raise HTTPException(status_code=409, detail="Email already in use") from e
            raise HTTPException(status_code=400, detail=error_msg) from e

        # Generate and send OTP
        try:
            otp_code, _ = await otp_service.create_otp(data.email)
            # Send OTP via email
            email_sent = email_service.send_otp_email(data.email, otp_code)
            if not email_sent:
                logger.warning("Failed to send OTP email to %s", data.email)
        except Exception as e:
            logger.error("Failed to process OTP for %s: %s", data.email, e)
            # We don't fail registration if OTP fails (user can resend), but we log it
            pass

        log_security_event("register_success_otp_pending", details={"email": data.email}, severity="INFO")

        return LoginResponse(
            access_token=None,  # nosec B105
            token_type=None,  # nosec B105
            user=None,
            message="Registration successful. Please check your email for the verification code.",
            requires_verification=True,
            email=data.email,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed: %s", e)
        log_security_event("register_failed", details={"error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again") from e


@router.post("/verify-otp")
@auth_limiter.limit("10/minute")
async def verify_otp(
    response: Response,
    request: Request,
    req: VerifyOTPRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    otp_service: Annotated[OTPService, Depends(get_otp_service)],
) -> LoginResponse:
    """
    Verify email with OTP and complete registration.
    """
    try:
        # 1. Verify OTP
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
            # Standardizing error message for the frontend
            error_msg = result.get("error", "Invalid verification code")
            if "expired" in error_msg.lower():
                error_msg = "Verification code has expired. Please request a new one."
            raise HTTPException(status_code=400, detail=error_msg)

        # 2. Confirm email in Auth system
        confirmed = await auth_service.confirm_user_email(req.email)
        if not confirmed:
            logger.error("Email confirmation failed for %s", req.email)
            raise HTTPException(status_code=500, detail="Failed to verify email. Please contact support.")

        # 3. Retrieve user to create session
        user_info = await auth_service.get_user_by_email_unverified(req.email)
        if not user_info:
            logger.error("Post-verification user retrieval failed for %s", req.email)
            raise HTTPException(status_code=404, detail="User account not found after verification")

        # 4. Success - Create login response
        # This will create or update the user in our DB and generate both tokens
        user = await auth_service.create_or_get_user(user_info)
        _ensure_user_not_banned(user)
        await _invalidate_auth_cache_for_user(user)

        log_security_event("otp_verified", details={"user_id": user.id, "email": req.email}, severity="INFO")

        return create_login_response(auth_service, user, request, response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("OTP Verification exception: %s", e)
        raise HTTPException(status_code=500, detail="Verification process failed. Please try again.") from e


@router.post("/resend-otp", response_model=ResendOTPResponse)
@auth_limiter.limit("3/minute")
async def resend_otp(
    request: Request,  # noqa: ARG001
    req: ResendOTPRequest,
    response: Response,  # noqa: ARG001
    otp_service: Annotated[OTPService, Depends(get_otp_service)],
) -> ResendOTPResponse:
    """
    Resend verification OTP code.

    Raises:
        HTTPException: 429 - If cooldown is active.
        HTTPException: 500 - If sending fails.
    """
    try:
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
            logger.warning("Failed to send OTP email to %s", req.email)

        log_security_event("otp_resend", details={"email": req.email}, severity="INFO")

        return ResendOTPResponse(message="Verification code sent. Please check your email.", expires_at=expires_at)

    except HTTPException:
        raise
    except Exception:
        logger.error("Resend OTP error")
        raise HTTPException(status_code=500, detail="Failed to send verification code. Please try again.")


@router.post("/login", response_model=LoginResponse)
@auth_limiter.limit("5/minute")
async def login(
    response: Response,
    request: Request,
    req: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """
    Login with email and password via Supabase Auth.

    Raises:
        HTTPException: 401 - If credentials are invalid.
        HTTPException: 500 - If login fails.
    """
    try:
        user_data = await auth_service.authenticate_user(req.email, req.password)
        if not user_data:
            log_security_event("login_failed_invalid_credentials", details={"email": req.email}, severity="WARNING")
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        _ensure_user_not_banned(user_data)
        await _invalidate_auth_cache_for_user(user_data)

        # user_data now contains data from Supabase, but we want our own tokens
        return create_login_response(auth_service, user_data, request, response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login error")
        log_security_event("login_error", details={"email": req.email, "error": str(e)}, severity="ERROR")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh-token", response_model=LoginResponse)
async def refresh_token(
    response: Response,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """
    Refresh access token using long-lived refresh token from HttpOnly cookie.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        # Return empty access token to allow silent refresh logic in frontend to reset state
        return LoginResponse(access_token=None, token_type=None, message="No active session")

    try:
        ip, ua = get_client_info(request)
        payload = await auth_service.verify_refresh_token(refresh_token, ip, ua)

        if not payload:
            response.delete_cookie("refresh_token")
            return LoginResponse(access_token=None, token_type=None, message="Session expired")

        user_id = payload["user_id"]
        user_obj = await auth_service.get_user_by_id(user_id)

        if not user_obj:
            logger.warning("User not found during token refresh: %s", user_id)
            response.delete_cookie("refresh_token")
            return LoginResponse(access_token=None, token_type=None, message="User not found")
        if user_obj.banned_at:
            logger.info("Blocked refresh for suspended user: %s", user_id)
            response.delete_cookie("refresh_token")
            return LoginResponse(access_token=None, token_type=None, message="Account suspended")

        # Rotate token: revoke old one if it has a JTI
        old_jti = payload.get("jti")
        old_exp = payload.get("exp")
        if old_jti and old_exp:
            try:
                # payload['exp'] is usually a timestamp (int)
                exp_dt = datetime.fromtimestamp(old_exp, UTC) if isinstance(old_exp, (int, float)) else None
                if exp_dt:
                    await auth_service.revoke_token(old_jti, user_id, exp_dt)
            except Exception as e:
                logger.debug("Failed to revoke old refresh token: %s", e)

        log_security_event("token_refresh", details={"user_id": user_id}, severity="INFO")
        await _invalidate_auth_cache_for_user(user_obj)

        # use the central responder for consistency
        return create_login_response(auth_service, user_obj, request, response)

    except Exception as e:
        logger.error("Token refresh failed fundamentally: %s", e)
        response.delete_cookie("refresh_token")
        return LoginResponse(access_token=None, token_type=None, message="Refresh failed")


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    response: Response,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LogoutResponse:
    """
    Logout user (clear refresh token cookie and revoke it).

    Raises:
        HTTPException: 500 - If logout process fails unexpectedly.
    """
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
                    await auth_service.revoke_token(jti, user_id, datetime.fromtimestamp(exp, UTC))
        except Exception:
            logger.warning("Logout cleanup failed (ignore)")

    response.delete_cookie("refresh_token")
    return LogoutResponse(message="Logged out successfully")


@router.post("/forgot-password", response_model=PasswordResetResponse)
@forgot_password_limiter.limit(config.RATE_LIMIT_FORGOT_PASSWORD)
async def forgot_password(
    request: Request,  # noqa: ARG001
    req: ForgotPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> PasswordResetResponse:
    """
    Request password reset (via Supabase Auth).

    Raises:
        HTTPException: 500 - If forgot password request fails.
    """
    try:
        await auth_service.create_password_reset_token(req.email)
        return PasswordResetResponse(
            message="If this email is registered, you will receive password reset instructions."
        )
    except Exception:
        logger.error("Forgot password processing failed")
        return PasswordResetResponse(
            message="If this email is registered, you will receive password reset instructions."
        )


@router.post("/reset-password", response_model=PasswordResetResponse)
@forgot_password_limiter.limit(config.RATE_LIMIT_FORGOT_PASSWORD)
async def reset_password(
    request: Request,  # noqa: ARG001
    req: ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> PasswordResetResponse:
    """
    Reset password using token.

    Raises:
        HTTPException: 400 - If reset token is invalid or expired.
    """
    try:
        success = await auth_service.reset_password(req.token, req.new_password)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return PasswordResetResponse(message="Password updated successfully")


@router.post("/session-exchange", response_model=LoginResponse)
@auth_limiter.limit("10/minute")
async def exchange_session(
    response: Response,
    request: Request,
    req: SessionExchangeRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """
    Exchange Supabase Session (from email verification redirect) for Backend Session.
    Validates the Supabase token and issues our own secure HttpOnly cookies.
    """
    try:
        # 1. Verify Supabase Token (Async)
        user_res = await auth_service.supabase_client.auth.get_user(req.access_token)
        if not user_res or not user_res.user:
            log_security_event("session_exchange_failed_invalid_token", severity="WARNING")
            raise HTTPException(status_code=401, detail="Invalid Supabase session")

        sb_user = user_res.user
        user_id = sb_user.id
        email = sb_user.email

        # 2. Get User Profile (to ensure we have role/permissions/metadata)
        db_user = await auth_service.get_user_by_id(user_id)

        # Fallback metadata from Supabase if DB record doesn't exist yet
        name = sb_user.user_metadata.get("name") or sb_user.user_metadata.get("full_name", "")
        picture = sb_user.user_metadata.get("avatar_url") or sb_user.user_metadata.get("picture", "")

        # Prepare data for responders (handle both models and dicts)
        user_payload: Any
        if db_user:
            _ensure_user_not_banned(db_user)
            user_payload = db_user
        else:
            user_payload = {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "role": "user",
                "permissions": [],
            }

        log_security_event("session_exchange_success", details={"user_id": user_id}, severity="INFO")
        await _invalidate_auth_cache_for_user(user_payload)
        return create_login_response(auth_service, user_payload, request, response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Session exchange failed: %s", e)
        raise HTTPException(status_code=401, detail="Session verification failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Annotated[UserResponse, Depends(get_current_user)]) -> UserResponse:
    """
    Get current user information (unified from both manual and google auth).

    Raises:
        HTTPException: 401 - If user is not authenticated.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        bio=current_user.bio,
        created_at=current_user.created_at,
        google_id=current_user.google_id,
        role=current_user.role,
        permissions=current_user.permissions,
    )


# ==========================================
# Google Authentication Routes
# ==========================================


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
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    """
    Exchange Google authorization code for tokens (PKCE OAuth 2.0 flow)

    Raises:
        HTTPException: 400 - If redirect URI is invalid or exchange data is missing.
        HTTPException: 500 - If code exchange fails.
    """
    try:
        if not exchange_data.code:
            raise ValueError("Authorization code is required")
        if not exchange_data.code_verifier:
            raise ValueError("Code verifier is required")
        if not exchange_data.redirect_uri:
            raise ValueError("Redirect URI is required")

        logger.debug("Auth Exchange Debug: Received redirect_uri=%s", sanitize_log_value(exchange_data.redirect_uri))

        if not _validate_google_redirect_uri(exchange_data.redirect_uri):
            logger.warning("Invalid redirect URI: %s", sanitize_log_value(exchange_data.redirect_uri))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid redirect URI",
            )

        # Exchange code for tokens
        # Pass IP and User-Agent for fingerprinting
        ip, ua = get_client_info(request)
        try:
            login_response = await auth_service.exchange_google_code(
                exchange_data.code, exchange_data.code_verifier, exchange_data.redirect_uri, ip, ua
            )
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
        except ValueError as e:
            logger.warning("[OAuth] Invalid code exchange: %s", e)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except Exception as e:
            logger.error("[OAuth] Code exchange processing error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication failed"
            ) from e

        if login_response.user is None:
            logger.error("Google exchange succeeded but user is None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication succeeded but user profile is missing",
            )

        refresh_token = auth_service.create_refresh_token(login_response.user.id, ip, ua)
        set_refresh_cookie(response, refresh_token)

        log_security_event("google_exchange_success", details={"user_id": login_response.user.id}, severity="INFO")
        return login_response

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        logger.error("Google Exchange failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code exchange failed",
        )


@router.post("/sync-user", response_model=SyncUserResponse)
async def sync_user_data(
    user_payload: Annotated[dict, Depends(get_current_user_from_header)],
) -> SyncUserResponse:
    """
    Sync user data from JWT payload to database.
    """
    try:
        user_id = user_payload.get("sub") or user_payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub")

        email = user_payload.get("email")
        user_metadata = user_payload.get("user_metadata", {})
        app_metadata = user_payload.get("app_metadata", {})

        # Extract name and picture with fallback
        name = user_metadata.get("name") or user_metadata.get("full_name") or user_payload.get("name")
        picture = user_metadata.get("avatar_url") or user_metadata.get("picture") or user_payload.get("picture")

        google_id = None
        provider = app_metadata.get("provider", "")
        if provider == "google":
            google_id = user_metadata.get("provider_id")
        elif user_payload.get("google_id"):
            google_id = user_payload.get("google_id")

        data = {
            "id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "google_id": google_id,
        }

        # Filter out None values to avoid overwriting existing data with null
        upsert_data = {k: v for k, v in data.items() if v is not None}

        # Use admin client to ensure we can update users table
        from dependencies import get_async_supabase_admin_client

        supabase_admin = await get_async_supabase_admin_client()

        res = await supabase_admin.table("users").upsert(upsert_data, on_conflict="id").execute()

        # Safe access to data attribute
        sync_result = getattr(res, "data", [upsert_data])[0] if getattr(res, "data", None) else upsert_data

        logger.info("User synced successfully: %s", user_id)
        return SyncUserResponse(message="User synced", data=sync_result)

    except Exception as e:
        logger.error("Sync failed for user: %s", e)
        raise HTTPException(status_code=500, detail="Sync failed")
