"""
Authentication routes for Google OAuth and email/password authentication
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from supabase import Client
from services.auth_service import AuthService
from user_models.user import LoginResponse, UserResponse, User, UserCreateWithPassword, UserLogin
from middleware.auth_middleware import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    token: str


class GoogleCodeExchangeRequest(BaseModel):
    code: str
    code_verifier: str
    redirect_uri: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SimpleLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def get_auth_service_for_routes():
    """Dependency to get AuthService instance"""
    from dependencies import get_supabase_client
    supabase = get_supabase_client()
    return AuthService(supabase)


@router.post("/google", response_model=LoginResponse)
async def google_login(
    request: GoogleTokenRequest,
    auth_service = Depends(get_auth_service_for_routes)
):
    """
    Login with Google OAuth token
    """
    try:
        # Verify Google token
        user_data = auth_service.verify_google_token(request.token)
        
        # Create or get user from database
        user = auth_service.create_or_get_user(user_data)
        
        # Create access token
        access_token = auth_service.create_access_token(user.id)
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                picture=user.picture,
                created_at=user.created_at
            )
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/google/exchange", response_model=LoginResponse)
async def google_exchange_code(
    request: GoogleCodeExchangeRequest,
    auth_service = Depends(get_auth_service_for_routes)
):
    """
    Exchange Google authorization code for tokens (Modern OAuth 2.0 flow)
    """
    try:
        login_response = await auth_service.exchange_google_code(
            code=request.code,
            code_verifier=request.code_verifier,
            redirect_uri=request.redirect_uri
        )
        
        return LoginResponse(
            access_token=login_response.access_token,
            token_type=login_response.token_type,
            user=UserResponse(
                id=login_response.user.id,
                email=login_response.user.email,
                name=login_response.user.name,
                picture=login_response.user.picture,
                created_at=login_response.user.created_at
            )
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code exchange failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        created_at=current_user.created_at        )


@router.post("/signup", response_model=SimpleLoginResponse)
def signup(req: SignupRequest, auth_service: AuthService = Depends(get_auth_service_for_routes)):
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


@router.post("/login", response_model=SimpleLoginResponse)
def login(req: LoginRequest, auth_service: AuthService = Depends(get_auth_service_for_routes)):
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


@router.post("/register", response_model=LoginResponse)
async def register(
    request: UserCreateWithPassword,
    auth_service = Depends(get_auth_service_for_routes)
):
    """
    Register new user with email and password
    """
    try:
        # Check if user already exists
        existing_user = auth_service.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        user_data = auth_service.create_user_with_password(
            email=request.email,
            password=request.password,
            name=request.name
        )
        
        # Create access token
        access_token = auth_service.create_access_token(user_data["id"])
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"],
                picture=user_data.get("picture"),
                created_at=user_data["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: UserLogin,
    auth_service = Depends(get_auth_service_for_routes)
):
    """
    Login with email and password
    """
    try:
        # Authenticate user
        user = auth_service.authenticate_user(request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token = auth_service.create_access_token(user["id"])
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user["id"],
                email=user["email"],
                name=user["name"],
                picture=user.get("picture"),
                created_at=user["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout():
    """
    Logout user (client-side token removal)
    """
    return {"message": "Logged out successfully"}
