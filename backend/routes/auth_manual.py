"""
Manual authentication routes for email/password login
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from services.auth_service import AuthService
from dependencies import get_supabase_client
from middleware.auth_middleware import get_current_user
from user_models.user import UserResponse

router = APIRouter(prefix="/auth", tags=["Manual Authentication"])

class RegisterInput(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

def get_auth_service():
    return AuthService(get_supabase_client())

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hash(password)

def verify_password(password: str, hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.verify(password, hash)

@router.post("/register", response_model=LoginResponse)
async def register(data: RegisterInput, auth_service: AuthService = Depends(get_auth_service)):
    """
    Register new user with email and password - Simplified version
    """
    try:
        # ✅ Check if email already exists
        existing_user = auth_service.get_user_by_email(data.email)
        if existing_user:
            raise HTTPException(
                status_code=400, 
                detail="This email is already in use. Please use another email"
            )
        
        # ✅ Validate password strength
        if len(data.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters long"
            )
        
        # ✅ Validate name
        if not data.name.strip():
            raise HTTPException(
                status_code=400,
                detail="Please enter first and last name"
            )
        
        # 🔐 Hash password and insert directly to Supabase
        password_hash = hash_password(data.password)
        
        
        # Direct insert to Supabase table using admin client to bypass RLS
        from dependencies import get_supabase_admin_client
        supabase_admin = get_supabase_admin_client()
        result = supabase_admin.table("users").insert({
            "email": data.email,
            "name": data.name.strip(),
            "password_hash": password_hash
        }).execute()
        
        if hasattr(result, 'data') and result.data:
            user = result.data[0]
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to create user"
            )
        
        # 🎫 Generate access token
        token = auth_service.create_access_token(user["id"])

        # 🛠 Map user -> UserResponse schema
        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            picture=user.get("picture"),
            bio=user.get("bio"),
            created_at=user["created_at"]
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user_response
        }

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, etc.)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Registration failed. Please try again"
        )

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Login with email and password
    """
    try:
        user = auth_service.authenticate_user(req.email, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        
        token = auth_service.create_access_token(user["id"])
        
        # 🛠 Map user -> UserResponse schema
        user_response = UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            picture=user.get("picture"),
            bio=user.get("bio"),
            created_at=user["created_at"]
        )

        return {
            "access_token": token,
            "token_type": "bearer",  # ✅ REQUIRED by LoginResponse
            "user": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )


@router.get("/me")
async def get_user(current_user = Depends(get_current_user)):
    """
    Get current user information (simple version)
    """
    return current_user
