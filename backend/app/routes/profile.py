"""
User profile management routes
"""

import re
from typing import Annotated, Any, cast

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Path, Response, UploadFile
from starlette.requests import Request

from app.config import config
from app.dependencies import (
    get_admin_gallery_service,
    get_async_supabase_admin_client,
    get_auth_service,
    get_storage_service,
)
from app.limiter import auth_limiter, get_api_limit, get_strict_limit, limiter, strict_limiter
from app.logger import logger, sanitize_log_value
from app.middleware.auth_middleware import get_current_user_from_credentials
from app.schemas.location import CatLocation
from app.schemas.user import User
from app.utils.avatar import sanitize_avatar_url
from app.utils.cache import invalidate_gallery_cache
from app.utils.file_processing import process_uploaded_image
from app.utils.location_utils import protect_photo_locations

router = APIRouter(prefix="/profile", tags=["Profile"])

USER_NOT_FOUND_DETAIL = "User not found"
PUBLIC_PROFILE_CACHE_CONTROL = "public, max-age=60"


from app.schemas.profile import (
    AccountDeletionResponse,
    ChangePasswordRequest,
    PasswordChangeResponse,
    PhotoDeleteResponse,
    PhotoUpdateResponse,
    ProfilePictureResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
    PublicProfileBundleResponse,
    PublicProfileResponse,
    UpdatePhotoRequest,
    UploadsResponse,
)
from app.services.auth_service import AuthService
from app.services.gallery_service import GalleryService
from app.services.storage_service import StorageService

# Services are now imported from dependencies


def _build_profile_update_data(profile_data: ProfileUpdateRequest) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "name": profile_data.name,
            "username": profile_data.username,
            "bio": profile_data.bio,
            "picture": profile_data.picture,
        }.items()
        if value is not None
    }


