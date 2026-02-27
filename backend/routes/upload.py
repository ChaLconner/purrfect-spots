"""
Upload routes for cat photo uploads with location information
Enhanced with security features: rate limiting, input sanitization, security logging
"""

import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from config import config
from dependencies import get_gallery_service, get_quota_service
from exceptions import ExternalServiceError
from limiter import limiter
from logger import logger
from middleware.auth_middleware import get_current_user
from services.cat_detection_service import CatDetectionService, cat_detection_service
from services.gallery_service import GalleryService
from services.quota_service import QuotaService
from services.storage_service import StorageService, storage_service
from utils.cache import invalidate_gallery_cache, invalidate_tags_cache, invalidate_user_cache
from utils.file_processing import process_uploaded_image, validate_coordinates, validate_location_data
from utils.security import (
    log_security_event,
    sanitize_tags,
)

router = APIRouter(prefix="/upload", tags=["Upload"])


# Alias for backward compatibility with tests
def parse_tags(tags_json: str | None) -> list[str]:
    """Backward compatible alias for parse_and_sanitize_tags"""
    return parse_and_sanitize_tags(tags_json)


def get_storage_service() -> StorageService:
    return storage_service


def get_cat_detection_service() -> CatDetectionService:
    return cat_detection_service


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

from schemas.cat_detection import CatDetectionResult


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

    # Log discrepancy if client said "has_cats" but server says "no"
    if client_cat_data and client_cat_data.get("has_cats") and not detection_result.get("has_cats"):
        log_security_event(
            "detection_mismatch",
            user_id=user_id,
            details={
                "client_result": client_cat_data,
                "server_result": str(detection_result)[:200],
            },
            severity="WARNING",
        )

    # Reject if no cats found by server
    if not detection_result.get("has_cats", False):
        log_security_event(
            "upload_rejected_no_cats",
            user_id=user_id,
            details={"detection_result": str(detection_result)[:200]},
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


@router.get("/quota")
async def get_upload_quota(
    current_user: Any = Depends(get_current_user),
    quota_service: QuotaService = Depends(get_quota_service),
) -> dict[str, Any]:
    """Get current user's upload quota status."""
    return await quota_service.get_user_quota_status(str(current_user.id), current_user.is_pro)


@router.post("/cat")
@limiter.limit(config.UPLOAD_RATE_LIMIT)  # Rate limit from config
async def upload_cat_photo(
    request: Request,  # Required for rate limiting
    file: UploadFile = File(...),
    lat: str = Form(...),
    lng: str = Form(...),
    location_name: str = Form(...),
    description: str | None = Form(""),
    tags: str | None = Form(None),
    cat_detection_data: str | None = Form(None),
    location_blurred: str = Form("false"),
    current_user: Any = Depends(get_current_user),
    gallery_service: GalleryService = Depends(get_gallery_service),
    detection_service: CatDetectionService = Depends(get_cat_detection_service),
    storage_service: StorageService = Depends(get_storage_service),
    quota_service: QuotaService = Depends(get_quota_service),
) -> JSONResponse:
    """
    Upload cat photo with location information.

    Security features:
    - Rate limited: 5 requests per minute
    - Magic bytes validation for file type
    - Input sanitization for all text fields
    - Security event logging

    The image is automatically optimized (resized/compressed) before upload to S3.
    """
    user_id = str(current_user.id)

    try:
        # Log upload attempt
        log_security_event(
            "cat_photo_upload_started",
            user_id=user_id,
            details={
                "filename": file.filename,
                "location_name": location_name[:50] if location_name else "unknown",
            },
        )

        # Check Quota (Atomic Check & Increment)
        allowed = await quota_service.check_and_increment(user_id, current_user.is_pro)
        if not allowed:
            log_security_event("quota_exceeded", user_id=user_id, severity="WARNING")
            raise HTTPException(status_code=429, detail="Daily upload limit reached. Upgrade to Pro for more uploads.")

        # Process and validate the uploaded image with optimization and security checks
        contents, content_type, file_extension = await process_uploaded_image(
            file,
            max_size_mb=config.UPLOAD_MAX_SIZE_MB,
            optimize=True,
            max_dimension=config.UPLOAD_MAX_DIMENSION,
            user_id=user_id,
        )

        # Parse client side cat detection data (logging/debugging only)
        client_cat_data = None
        if cat_detection_data:
            try:
                client_cat_data = json.loads(cat_detection_data)
                logger.debug("Client-side detection data received: %r", client_cat_data)
            except json.JSONDecodeError:
                logger.warning("Failed to parse client detection data: %r", cat_detection_data)

        # Perform server-side detection using OPTIMIZED content (smaller, standard format)
        # This prevents issues with large files or unsupported formats (like HEIC) failing in Vision API
        cat_data = await _perform_server_side_detection(contents, detection_service, user_id, client_cat_data)

        # Use shared validation utilities for coordinates and location text
        latitude, longitude = validate_coordinates(lat, lng)

        # Apply privacy blur offset if requested
        blurred_val = str(location_blurred).lower() in ["true", "1", "yes"]
        if blurred_val:
            import secrets

            rng = secrets.SystemRandom()
            latitude += rng.uniform(-0.00045, 0.00045)
            longitude += rng.uniform(-0.00045, 0.00045)

        # Consolidate text validation
        cleaned_location_name, cleaned_description = validate_location_data(location_name, description)

        # Process and sanitize tags
        parsed_tags = parse_and_sanitize_tags(tags)
        if parsed_tags:
            cleaned_description = format_tags_for_description(parsed_tags, cleaned_description)

        # Determine status
        status = "pending_review" if "fallback_active" in cat_data else "approved"

        # Upload optimized file to S3
        try:
            image_url = await storage_service.upload_file(
                file_content=contents,
                content_type=content_type,
                file_extension=file_extension,
            )
        except ExternalServiceError as s3_error:
            # Catch all S3/storage related errors
            logger.error("S3 upload failed: %s", s3_error)
            log_security_event(
                "s3_upload_failed",
                user_id=user_id,
                details={"error": str(s3_error)[:200]},
                severity="ERROR",
            )
            raise HTTPException(status_code=500, detail="Failed to upload image")

        # Insert into database (cat_photos table)
        photo_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "location_name": cleaned_location_name,
            "description": cleaned_description if cleaned_description else None,
            "tags": parsed_tags if parsed_tags else [],
            "latitude": latitude,
            "longitude": longitude,
            "image_url": image_url,
            "uploaded_at": datetime.now().isoformat(),
            "location_blurred": blurred_val,
            "status": status,
        }

        try:
            created_photo = await gallery_service.save_photo(photo_data)
        except Exception as db_error:
            # Rollback: Delete file from S3 if DB insert fails
            logger.error("Database insert failed: %s. Rolling back S3 upload.", db_error)
            await storage_service.delete_file(image_url)

            log_security_event(
                "upload_transaction_rollback",
                user_id=user_id,
                details={"error": str(db_error)[:200], "image_url": image_url},
                severity="ERROR",
            )
            raise HTTPException(status_code=500, detail="Failed to save cat photo")

        # Invalidate gallery, tags and user photos cache after new upload
        await invalidate_gallery_cache()
        await invalidate_tags_cache()
        await invalidate_user_cache(user_id)

        log_security_event(
            "cat_photo_upload_success",
            user_id=user_id,
            details={
                "photo_id": created_photo["id"],
                "location_name": cleaned_location_name,
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


@router.get("/test")
async def test_upload_endpoint() -> dict[str, Any]:
    """
    Test if upload endpoint is working
    """
    return {
        "message": "Upload endpoint is working!",
        "timestamp": datetime.now().isoformat(),
    }
