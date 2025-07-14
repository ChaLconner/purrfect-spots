"""
Authentication service for Google OAuth
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional
from google.auth.transport import requests
from google.oauth2 import id_token
from supabase import Client
from ..models.user import User, UserCreate


class AuthService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24

    def verify_google_token(self, token: str) -> dict:
        """Verify Google OAuth token and return user info"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), self.google_client_id
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
                
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo['name'],
                'picture': idinfo.get('picture', '')
            }
        except ValueError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def create_or_get_user(self, user_data: dict) -> User:
        """Create new user or get existing user from database"""
        try:
            # Check if user exists
            result = self.supabase.table('users').select('*').eq('google_id', user_data['google_id']).execute()
            
            if result.data:
                # User exists, update their info
                user_update = {
                    'name': user_data['name'],
                    'picture': user_data['picture'],
                    'updated_at': datetime.utcnow().isoformat()
                }
                updated_result = self.supabase.table('users').update(user_update).eq('google_id', user_data['google_id']).execute()
                return User(**updated_result.data[0])
            else:
                # Create new user
                user_create = UserCreate(**user_data)
                new_user_data = user_create.dict()
                new_user_data['created_at'] = datetime.utcnow().isoformat()
                new_user_data['updated_at'] = datetime.utcnow().isoformat()
                
                insert_result = self.supabase.table('users').insert(new_user_data).execute()
                return User(**insert_result.data[0])
                
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        to_encode = {
            "user_id": user_id,
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        return encoded_jwt

    def verify_access_token(self, token: str) -> Optional[str]:
        """Verify JWT access token and return user_id"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            user_id = payload.get("user_id")
            return user_id
        except jwt.PyJWTError:
            return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from database"""
        try:
            result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception:
            return None
