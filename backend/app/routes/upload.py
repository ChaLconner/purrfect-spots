"""
Upload routes for cat photo uploads with location information
Enhanced with security features: rate limiting, input sanitization, security logging
"""

import inspect
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import config
from app.dependencies import get_cat_detection_service, get_gallery_service, get_quota_service, get_storage_service
from app.limiter import get_upload_limit, upload_limiter

limiter = upload_limiter  # Alias for backward compatibility with tests
from app.logger import logger, sanitize_log_value
from app.middleware.auth_middleware import get_current_user
from app.schemas.gallery import UploadQuotaResponse
from app.schemas.user import User
from app.services.cat_detection_service import CatDetectionService
from app.services.gallery_service import GalleryService
from app.services.quota_service import QuotaService, QuotaServiceUnavailable
from app.services.redis_service import RedisLockError, redis_service
from app.services.storage_service import StorageService
from app.utils import cache as cache_utils
from app.utils.cache import invalidate_after_upload
from app.utils.exceptions import ExternalServiceError
from app.utils.file_processing import process_uploaded_image, validate_coordinates, validate_location_data
from app.utils.security import (
    log_security_event,
    sanitize_tags,
)
from app.utils.upload_verification import verify_upload_verification_token

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_QUOTA_UNAVAILABLE = "Upload quota service unavailable"
UPLOAD_LIMIT_REACHED = "Daily upload limit reached. Upgrade to Pro for more uploads."
UPLOAD_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"description": "Invalid upload data or no cats detected"},
    429: {"description": "Daily upload limit reached"},
    500: {"description": "Internal Server Error"},
    503: {"description": "Upload quota or verification service unavailable"},
}


@dataclass(frozen=True)
class UploadFormData:
    file: UploadFile
    lat: str
    lng: str
    location_name: str
    description: str | None
    tags: str | None
    cat_detection_data: str | None
    verification_token: str | None
    location_blurred: str


def _get_upload_form_data(
    file: Annotated[UploadFile, File(...)],
    lat: Annotated[str, Form(...)],
    lng: Annotated[str, Form(...)],
    location_name: Annotated[str, Form(...)],
    description: Annotated[str | None, Form()] = "",
    tags: Annotated[str | None, Form()] = None,
    cat_detection_data: Annotated[str | None, Form()] = None,
    verification_token: Annotated[str | None, Form()] = None,
    location_blurred: Annotated[str, Form()] = "false",
) -> UploadFormData:
    """Collect multipart upload fields without expanding the route signature."""
    return UploadFormData(
        file=file,
        lat=lat,
        lng=lng,
        location_name=location_name,
        description=description,
        tags=tags,
        cat_detection_data=cat_detection_data,
        verification_token=verification_token,
        location_blurred=location_blurred,
    )


# Compatibility exports for integrations that patch the legacy invalidation
# tasks. Uploads now use one coalesced invalidation task below.
invalidate_gallery_cache = cache_utils.invalidate_gallery_cache
invalidate_tags_cache = cache_utils.invalidate_tags_cache


# Alias for backward compatibility with tests
def parse_tags(tags_json: str | None) -> list[str]:
    """Backward compatible alias for parse_and_sanitize_tags"""
    return parse_and_sanitize_tags(tags_json)


# local dependency functions removed


def parse_and_sanitize_tags(tags_json: str | None) -> list[str]:
    """Parse and sanitize tags from JSON string with security measures."""
    if not tags_json:
        return []

    try:
        tag_list = json.loads(tags_json)
        if tag_list and isinstance(tag_list, list):
            # Use security utility for sanitization
            return sanitize_tags(tag_list)
    except (ValueError, TypeError) as e:
        logger.warning("Failed to parse tags: %s", e)

    return []


def format_tags_for_description(tags: list[str], description: str) -> str:
    """Append hashtags to description for backward compatibility."""
    if not tags:
        return description

    hashtag_string = " ".join([f"#{tag}" for tag in tags])
    if description:
        return f"{description}\n\n{hashtag_string}"
    return hashtag_string


