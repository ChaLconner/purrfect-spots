"""
User profile management routes
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Response, UploadFile
from supabase import Client
from pydantic import BaseModel
from starlette.requests import Request

from config import config
from dependencies import get_supabase_admin_client, get_supabase_client
from limiter import auth_limiter
from logger import logger
from middleware.auth_middleware import get_current_user_from_credentials
from schemas.location import CatLocation
from services.storage_service import StorageService
from user_models.user import User
from utils.cache import invalidate_gallery_cache
from utils.file_processing import process_uploaded_image

router = APIRouter(prefix="/profile", tags=["Profile"])


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    username: str | None = None
    bio: str | None = None
    picture: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


from services.auth_service import AuthService
from services.gallery_service import GalleryService


def get_auth_service(supabase: Client = Depends(get_supabase_client)) -> AuthService:
    return AuthService(supabase)


def get_gallery_service(supabase: Client = Depends(get_supabase_client)) -> GalleryService:
    return GalleryService(supabase)


def get_storage_service() -> StorageService:
    return StorageService()


@router.put("")
@router.put("/")
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """
    Update user profile information
    """
    try:
        # Prepare update data
        update_data = {}
        if profile_data.name is not None:
            update_data["name"] = profile_data.name
        if profile_data.username is not None:
            update_data["username"] = profile_data.username
        if profile_data.bio is not None:
            update_data["bio"] = profile_data.bio
        if profile_data.picture is not None:
            update_data["picture"] = profile_data.picture

        if not update_data:
            raise HTTPException(status_code=400, detail="No data provided for update")

        # Sanitize inputs
        from utils.security import sanitize_text

        if "name" in update_data:
            update_data["name"] = sanitize_text(update_data["name"], max_length=100)
            
        if "username" in update_data:
            username = update_data["username"]
            # Validate username format (alphanumeric + underscore, min 3 chars)
            import re
            if not re.match(r"^[a-zA-Z0-9_]{3,30}$", username):
                raise HTTPException(status_code=400, detail="Username must be 3-30 characters and contain only letters, numbers, and underscores")
            
            # Check for uniqueness if username changed
            if username != current_user.username:
                existing_user = auth_service.user_service.get_user_by_username(username)
                if existing_user:
                     raise HTTPException(status_code=409, detail="Username already taken")

        if "bio" in update_data and update_data["bio"]:
            update_data["bio"] = sanitize_text(update_data["bio"], max_length=500)

        # Update via service
        try:
            updated_user = auth_service.update_user_profile(current_user.id, update_data)
        except ValueError:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user["id"],
                "email": updated_user["email"],
                "name": updated_user["name"],
                "username": updated_user.get("username"),
                "picture": updated_user.get("picture"),
                "bio": updated_user.get("bio"),
                "created_at": updated_user["created_at"],
            },
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.error("Error updating profile")
        raise HTTPException(status_code=500, detail="Failed to update profile due to an internal error")


@router.get("")
@router.get("/")
async def get_profile(
    response: Response,
    current_user: User = Depends(get_current_user_from_credentials),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """
    Get current user profile
    """
    # Prevent caching of profile data
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
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

    except Exception:
        logger.error("Failed to get profile")
        raise HTTPException(status_code=500, detail="Failed to get profile")


def get_admin_gallery_service(supabase: Client = Depends(get_supabase_admin_client)) -> GalleryService:
    return GalleryService(supabase)


@router.get("/public/{identifier}")
async def get_public_profile(
    identifier: str,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """
    Get public user profile by ID or username
    """
    response.headers["Cache-Control"] = "public, max-age=60"
    try:
        # Check if identifier looks like a UUID
        is_uuid = False
        try:
            import uuid

            uuid.UUID(identifier)
            is_uuid = True
        except ValueError:
            is_uuid = False

        user = None
        if is_uuid:
            user = auth_service.get_user_by_id(identifier)
        
        # If not found by ID or not a UUID, try by username
        if not user:
            user = auth_service.user_service.get_user_by_username(identifier)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "name": user.name,
            "picture": user.picture,
            "bio": user.bio,
            "created_at": user.created_at,
            "is_pro": user.is_pro,
            # Don't expose email or other sensitive data
        }

    except Exception:
        logger.error(f"Failed to get public profile for {identifier}")
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/public/{identifier}/uploads")
async def get_public_user_uploads(
    identifier: str,
    response: Response,
    gallery_service: GalleryService = Depends(get_admin_gallery_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """
    Get public uploads by user_id or username
    """
    response.headers["Cache-Control"] = "public, max-age=60"
    try:
        # Resolve identifier to user_id
        is_uuid = False
        try:
            import uuid

            uuid.UUID(identifier)
            is_uuid = True
        except ValueError:
            is_uuid = False

        user_id = identifier
        if not is_uuid:
            user = auth_service.user_service.get_user_by_username(identifier)
            if not user:
                 raise HTTPException(status_code=404, detail="User not found")
            user_id = user.id

        photos = await gallery_service.get_user_photos(user_id)

        # Format data
        uploads = []
        for photo in photos:
            try:
                upload_item = {
                    "id": photo["id"],
                    "image_url": photo["image_url"],
                    "description": photo.get("description", ""),
                    "location_name": photo.get("location_name", ""),
                    "uploaded_at": photo.get("uploaded_at", ""),
                    "latitude": photo.get("latitude"),
                    "longitude": photo.get("longitude"),
                }
                uploads.append(upload_item)
            except Exception as e:
                logger.debug(f"Skipping malformed photo {photo.get('id')}: {e}")
                continue

        return {"uploads": uploads, "count": len(uploads)}

    except Exception as e:
        logger.error(f"Failed to get uploads for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get uploads")


@router.get("/uploads")
async def get_user_uploads(
    response: Response,
    current_user: User = Depends(get_current_user_from_credentials),
    gallery_service: GalleryService = Depends(get_admin_gallery_service),
) -> dict[str, Any]:
    """
    Get all uploads by current user - filtered by user_id
    """
    # Prevent caching of user uploads
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    try:
        photos = await gallery_service.get_user_photos(current_user.id)

        # Use central schema for consistent data structure
        uploads = [CatLocation(**photo).dict() for photo in photos]

        return {"uploads": uploads, "count": len(uploads)}

    except Exception as e:
        logger.error("Failed to get uploads for user %s: %s", current_user.id, e, exc_info=True)
        # In development, return the actual error
        detail = f"Internal Server Error: {e!s}" if config.ENVIRONMENT == "development" else "Internal Server Error"
        raise HTTPException(status_code=500, detail=detail)


@router.post("/picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_from_credentials),
    auth_service: AuthService = Depends(get_auth_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> dict[str, str]:
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

        # Upload to Storage
        image_url = storage_service.upload_file(
            file_content=contents,
            content_type=content_type,
            file_extension=file_extension,
            folder="avatars",
        )

        # NOTE: We no longer update the auth_service here.
        # The frontend will receive this URL and send it back in the final /profile PUT request.

        return {"message": "Photo uploaded successfully", "picture": image_url}

    except HTTPException:
        raise
    except Exception:
        logger.error("Profile picture upload failed")
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")


@router.put("/password")
@auth_limiter.limit("5/minute")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    Change user password
    """
    # Extract client info for audit log (removed unused ip/user_agent)

    # Audit log: Attempt
    logger.info("[AUDIT] Password change attempt")

    try:
        success = await auth_service.change_password(
            current_user.id, password_data.current_password, password_data.new_password
        )

        if success:
            # Audit log: Success
            logger.info("[AUDIT] Password change SUCCESS")
            return {"message": "Password changed successfully"}
        # Audit log: Failure (Logic)
        logger.warning("[AUDIT] Password change FAILED (logic)")
        raise HTTPException(
            status_code=400,
            detail="Failed to change password (check current password)",
        )

    except HTTPException:
        # Audit log: Failure (Validation/Auth)
        logger.warning("[AUDIT] Password change FAILED (auth)")
        raise
    except ValueError:
        # Audit log: Failure (Specific value error)
        logger.warning("[AUDIT] Password change FAILED (validation)")
        raise HTTPException(status_code=400, detail="Invalid password data")
    except Exception:
        # Audit log: Failure (System error)
        logger.error("[AUDIT] Password change ERROR")
        raise HTTPException(status_code=500, detail="An error occurred")


