"""
Manual authentication routes for email/password login
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from services.auth_service import AuthService
from dependencies import get_supabase_client
from middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Manual Authentication"])

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

def get_auth_service():
    return AuthService(get_supabase_client())

@router.post("/signup", response_model=LoginResponse)
def signup(req: SignupRequest, auth_service: AuthService = Depends(get_auth_service)):
    """
    Register new user with email and password
    """
    try:
        if auth_service.get_user_by_email(req.email):
            raise HTTPException(status_code=400, detail="Email already registered.")
        
        user = auth_service.create_user(req.email, req.password, req.name)
        token = auth_service.create_access_token(user["id"])
        return {"access_token": token, "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
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
        return {"access_token": token, "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me")
async def get_user(current_user = Depends(get_current_user)):
    """
    Get current user information (simple version)
    """
    return current_user