from pydantic import ValidationError

from app.schemas.cat_detection import CatDetectionResult


def validate_cat_detection_data(cat_data: dict) -> bool:
    """
    Validate cat detection data structure and values using Pydantic model.

    Returns:
        True if valid, False otherwise
    """
    if not cat_data or not isinstance(cat_data, dict):
        return False

    try:
        # Use simple validation against the schema
        # We need to handle potential missing optional fields loosely if client sends partial data,
        # but here we want to ensure the structure is correct.
        CatDetectionResult(**cat_data)
        return True
    except ValidationError:
        return False
    except (ValueError, TypeError):
        return False


async def _perform_server_side_detection(
    file: UploadFile | bytes, detection_service: CatDetectionService, user_id: str, client_cat_data: dict | None
) -> dict[str, Any]:
    """Run server-side cat detection and validate results"""
    # CRITICAL SECURITY FIX: Always perform server-side detection

    # If file is UploadFile (legacy/fallback), reset cursor. If bytes, use directly.
    if isinstance(file, UploadFile):
        await file.seek(0)

    detection_result = await detection_service.detect_cats(file)

    if detection_result.get("service_available") is False or detection_result.get("fallback_active"):
        log_security_event(
            "upload_verification_unavailable",
            user_id=user_id,
            severity="WARNING",
        )
        raise HTTPException(
            status_code=503,
            detail="Cat verification service unavailable. Please try again later.",
        )

    # Log discrepancy if client said "has_cats" but server says "no"
    if client_cat_data and client_cat_data.get("has_cats") and not detection_result.get("has_cats"):
        log_security_event(
            "detection_mismatch",
            user_id=user_id,
            details={
                "client_result": sanitize_log_value(client_cat_data),
                "server_result": sanitize_log_value(str(detection_result)[:200]),
            },
            severity="WARNING",
        )

    # Reject if no cats found by server
    if not detection_result.get("has_cats", False):
        log_security_event(
            "upload_rejected_no_cats",
            user_id=user_id,
            details={"detection_result": sanitize_log_value(str(detection_result)[:200])},
            severity="INFO",
        )
        raise HTTPException(
            status_code=400,
            detail="No cats detected in the image. Please upload a photo containing cats.",
        )

    return {
        "has_cats": detection_result.get("has_cats"),
        "cat_count": detection_result.get("cat_count", 0),
        "confidence": detection_result.get("confidence", 0),
        "suitable_for_cat_spot": detection_result.get("suitable_for_cat_spot", False),
        "cats_detected": detection_result.get("cats_detected", []),
        "detection_timestamp": datetime.now().isoformat(),
        "detection_source": "server",
    }


@asynccontextmanager
async def _upload_quota_lock(user_id: str) -> AsyncIterator[None]:
    """Hold the per-user admission lock only around quota and persistence work."""
    try:
        async with redis_service.lock(f"quota:upload:{user_id}", ttl=30, wait_timeout=15):
            yield
    except RedisLockError as lock_error:
        logger.error("Upload quota lock unavailable for %s: %s", user_id, lock_error)
        raise HTTPException(status_code=503, detail=UPLOAD_QUOTA_UNAVAILABLE) from lock_error


async def _ensure_upload_quota(quota_service: QuotaService, user_id: str, is_pro: bool) -> None:
    """Check quota under a short lock; expensive upload work runs outside the lock."""
    async with _upload_quota_lock(user_id):
        allowed = await quota_service.check_quota(user_id, is_pro)

    if not allowed:
        log_security_event("quota_exceeded", user_id=user_id, severity="WARNING")
        raise HTTPException(status_code=429, detail=UPLOAD_LIMIT_REACHED)


