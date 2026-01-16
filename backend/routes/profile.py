"""
User profile management routes
"""


from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from dependencies import get_supabase_client
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from services.storage_service import StorageService
from user_models.user import User
from utils.file_processing import process_uploaded_image

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    bio: str | None = None
    picture: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


from services.auth_service import AuthService
from services.gallery_service import GalleryService


def get_auth_service(supabase=Depends(get_supabase_client)):
    return AuthService(supabase)


def get_gallery_service(supabase=Depends(get_supabase_client)):
    return GalleryService(supabase)


def get_storage_service() -> StorageService:
    return StorageService()


@router.put("/")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Update user profile information
    """
    try:
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

        # Update via service
        try:
            updated_user = auth_service.update_user_profile(
                current_user.id, update_data
            )
        except ValueError:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user["id"],
                "email": updated_user["email"],
                "name": updated_user["name"],
                "picture": updated_user.get("picture"),
                "bio": updated_user.get("bio"),
                "created_at": updated_user["created_at"],
            },
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error updating profile: {e!s}")  # Log the error
        raise HTTPException(
            status_code=500, detail="Failed to update profile due to an internal error"
        )


@router.get("/")
async def get_profile(
    current_user: User = Depends(get_current_user_from_credentials),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Get current user profile
    """
    try:
        user = auth_service.get_user_by_id(current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "bio": user.bio,
            "created_at": user.created_at,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {e!s}")


@router.get("/uploads")
async def get_user_uploads(
    current_user: User = Depends(get_current_user_from_credentials),
    gallery_service: GalleryService = Depends(get_gallery_service),
):
    """
    Get all uploads by current user - filtered by user_id
    """
    try:
        photos = gallery_service.get_user_photos(current_user.id)

        # Format data
        uploads = []
        for photo in photos:
            upload_item = {
                "id": photo["id"],
                "image_url": photo["image_url"],
                "description": photo.get("description", ""),
                "location_name": photo.get("location_name", ""),
                "uploaded_at": photo.get("uploaded_at", ""),
                "latitude": photo.get("latitude"),
                "longitude": photo.get("longitude"),
            }

            if photo.get("latitude") and photo.get("longitude"):
                upload_item["location"] = {
                    "lat": float(photo["latitude"]),
                    "lng": float(photo["longitude"]),
                }

            uploads.append(upload_item)

        return {"uploads": uploads, "count": len(uploads)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get uploads: {e!s}")


@router.post("/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_from_credentials),
    auth_service: AuthService = Depends(get_auth_service),
    storage_service: StorageService = Depends(get_storage_service),
):
    """
    Upload and update profile picture
    """
    try:
        # Process image
        contents, content_type, file_extension = await process_uploaded_image(
            file,
            max_size_mb=5,
            optimize=True,
            max_dimension=500,  # Smaller dimension for avatars
        )

        # Upload to S3 (or Supabase Storage)
        image_url = await storage_service.upload_file(
            file_content=contents,
            content_type=content_type,
            file_extension=file_extension,
            folder="avatars",
        )

        # Update user profile
        auth_service.update_user_profile(current_user.id, {"picture": image_url})

        return {"message": "Profile picture updated", "picture": image_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile picture upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")


@router.put("/password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Change user password
    """
    try:
        success = auth_service.change_password(
            current_user.id, password_data.current_password, password_data.new_password
        )

        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to change password (check current password)",
            )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(status_code=500, detail="An error occurred")