class UpdatePhotoRequest(BaseModel):
    location_name: str | None = None
    description: str | None = None


@router.put("/uploads/{photo_id}")
async def update_user_photo(
    photo_id: str,
    update_data: UpdatePhotoRequest,
    current_user: User = Depends(get_current_user_from_credentials),
    gallery_service: GalleryService = Depends(get_admin_gallery_service),
) -> dict[str, str]:
    """Update a user's upload photo details (description, etc)"""
    try:
        # 1. Check ownership
        photo = await gallery_service.get_photo_by_id(photo_id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        if photo["user_id"] != current_user.id:
            from utils.security import log_security_event

            log_security_event(
                "unauthorized_update_attempt",
                user_id=current_user.id,
                details={"photo_id": photo_id, "owner": photo["user_id"]},
                severity="WARNING",
            )
            raise HTTPException(status_code=403, detail="Not authorized to update this photo")

        # 2. Sanitize Data
        from utils.security import sanitize_location_name, sanitize_text

        valid_updates = {}
        if update_data.location_name is not None:
            valid_updates["location_name"] = sanitize_location_name(update_data.location_name)
        if update_data.description is not None:
            valid_updates["description"] = sanitize_text(update_data.description, max_length=1000)

        if not valid_updates:
            raise HTTPException(status_code=400, detail="No valid data provided")

        valid_updates["updated_at"] = datetime.now(timezone.utc).isoformat()

        # 3. Update
        # Use admin service because we already verified ownership
        gallery_service.supabase.table("cat_photos").update(valid_updates).eq("id", photo_id).execute()

        # Invalidate cache to ensure updates are reflected immediately
        await invalidate_gallery_cache()

        from utils.security import log_security_event

        log_security_event(
            "photo_updated",
            user_id=current_user.id,
            details={"photo_id": photo_id, "updates": list(valid_updates.keys())},
        )

        return {"message": "Photo updated successfully"}

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to update photo %s", photo_id)
        raise HTTPException(status_code=500, detail="Failed to update photo")


@router.delete("/uploads/{photo_id}", status_code=202)
async def delete_user_photo(
    photo_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_from_credentials),
    gallery_service: GalleryService = Depends(get_admin_gallery_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> dict[str, str]:
    """Delete a user's uploaded photo with background processing"""
    try:
        # 1. Check ownership using service method
        photo = await gallery_service.verify_photo_ownership(photo_id, current_user.id)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found or access denied")

        # 2. Schedule background deletion (same as gallery route)
        background_tasks.add_task(
            gallery_service.process_photo_deletion,
            photo_id=photo_id,
            image_url=photo.get("image_url") or "",
            user_id=current_user.id,
            storage_service=storage_service
        )

        return {"message": "Deletion scheduled"}

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to delete photo %s", photo_id)
        raise HTTPException(status_code=500, detail="Failed to delete photo")