async def _reserve_or_check_upload_quota(
    quota_service: QuotaService, user_id: str, is_pro: bool
) -> tuple[str | None, bool]:
    """Use atomic DB reservations, retaining a compatibility path for legacy test doubles."""
    reserve_method = getattr(quota_service, "reserve_upload_quota", None)
    if callable(reserve_method):
        result = reserve_method(user_id, is_pro)
        if inspect.isawaitable(result):
            try:
                reservation_id = await result
            except QuotaServiceUnavailable as exc:
                raise HTTPException(status_code=503, detail=UPLOAD_QUOTA_UNAVAILABLE) from exc
            if not reservation_id:
                log_security_event("quota_exceeded", user_id=user_id, severity="WARNING")
                raise HTTPException(
                    status_code=429,
                    detail=UPLOAD_LIMIT_REACHED,
                )
            return str(reservation_id), True

    # Older integrations may provide only check_quota/increment_usage. Keep
    # them safe and compatible until they adopt the reservation contract.
    await _ensure_upload_quota(quota_service, user_id, is_pro)
    return None, False


@router.get("/quota")
async def get_upload_quota(
    current_user: Annotated[User, Depends(get_current_user)],
    quota_service: Annotated[QuotaService, Depends(get_quota_service)],
) -> UploadQuotaResponse:
    """Get current user upload quota status."""
    return await quota_service.get_user_quota_status(str(current_user.id), current_user.is_pro)


@dataclass(frozen=True)
class PreparedUploadData:
    latitude: float
    longitude: float
    location_name: str
    description: str
    tags: list[str]
    location_blurred: bool


def _prepare_upload_data(form_data: UploadFormData) -> PreparedUploadData:
    latitude, longitude = validate_coordinates(form_data.lat, form_data.lng)
    cleaned_location_name, cleaned_description = validate_location_data(form_data.location_name, form_data.description)
    parsed_tags = parse_and_sanitize_tags(form_data.tags)
    if parsed_tags:
        cleaned_description = format_tags_for_description(parsed_tags, cleaned_description)
    return PreparedUploadData(
        latitude=latitude,
        longitude=longitude,
        location_name=cleaned_location_name,
        description=cleaned_description,
        tags=parsed_tags,
        location_blurred=str(form_data.location_blurred).lower() in ["true", "1", "yes"],
    )


def _parse_client_detection_data(cat_detection_data: str | None) -> dict | None:
    if not cat_detection_data:
        return None
    try:
        client_cat_data = json.loads(cat_detection_data)
        logger.debug("Client-side detection data received")
        return cast(dict[str, Any], client_cat_data)
    except json.JSONDecodeError:
        logger.warning("Failed to parse client detection data: %s", sanitize_log_value(cat_detection_data))
        return None


async def _resolve_upload_detection(
    verification_token: str | None,
    contents: bytes,
    user_id: str,
    detection_service: CatDetectionService,
    client_cat_data: dict | None,
) -> dict[str, Any]:
    verified_detection = None
    if verification_token:
        verified_detection = await verify_upload_verification_token(verification_token, contents, user_id)
    if verified_detection:
        return {
            **verified_detection,
            "detection_timestamp": datetime.now().isoformat(),
            "detection_source": "verified_token",
        }
    return await _perform_server_side_detection(contents, detection_service, user_id, client_cat_data)


async def _renew_upload_reservation(
    quota_service: QuotaService, reservation_id: str | None, uses_reservation: bool
) -> None:
    if not (uses_reservation and reservation_id):
        return
    try:
        renewed = await quota_service.renew_upload_quota(reservation_id)
    except QuotaServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=UPLOAD_QUOTA_UNAVAILABLE) from exc
    if not renewed:
        raise HTTPException(status_code=503, detail="Upload quota reservation expired")


def _get_upload_status(cat_data: dict[str, Any]) -> str:
    confidence_val = float(cat_data.get("confidence", 0))
    confidence_pct = confidence_val * 100.0 if confidence_val <= 1.0 else confidence_val
    return "approved" if confidence_pct >= 60.0 else "pending_review"


