"""
Authentication service for Google OAuth and traditional email/password auth
"""
import os
import jwt
import httpx
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from google.auth.transport import requests
from google.oauth2 import id_token
from supabase import Client
from user_models.user import User, UserCreate, UserCreateWithPassword, UserLogin, LoginResponse, UserResponse

# Load environment variables
import pathlib
backend_dir = pathlib.Path(__file__).parent.parent
env_path = backend_dir / ".env"
load_dotenv(str(env_path))

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


class AuthService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        # Import admin client for user creation operations
        from dependencies import get_supabase_admin_client
        self.supabase_admin = get_supabase_admin_client()
        self.google_client_id = GOOGLE_CLIENT_ID
        self.google_client_secret = GOOGLE_CLIENT_SECRET
        self.jwt_secret = os.getenv("JWT_SECRET", "your-secret-key")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hash.encode("utf-8"))

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
        """Create new user or get existing user from database using Supabase Auth pattern"""
        try:
            # Use user_id from Supabase JWT (auth.uid()) as primary key
            user_id = user_data.get('id') or user_data.get('sub')
            
            if not user_id:
                raise ValueError("Missing user_id (sub) in user_data")
            
            email = user_data.get('email', '')
            name = user_data.get('name', '')
            picture = user_data.get('picture', '')
            google_id = user_data.get('google_id')
            
            # Upsert to users table using auth.uid() as primary key
            user_record = {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "google_id": google_id,
                "bio": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Add password_hash as None for OAuth users
            user_record['password_hash'] = None
            
            # Use admin client for user creation (bypass RLS)
            result = self.supabase_admin.table('users').upsert(
                user_record,
                on_conflict="id"
            ).execute()
            
            user_dict = result.data[0]
            
            # Add password_hash field if missing (for backward compatibility)
            if 'password_hash' not in user_dict:
                user_dict['password_hash'] = None
            
            return User(**user_dict)
                
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    def create_access_token(self, user_id: str, user_data: dict = None) -> str:
        """Create JWT access token with user data in Supabase format"""
        expire = datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        to_encode = {
            "user_id": user_id,
            "sub": user_id,  # Add sub claim for compatibility
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        # Add user data in JWT payload in Supabase format
        if user_data:
            to_encode.update({
                "email": user_data.get("email", ""),
                "user_metadata": {
                    "name": user_data.get("name", ""),
                    "avatar_url": user_data.get("picture", ""),
                    "provider_id": user_data.get("google_id")
                },
                "app_metadata": {
                    "provider": "google" if user_data.get("google_id") else "email"
                }
            })
        
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

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email from database"""
        try:
            result = self.supabase.table('users').select('*').eq('email', email).single().execute()
            return result.data if result.data else None
        except Exception:
            return None

    def create_user_with_password(self, email: str, password: str, name: str) -> dict:
        """Create new user with email and password"""
        try:
            password_hash = self.hash_password(password)
            user_data = {
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "bio": None,  # Default bio value
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            # Use admin client for user creation (bypass RLS)
            result = self.supabase_admin.table('users').insert(user_data).execute()
            return result.data[0]
        except Exception as e:
            raise Exception(f"Failed to create user: {str(e)}")

    def create_user(self, email: str, password: str, name: str) -> dict:
        """Create new user with email and password (alias for create_user_with_password)"""
        return self.create_user_with_password(email, password, name)

    def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user with email and password"""
        try:
            user = self.get_user_by_email(email)
            if not user or not user.get("password_hash"):
                return None
            if not self.verify_password(password, user["password_hash"]):
                return None
            return user
        except Exception:
            return None

    async def exchange_google_code(self, code: str, code_verifier: str, redirect_uri: str) -> LoginResponse:
        """
        Exchange Google authorization code for access token using PKCE flow
        """
        try:
            # Validate required parameters
            if not code:
                raise ValueError("Authorization code is required")
            if not code_verifier:
                raise ValueError("Code verifier is required")
            if not redirect_uri:
                raise ValueError("Redirect URI is required")
            
            # Exchange code for access token
            token_url = "https://oauth2.googleapis.com/token"
            
            data = {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(token_url, data=data, headers=headers)
                
                if response.status_code != 200:
                    error_text = response.text
                    try:
                        error_json = response.json()
                        if "error" in error_json:
                            error_text = f"OAuth error: {error_json['error']}"
                            if "error_description" in error_json:
                                error_text += f" - {error_json['error_description']}"
                    except:
                        pass
                    raise ValueError(f"Token exchange failed: {error_text}")
                
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
                
                # Extract user info with Supabase-compatible UUID
                import uuid
                
                google_sub = idinfo['sub']  # Google's user ID
                
                # Try to find user with google_id matching this Google sub first
                existing_user = None
                try:
                    result = self.supabase.table('users').select('*').eq('google_id', google_sub).execute()
                    if result.data:
                        existing_user = result.data[0]
                except:
                    pass
                
                # If no existing user, create new UUID for auth.uid()
                user_uuid = existing_user['id'] if existing_user else str(uuid.uuid4())
                
                user_data = {
                    'id': user_uuid,
                    'sub': user_uuid,
                    'google_id': google_sub,
                    'email': idinfo['email'],
                    'name': idinfo['name'],
                    'picture': idinfo.get('picture', '')
                }
                
                # Create or get user
                user = self.create_or_get_user(user_data)
                
                # Create JWT token
                jwt_token = self.create_access_token(user.id, user_data)
                
                return LoginResponse(
                    access_token=jwt_token,
                    token_type="bearer",
                    user=UserResponse(
                        id=user.id,
                        email=user.email,
                        name=user.name,
                        picture=user.picture,
                        bio=user.bio,
                        created_at=user.created_at
                    )
                )
                
        except ValueError as e:
            # Re-raise ValueError with original message
            raise e
        except Exception as e:
            raise ValueError(f"Code exchange failed: {str(e)}")
