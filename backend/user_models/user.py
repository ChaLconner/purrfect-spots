"""
User model for authentication
"""

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    id: str
    google_id: str | None = None
    email: str
    name: str | None
    picture: str | None = None
    bio: str | None = None
    password_hash: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserCreate(BaseModel):
    google_id: str | None = None
    email: str
    name: str
    picture: str | None = None
    bio: str | None = None
    password_hash: str | None = None


class UserCreateWithPassword(BaseModel):
    email: str
    name: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None = None
    picture: str | None = None
    bio: str | None = None
    created_at: datetime | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    refresh_token: str | None = None
