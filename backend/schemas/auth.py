from pydantic import BaseModel, EmailStr, Field

from user_models.user import UserResponse


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: str = Field(..., min_length=1, description="Please enter first and last name")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str | None = None
    token_type: str | None = "bearer"
    user: UserResponse | None = None
    message: str | None = None
    requires_verification: bool = False
    email: str | None = None


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit OTP code")


class ResendOTPRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class SessionExchangeRequest(BaseModel):
    access_token: str
    refresh_token: str
