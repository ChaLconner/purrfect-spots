"""
User model for authentication
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    id: Optional[str] = None
    google_id: Optional[str] = None
    email: str
    name: str
    picture: Optional[str] = None
    bio: Optional[str] = None
    password_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserCreate(BaseModel):
    google_id: Optional[str] = None
    email: str
    name: str
    picture: Optional[str] = None
    bio: Optional[str] = None
    password_hash: Optional[str] = None


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
    name: str
    picture: Optional[str] = None
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
