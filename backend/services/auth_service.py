"""
Authentication service for Google OAuth
"""
import os
import jwt
import httpx
from datetime import datetime, timedelta
from typing import Optional
from google.auth.transport import requests
from google.oauth2 import id_token
from supabase import Client
from user_models.user import User, UserCreate, LoginResponse, UserResponse


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

    async def exchange_google_code(self, code: str, code_verifier: str, redirect_uri: str) -> LoginResponse:
        """
        Exchange Google authorization code for access token using PKCE flow
        """
        try:
            # Exchange code for access token
            token_url = "https://oauth2.googleapis.com/token"
            
            data = {
                "client_id": self.google_client_id,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data)
                
                if response.status_code != 200:
                    raise ValueError(f"Token exchange failed: {response.text}")
                
                token_data = response.json()
                access_token = token_data.get("access_token")
                id_token_str = token_data.get("id_token")
                
                if not access_token or not id_token_str:
                    raise ValueError("Missing tokens in response")
                
                # Verify and decode ID token
                idinfo = id_token.verify_oauth2_token(
                    id_token_str, requests.Request(), self.google_client_id
                )
                
                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError('Wrong issuer.')
                
                # Extract user info
                user_data = {
                    'google_id': idinfo['sub'],
                    'email': idinfo['email'],
                    'name': idinfo['name'],
                    'picture': idinfo.get('picture', '')
                }
                
                # Create or get user
                user = self.create_or_get_user(user_data)
                
                # Create JWT token
                jwt_token = self.create_access_token(user.id)
                
                return LoginResponse(
                    access_token=jwt_token,
                    token_type="bearer",
                    user=UserResponse(
                        id=user.id,
                        email=user.email,
                        name=user.name,
                        picture=user.picture,
                        created_at=user.created_at
                    )
                )
                
        except Exception as e:
            raise ValueError(f"Code exchange failed: {str(e)}")
