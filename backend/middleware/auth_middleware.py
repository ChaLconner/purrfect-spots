"""
Authentication middleware for protecting routes
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from supabase import Client


security = HTTPBearer()


def get_auth_service_dependency():
    """Dependency to get AuthService instance"""
    from services.auth_service import AuthService
    from main import get_supabase_client
    supabase = get_supabase_client()
    return AuthService(supabase)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service = Depends(get_auth_service_dependency)
):
    """Get current authenticated user"""
    from user_models.user import User
    
    token = credentials.credentials
    user_id = auth_service.verify_access_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service = Depends(get_auth_service_dependency)
):
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, auth_service)
    except HTTPException:
        return None
