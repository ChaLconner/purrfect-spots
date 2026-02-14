from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_current_admin_user, get_supabase_admin_client
from logger import logger

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[dict])
async def list_users(
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin_user)
) -> List[dict[str, Any]]:
    """
    List all users with pagination and optional search.
    Only accessible by admins.
    """
    try:
        admin_client = get_supabase_admin_client()
        query = admin_client.table("users").select("*").range(offset, offset + limit - 1).order("created_at", desc=True)
        
        if search:
            query = query.or_(f"email.ilike.%{search}%,name.ilike.%{search}%")
            
        result = query.execute()
        return result.data
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.get("/stats")
async def get_system_stats(current_admin: dict = Depends(get_current_admin_user)) -> dict[str, Any]:
    """
    Get basic system statistics.
    """
    try:
        admin_client = get_supabase_admin_client()
        
        # User count
        user_count = admin_client.table("users").select("id", count="exact").execute().count  # type: ignore
        
        # Photo count
        photo_count = admin_client.table("cat_photos").select("id", count="exact").is_("deleted_at", "null").execute().count  # type: ignore
        
        # Recent activity (last 24h)
        # Note: This might be slow on large datasets, optimize later
        
        return {
            "total_users": user_count,
            "total_photos": photo_count,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_admin: dict = Depends(get_current_admin_user)) -> dict[str, str]:
    """
    Delete (ban) a user.
    """
    try:
        admin_client = get_supabase_admin_client()
        
        # Check if user exists
        check = admin_client.table("users").select("role").eq("id", user_id).single().execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="User not found")
            
        if check.data.get("role") == "admin":
             raise HTTPException(status_code=400, detail="Cannot delete an admin user")
        
        # Delete user (CASCADE should handle related data if configured, otherwise manual cleanup needed)
        # Using Supabase Auth Admin to delete user from Auth + Public Schema (via triggers usually)
        # But here we use Table delete for public schema first
        
        # Soft delete or Hard delete? Let's do hard delete for "Ban" for now or use a 'banned' status
        # For simplicity, we delete from public.users table. 
        # Ideally we should also delete from auth.users via admin api
        
        admin_client.auth.admin.delete_user(user_id) # Delete from Auth (cascades to public usually)
        
        return {"message": f"User {user_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {e}")