def _validate_profile_picture(update_data: dict[str, Any]) -> None:
    if "picture" not in update_data:
        return

    from app.utils.avatar import validate_avatar_url

    try:
        validated_picture = validate_avatar_url(update_data["picture"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if validated_picture is None:
        raise HTTPException(status_code=400, detail="Avatar URL cannot be null in this update")
    update_data["picture"] = validated_picture


async def _validate_profile_username(
    update_data: dict[str, Any], current_user: User, auth_service: AuthService
) -> None:
    if "username" not in update_data:
        return

    username = update_data["username"]
    if not re.match(r"^(?a:\w){3,30}$", username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3-30 characters and contain only letters, numbers, and underscores",
        )
    if username.lower() == (current_user.username or "").lower():
        return

    existing_user = await auth_service.user_service.get_user_by_username(username)
    if existing_user:
        raise HTTPException(status_code=409, detail="Username already taken")


async def _prepare_profile_update(
    profile_data: ProfileUpdateRequest,
    current_user: User,
    auth_service: AuthService,
) -> dict[str, Any]:
    from app.utils.security import sanitize_text

    update_data = _build_profile_update_data(profile_data)
    _validate_profile_picture(update_data)

    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided for update")
    if "name" in update_data:
        update_data["name"] = sanitize_text(update_data["name"], max_length=100)
    await _validate_profile_username(update_data, current_user, auth_service)
    if update_data.get("bio"):
        update_data["bio"] = sanitize_text(update_data["bio"], max_length=500)
    return update_data


@router.put(
    "",
    responses={
        400: {"description": "Bad Request"},
        404: {"description": "Not Found"},
        409: {"description": "Conflict"},
        500: {"description": "Internal Server Error"},
    },
)
@strict_limiter.limit("5/minute")
async def update_profile(
    request: Request,
    profile_data: ProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ProfileUpdateResponse:
    """
    Update user profile information

    Raises:
        HTTPException: 400 - If no update data provided or invalid username.
        HTTPException: 404 - If user not found.
        HTTPException: 409 - If username already taken.
        HTTPException: 500 - If profile update fails.
    """
    try:
        update_data = await _prepare_profile_update(profile_data, current_user, auth_service)
        try:
            updated_user = await auth_service.update_user_profile(current_user.id, update_data)
        except ValueError:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND_DETAIL)

        return ProfileUpdateResponse(
            message="Profile updated successfully",
            user={
                "id": updated_user["id"],
                "email": updated_user["email"],
                "name": updated_user["name"],
                "username": updated_user.get("username"),
                "picture": sanitize_avatar_url(updated_user.get("picture")),
                "bio": updated_user.get("bio"),
                "created_at": updated_user["created_at"],
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error updating profile for user %s: %s", sanitize_log_value(current_user.id), e)
        raise HTTPException(status_code=500, detail="Failed to update profile due to an internal error")


@router.get(
    "",
    responses={404: {"description": USER_NOT_FOUND_DETAIL}, 500: {"description": "Internal Server Error"}},
)
@limiter.limit(get_api_limit)
async def get_profile(
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ProfileResponse:
    """
    Get current user profile

    Raises:
        HTTPException: 404 - If user not found.
        HTTPException: 500 - If profile fetch fails.
    """
    # Prevent caching of profile data
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    try:
        user = await auth_service.get_user_by_id(current_user.id)
        if not user:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND_DETAIL)

        return ProfileResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            name=user.name,
            picture=sanitize_avatar_url(user.picture),
            bio=user.bio,
            created_at=user.created_at,
            is_pro=user.is_pro,
        )

    except Exception as e:
        logger.error("Failed to get profile for user %s: %s", sanitize_log_value(current_user.id), e)
        raise HTTPException(status_code=500, detail="Failed to get profile")


# GalleryService is imported from dependencies


UsernameOrIdPath = Annotated[
    str,
    Path(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="User UUID or Username endpoint identifier",
    ),
]

from app.routes.gallery import PhotoIdPath, schedule_photo_deletion


async def resolve_user_by_identifier(
    identifier: UsernameOrIdPath, auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> Any:  # Assuming User object is returned
    """Resolve a user profile by ID or username.

    Args:
        identifier: User UUID or username.
        auth_service: Service to interact with the authentication system.

    Returns:
        The user profile.

    Raises:
        HTTPException: 404 - If user not found.
    """
    import uuid

    try:
        is_uuid = bool(uuid.UUID(identifier))
    except ValueError:
        is_uuid = False

    user = None
    if is_uuid:
        user = await auth_service.get_user_by_id(identifier)

    # If not found by ID or not a UUID, try by username
    if not user:
        user = await auth_service.user_service.get_user_by_username(identifier)

    if not user:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND_DETAIL)

    return user


def _public_profile_response(user: Any) -> PublicProfileResponse:
    return PublicProfileResponse(
        id=user.id,
        name=user.name,
        picture=sanitize_avatar_url(user.picture),
        bio=user.bio,
        created_at=user.created_at,
        is_pro=user.is_pro,
    )


def _public_upload_items(photos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    uploads = []
    for photo in photos:
        try:
            uploads.append(
                {
                    "id": photo["id"],
                    "image_url": photo["image_url"],
                    "description": photo.get("description", ""),
                    "location_name": photo.get("location_name", ""),
                    "uploaded_at": photo.get("uploaded_at", ""),
                    "latitude": photo.get("latitude"),
                    "longitude": photo.get("longitude"),
                }
            )
        except Exception as e:
            logger.debug("Skipping malformed photo %r: %s", photo.get("id"), e)
            continue

    return protect_photo_locations(uploads)


@router.get("/public/{identifier}", responses={500: {"description": "Internal Server Error"}})
def get_public_profile(
    response: Response,
    user: Annotated[Any, Depends(resolve_user_by_identifier)],
) -> PublicProfileResponse:
    """
    Get public user profile by ID or username

    Raises:
        HTTPException: 500 - If profile fetch fails.
    """
    response.headers["Cache-Control"] = PUBLIC_PROFILE_CACHE_CONTROL
    try:
        return _public_profile_response(user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get public profile for %s: %s", sanitize_log_value(user.id), e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user profile")


@router.get(
    "/public/{identifier}/bundle",
    responses={500: {"description": "Internal Server Error"}},
)
async def get_public_profile_bundle(
    response: Response,
    user: Annotated[Any, Depends(resolve_user_by_identifier)],
    gallery_service: Annotated[GalleryService, Depends(get_admin_gallery_service)],
) -> PublicProfileBundleResponse:
    """Get public profile and uploads in one request."""
    response.headers["Cache-Control"] = PUBLIC_PROFILE_CACHE_CONTROL
    try:
        photos = await gallery_service.get_user_photos(user.id, include_unapproved=False)
        uploads = _public_upload_items(photos)
        return PublicProfileBundleResponse(
            profile=_public_profile_response(user),
            uploads=uploads,
            count=len(uploads),
        )
    except Exception as e:
        logger.error("Failed to get public profile bundle for %s: %s", sanitize_log_value(user.id), e)
        raise HTTPException(status_code=500, detail="Failed to retrieve user profile")


@router.get(
    "/public/{identifier}/uploads",
    responses={500: {"description": "Internal Server Error"}},
)
async def get_public_user_uploads(
    response: Response,
    user: Annotated[Any, Depends(resolve_user_by_identifier)],
    gallery_service: Annotated[GalleryService, Depends(get_admin_gallery_service)],
) -> UploadsResponse:
    """
    Get public uploads by user_id or username

    Raises:
        HTTPException: 500 - If uploads fetch fails.
    """
    response.headers["Cache-Control"] = PUBLIC_PROFILE_CACHE_CONTROL
    try:
        user_id = user.id
        photos = await gallery_service.get_user_photos(user_id, include_unapproved=False)
        uploads = _public_upload_items(photos)

        return UploadsResponse(uploads=uploads, count=len(uploads))

    except Exception as e:
        logger.error("Failed to get uploads for user %s: %s", sanitize_log_value(user.id), e)
        raise HTTPException(status_code=500, detail="Failed to get uploads")


@router.get("/uploads", responses={500: {"description": "Internal Server Error"}})
async def get_user_uploads(
    response: Response,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    gallery_service: Annotated[GalleryService, Depends(get_admin_gallery_service)],
) -> UploadsResponse:
    """
    Get all uploads by current user - filtered by user_id

    Raises:
        HTTPException: 500 - If uploads fetch fails.
    """
    # Prevent caching of user uploads
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    try:
        photos = await gallery_service.get_user_photos(current_user.id, include_unapproved=True)

        # Use central schema for consistent data structure
        uploads = [CatLocation(**photo).model_dump() for photo in photos]

        return UploadsResponse(uploads=uploads, count=len(uploads))

    except Exception as e:
        logger.error("Failed to get uploads for user %s: %s", sanitize_log_value(current_user.id), e, exc_info=True)
        detail = f"Internal Server Error: {e!s}" if config.ENVIRONMENT == "development" else "Internal Server Error"
        raise HTTPException(status_code=500, detail=detail)


@router.post("/picture", responses={500: {"description": "Internal Server Error"}})
@strict_limiter.limit(get_strict_limit)
async def upload_profile_picture(
    request: Request,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
) -> ProfilePictureResponse:
    """
    Upload and update profile picture

    Raises:
        HTTPException: 500 - If image upload or processing fails.
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
        image_url = await storage_service.upload_file(
            file_content=contents,
            content_type=content_type,
            file_extension=file_extension,
            folder="avatars",
        )

        # NOTE: We no longer update the auth_service here.
        # The frontend will receive this URL and send it back in the final /profile PUT request.

        return ProfilePictureResponse(message="Photo uploaded successfully", picture=image_url)

    except HTTPException:
        raise
    except Exception:
        logger.error("Profile picture upload failed")
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")


@router.put(
    "/password",
    responses={400: {"description": "Bad Request"}, 500: {"description": "Internal Server Error"}},
)
@auth_limiter.limit("5/minute")
async def change_password(
    request: Request,
    password_data: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> PasswordChangeResponse:
    """
    Change user password

    Raises:
        HTTPException: 400 - If password change fails due to invalid current password.
        HTTPException: 500 - If password change fails due to internal system error.
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
            return PasswordChangeResponse(message="Password changed successfully")
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


@router.put(
    "/uploads/{photo_id}",
    responses={
        400: {"description": "Bad Request"},
        403: {"description": "Unauthorized"},
        404: {"description": "Not Found"},
        500: {"description": "Internal Server Error"},
    },
)
async def update_user_photo(
    photo_id: PhotoIdPath,
    update_data: UpdatePhotoRequest,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    gallery_service: Annotated[GalleryService, Depends(get_admin_gallery_service)],
) -> PhotoUpdateResponse:
    """
    Update a user's upload photo details (description, etc)

    Raises:
        HTTPException: 400 - If no valid data provided.
        HTTPException: 403 - If not authorized to update photo.
        HTTPException: 404 - If photo not found.
        HTTPException: 500 - If photo update fails.
    """
    photo_id_str = str(photo_id)
    try:
        # 1. Check ownership
        photo = await gallery_service.get_photo_by_id(photo_id_str, include_unapproved=True)
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")

        if photo["user_id"] != current_user.id:
            from app.utils.security import log_security_event

            log_security_event(
                "unauthorized_update_attempt",
                user_id=current_user.id,
                details={"photo_id": photo_id_str, "owner": photo["user_id"]},
                severity="WARNING",
            )
            raise HTTPException(status_code=403, detail="Not authorized to update this photo")

        # 2. Sanitize Data
        from app.utils.security import sanitize_location_name, sanitize_text

        valid_updates = {}
        if update_data.location_name is not None:
            valid_updates["location_name"] = sanitize_location_name(update_data.location_name)
        if update_data.description is not None:
            valid_updates["description"] = sanitize_text(update_data.description, max_length=1000)

        if not valid_updates:
            raise HTTPException(status_code=400, detail="No valid data provided")

        # 3. Update
        # Use admin service because we already verified ownership
        admin_supabase = await get_async_supabase_admin_client()
        await admin_supabase.table("cat_photos").update(valid_updates).eq("id", photo_id_str).execute()

        # Invalidate cache to ensure updates are reflected immediately
        await invalidate_gallery_cache()

        from app.utils.security import log_security_event

        log_security_event(
            "photo_updated",
            user_id=current_user.id,
            details={"photo_id": photo_id_str, "updates": list(valid_updates.keys())},
        )

        return PhotoUpdateResponse(message="Photo updated successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update photo %s: %s", sanitize_log_value(photo_id_str), str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update photo")


@router.delete(
    "/uploads/{photo_id}",
    status_code=202,
    responses={404: {"description": "Not Found"}, 500: {"description": "Internal Server Error"}},
)
async def delete_user_photo(
    photo_id: PhotoIdPath,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    gallery_service: Annotated[GalleryService, Depends(get_admin_gallery_service)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
) -> PhotoDeleteResponse:
    """
    Delete a user's uploaded photo with background processing

    Raises:
        HTTPException: 404 - If photo not found or access denied.
        HTTPException: 500 - If deletion fails.
    """
    photo_id_str = str(photo_id)
    try:
        await schedule_photo_deletion(photo_id_str, current_user.id, gallery_service, storage_service, background_tasks)
        return PhotoDeleteResponse(message="Deletion scheduled")

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to delete photo %s", sanitize_log_value(photo_id_str))
        raise HTTPException(status_code=500, detail="Failed to delete photo")


async def _execute_account_deletion_action(coro: Any, log_msg: str, detail_msg: str) -> AccountDeletionResponse:
    try:
        return cast(AccountDeletionResponse, await coro)
    except HTTPException:
        raise
    except Exception as e:
        from app.utils.exceptions import ConflictError

        if isinstance(e, ConflictError):
            raise HTTPException(status_code=400, detail=str(e))
        logger.error(log_msg)
        raise HTTPException(status_code=500, detail=detail_msg)


@router.post(
    "/delete-request",
    responses={400: {"description": "Conflict/Bad Request"}, 500: {"description": "Internal Server Error"}},
)
@auth_limiter.limit("5/minute")
async def request_account_deletion(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccountDeletionResponse:
    """
    Request account deletion

    Raises:
        HTTPException: 400 - If delete request already exists or invalid data.
        HTTPException: 500 - If account deletion request fails.
    """
    client_ip = request.client.host if request.client else "unknown"
    return await _execute_account_deletion_action(
        auth_service.user_service.request_account_deletion(user_id=current_user.id, client_ip=client_ip),
        "Failed to request account deletion",
        "Failed to process account deletion request",
    )


@router.post(
    "/cancel-deletion",
    responses={400: {"description": "Conflict/Bad Request"}, 500: {"description": "Internal Server Error"}},
)
@auth_limiter.limit("5/minute")
async def cancel_account_deletion(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_from_credentials)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AccountDeletionResponse:
    """
    Cancel an ongoing account deletion request

    Raises:
        HTTPException: 400 - If no pending deletion request or invalid data.
        HTTPException: 500 - If cancellation fails.
    """
    return await _execute_account_deletion_action(
        auth_service.user_service.cancel_account_deletion(user_id=current_user.id),
        "Failed to cancel account deletion",
        "Failed to cancel account deletion",
    )