async def _upload_to_storage(
    storage_service: StorageService,
    contents: bytes,
    content_type: str,
    file_extension: str,
    user_id: str,
) -> str:
    try:
        return await storage_service.upload_file(
            file_content=contents,
            content_type=content_type,
            file_extension=file_extension,
        )
    except ExternalServiceError as s3_error:
        logger.error("S3 upload failed: %s", s3_error)
        log_security_event(
            "s3_upload_failed",
            user_id=user_id,
            details={"error": sanitize_log_value(str(s3_error)[:200])},
            severity="ERROR",
        )
        raise HTTPException(status_code=500, detail="Failed to upload image") from s3_error


def _build_photo_data(
    current_user: User,
    prepared: PreparedUploadData,
    image_url: str,
    status: str,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "location_name": prepared.location_name,
        "description": prepared.description if prepared.description else None,
        "tags": prepared.tags if prepared.tags else [],
        "latitude": prepared.latitude,
        "longitude": prepared.longitude,
        "image_url": image_url,
        "uploaded_at": datetime.now().isoformat(),
        "location_blurred": prepared.location_blurred,
        "status": status,
    }


async def _save_photo_record(
    gallery_service: GalleryService,
    quota_service: QuotaService,
    photo_data: dict[str, Any],
    user_id: str,
    is_pro: bool,
    uses_reservation: bool,
) -> tuple[dict[str, Any] | None, bool, Exception | None]:
    if uses_reservation:
        try:
            return await gallery_service.save_photo(photo_data), True, None
        except Exception as database_error:
            return None, True, database_error

    async with _upload_quota_lock(user_id):
        quota_allowed = await quota_service.check_quota(user_id, is_pro)
        if not quota_allowed:
            return None, False, None
        try:
            created_photo = await gallery_service.save_photo(photo_data)
            await quota_service.increment_usage(user_id)
            return created_photo, True, None
        except Exception as database_error:
            return None, True, database_error


async def _delete_uploaded_file(storage_service: StorageService, image_url: str, context: str) -> None:
    try:
        await storage_service.delete_file(image_url)
    except Exception as cleanup_error:
        logger.error("Failed to delete S3 file %s: %s", context, cleanup_error)


async def _complete_upload_reservation(
    quota_service: QuotaService, reservation_id: str | None, uses_reservation: bool
) -> None:
    if not (uses_reservation and reservation_id):
        return
    try:
        completed = await quota_service.complete_upload_quota(reservation_id)
        if not completed:
            logger.warning("Upload quota reservation %s was not marked consumed", reservation_id)
    except QuotaServiceUnavailable:
        logger.error("Upload quota completion unavailable for reservation %s", reservation_id)


