"""
User profile management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from middleware.auth_middleware import get_current_user
from dependencies import get_supabase_client
from user_models.user import User

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    picture: Optional[str] = None


@router.put("/")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile information
    """
    try:
        supabase = get_supabase_client()
        
        # Prepare update data
        update_data = {}
        if profile_data.name is not None:
            update_data["name"] = profile_data.name
        if profile_data.bio is not None:
            update_data["bio"] = profile_data.bio
        if profile_data.picture is not None:
            update_data["picture"] = profile_data.picture
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")
        
        # Update user in database
        result = supabase.table("users").update(update_data).eq("id", current_user.id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return updated user data
        updated_user = result.data[0]
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user["id"],
                "email": updated_user["email"],
                "name": updated_user["name"],
                "picture": updated_user.get("picture"),
                "bio": updated_user.get("bio"),
                "created_at": updated_user["created_at"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")


@router.get("/")
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    try:
        supabase = get_supabase_client()
        
        # Get user data from database
        result = supabase.table("users").select("*").eq("id", current_user.id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_data = result.data[0]
        return {
            "id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "bio": user_data.get("bio"),
            "created_at": user_data["created_at"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@router.get("/uploads")
async def get_user_uploads(current_user: User = Depends(get_current_user)):
    """
    Get all uploads by current user
    """
    try:
        supabase = get_supabase_client()
        
        # Get uploads from database (you'll need to create this table)
        result = supabase.table("uploads").select("*").eq("user_id", current_user.id).order("created_at", desc=True).execute()
        
        return {
            "uploads": result.data
        }
        
    except Exception as e:
        # Return empty list if table doesn't exist yet
        return {"uploads": []}
