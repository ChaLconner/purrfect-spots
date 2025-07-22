"""
User profile m@router.put("/")
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user_from_credentials)
):ment routes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from middleware.auth_middleware import get_current_user_from_credentials
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
    current_user: User = Depends(get_current_user_from_credentials)
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
async def get_profile(current_user: User = Depends(get_current_user_from_credentials)):
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
async def get_user_uploads(current_user: User = Depends(get_current_user_from_credentials)):
    """
    Get all uploads by current user - filtered by user_id
    """
    try:
        supabase = get_supabase_client()
        user_id = current_user.id
        
        print(f"Fetching uploads for user_id: {user_id}")
        
        # Get uploads from cat_photos table filtered by user_id
        result = supabase.table("cat_photos").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        
        print(f"Found {len(result.data)} uploads for user {user_id}")
        
        # Format the data to match frontend expectations
        uploads = []
        for photo in result.data:
            upload_item = {
                "id": photo["id"],
                "image_url": photo["image_url"],  # ใช้ image_url แทน url
                "description": photo.get("description", ""),
                "location_name": photo.get("location_name", ""),
                "created_at": photo.get("created_at", photo.get("uploaded_at", "")),
                "latitude": photo.get("latitude"),
                "longitude": photo.get("longitude")
            }
            
            # Add location data if available
            if photo.get("latitude") and photo.get("longitude"):
                upload_item["location"] = {
                    "lat": float(photo["latitude"]),
                    "lng": float(photo["longitude"])
                }
            
            uploads.append(upload_item)
        
        return {
            "uploads": uploads,
            "count": len(uploads)
        }
        
    except Exception as e:
        print(f"Error getting user uploads for user {user_id}: {e}")
        # Return empty list if there's an error
        return {"uploads": [], "count": 0}
