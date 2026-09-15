from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.constants.security import MIN_PASSWORD_LENGTH
from app.schemas.user import UserResponse


class EmailInput(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class RegisterInput(EmailInput):
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=1024,
        description=f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
    )
    name: str = Field(..., min_length=1, max_length=100, description="Please enter first and last name")


class LoginRequest(EmailInput):
    password: str = Field(..., min_length=1, max_length=1024)


class LoginResponse(BaseModel):
    access_token: str | None = None
    token_type: str | None = "bearer"  # nosec S105
    user: UserResponse | None = None
    message: str | None = None
    requires_verification: bool = False
    email: str | None = None


class VerifyOTPRequest(EmailInput):
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^[0-9]{6}$", description="6-digit OTP code")


class ResendOTPRequest(EmailInput):
    pass


class ResendOTPResponse(BaseModel):
    message: str
    expires_at: str | None = None


class ForgotPasswordRequest(EmailInput):
    pass


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=16384)
    new_password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=1024,
        description=f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
    )


class SessionExchangeRequest(BaseModel):
    access_token: str = Field(..., min_length=1, max_length=16384)


class GoogleCodeExchangeRequest(BaseModel):
    code: str = Field(..., max_length=4096)
    code_verifier: str = Field(..., max_length=128)
    redirect_uri: str = Field(..., max_length=2048)


class SyncUserResponse(BaseModel):
    message: str
    data: dict[str, Any]


class LogoutResponse(BaseModel):
    message: str


class PasswordResetResponse(BaseModel):
    message: str
