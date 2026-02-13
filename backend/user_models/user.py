"""
User model for authentication
"""

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: str
    username: str | None = None
    google_id: str | None = None
    email: str
    name: str | None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_pro: bool = False
    stripe_customer_id: str | None = None
    subscription_end_date: datetime | None = None
    cancel_at_period_end: bool = False
    treat_balance: int = 0
    role: str = "user"


class UserCreate(BaseModel):
    username: str | None = None
    google_id: str | None = None
    email: str
    name: str
    picture: str | None = None
    bio: str | None = None


class UserCreateWithPassword(BaseModel):
    username: str | None = None
    email: str
    name: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str | None = None
    google_id: str | None = None
    email: str
    name: str | None = None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None
    is_pro: bool = False
    treat_balance: int = 0
    role: str = "user"


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    refresh_token: str | None = None