@router.post("/cat", responses=UPLOAD_ERROR_RESPONSES)
@upload_limiter.limit(get_upload_limit)  # Uses default_limits=[get_upload_limit] defined in upload_limiter
async def upload_cat_photo(
    request: Request,  # Required for rate limiting
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    gallery_service: Annotated[GalleryService, Depends(get_gallery_service)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    quota_service: Annotated[QuotaService, Depends(get_quota_service)],
    form_data: Annotated[UploadFormData, Depends(_get_upload_form_data)],
) -> JSONResponse:
    """
    Upload cat photo with location information.

    Security features:
    - Rate limited: 5 requests per minute
    - Magic bytes validation for file type
    - Input sanitization for all text fields
    - Security event logging

    The image is automatically optimized (resized/compressed) before upload to S3.

    Raises:
        HTTPException: 400 - If no cats are detected in image.
        HTTPException: 429 - If daily upload limit is reached.
        HTTPException: 500 - If image processing or upload fails.
    """
    user_id = str(current_user.id)
    reservation_id: str | None = None
    uses_reservation = False
    photo_saved = False

    try:
        # Log upload attempt
        log_security_event(
            "cat_photo_upload_started",
            user_id=user_id,
            details={
                "filename": sanitize_log_value(form_data.file.filename),
                "location_name": sanitize_log_value(form_data.location_name[:50])
                if form_data.location_name
                else "unknown",
            },
        )

        prepared = _prepare_upload_data(form_data)

        reservation_id, uses_reservation = await _reserve_or_check_upload_quota(
            quota_service, user_id, current_user.is_pro
        )

        contents, content_type, file_extension = await process_uploaded_image(
            form_data.file,
            max_size_mb=config.UPLOAD_MAX_SIZE_MB,
            optimize=True,
            max_dimension=config.UPLOAD_MAX_DIMENSION,
            user_id=user_id,
        )

        cat_data = await _resolve_upload_detection(
            form_data.verification_token,
            contents,
            user_id,
            detection_service,
            _parse_client_detection_data(form_data.cat_detection_data),
        )

        await _renew_upload_reservation(quota_service, reservation_id, uses_reservation)
        image_url = await _upload_to_storage(storage_service, contents, content_type, file_extension, user_id)
        photo_data = _build_photo_data(current_user, prepared, image_url, _get_upload_status(cat_data))
        created_photo, quota_allowed, database_error = await _save_photo_record(
            gallery_service,
            quota_service,
            photo_data,
            user_id,
            current_user.is_pro,
            uses_reservation,
        )

        if not quota_allowed:
            log_security_event("quota_exceeded", user_id=user_id, severity="WARNING")
            await _delete_uploaded_file(storage_service, image_url, "after quota rejection")
            raise HTTPException(status_code=429, detail=UPLOAD_LIMIT_REACHED)

        if database_error is not None or created_photo is None:
            logger.error("Database insert failed: %s. Rolling back S3 upload.", database_error)
            await _delete_uploaded_file(storage_service, image_url, "during DB rollback")

            log_security_event(
                "upload_transaction_rollback",
                user_id=user_id,
                details={
                    "error": sanitize_log_value(str(database_error)[:200]),
                    "image_url": sanitize_log_value(image_url),
                },
                severity="ERROR",
            )
            raise HTTPException(status_code=500, detail="Failed to save cat photo")

        photo_saved = True
        await _complete_upload_reservation(quota_service, reservation_id, uses_reservation)

        # Invalidate gallery, tags and user photos cache after new upload in background
        background_tasks.add_task(invalidate_after_upload)

        log_security_event(
            "cat_photo_upload_success",
            user_id=user_id,
            details={
                "photo_id": created_photo["id"],
                "location_name": prepared.location_name,
            },
        )

        logger.info("Cat photo uploaded successfully: %r by %r", created_photo["id"], current_user.email)

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Cat photo uploaded successfully!",
                "photo": {
                    "id": created_photo["id"],
                    "location_name": created_photo["location_name"],
                    "location": {
                        "latitude": created_photo["latitude"],
                        "longitude": created_photo["longitude"],
                    },
                    "image_url": created_photo["image_url"],
                    "uploaded_at": created_photo["uploaded_at"],
                },
                "cat_detection": cat_data,
                "uploaded_by": current_user.email,
            },
            headers={"Content-Type": "application/json"},
        )

    except HTTPException:
        raise
    except Exception as e:
        # Catch-all for any other unexpected errors during upload process
        logger.error("Upload error: %s", e, exc_info=True)
        log_security_event(
            "upload_error",
            user_id=user_id,
            details={"error": "An internal upload error occurred"},
            severity="ERROR",
        )
        raise HTTPException(status_code=500, detail="Upload failed due to an internal error")
    finally:
        if reservation_id and not photo_saved:
            try:
                await quota_service.release_upload_quota(reservation_id)
            except Exception as release_error:
                logger.error("Failed to release upload quota reservation: %s", release_error)


# Test endpoint removed for security
