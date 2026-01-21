"""
Upload routes for cat photo uploads with location information
Enhanced with security features: rate limiting, input sanitization, security logging
"""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from config import config
from dependencies import get_supabase_client
from limiter import limiter
from logger import logger
from middleware.auth_middleware import get_current_user
from services.cat_detection_service import CatDetectionService
from services.storage_service import StorageService
from utils.cache import invalidate_gallery_cache, invalidate_tags_cache
from utils.file_processing import process_uploaded_image, validate_coordinates
from utils.security import (
    log_security_event,
    sanitize_description,
    sanitize_location_name,
    sanitize_tags,
)

router = APIRouter(prefix="/upload", tags=["Upload"])


# Alias for backward compatibility with tests
def parse_tags(tags_json):
    """Backward compatible alias for parse_and_sanitize_tags"""
    return parse_and_sanitize_tags(tags_json)


def get_storage_service() -> StorageService:
    return StorageService()


def get_cat_detection_service() -> CatDetectionService:
    return CatDetectionService()


def parse_and_sanitize_tags(tags_json: str | None) -> list:
    """Parse and sanitize tags from JSON string with security measures."""
    if not tags_json:
        return []

    try:
        tag_list = json.loads(tags_json)
        if tag_list and isinstance(tag_list, list):
            # Use security utility for sanitization
            return sanitize_tags(tag_list)
    except Exception as e:
        logger.warning(f"Failed to parse tags: {e}")

    return []


def format_tags_for_description(tags: list, description: str) -> str:
    """Append hashtags to description for backward compatibility."""
    if not tags:
        return description

    hashtag_string = " ".join([f"#{tag}" for tag in tags])
    if description:
        return f"{description}\n\n{hashtag_string}"
    return hashtag_string


def validate_cat_detection_data(cat_data: dict) -> bool:
    """
    Validate cat detection data structure and values.

    Returns:
        True if valid, False otherwise
    """
    if not cat_data or not isinstance(cat_data, dict):
        return False

    # Required fields
    required_fields = ["has_cats", "cat_count", "confidence"]
    for field in required_fields:
        if field not in cat_data:
            return False

    # Validate values
    if not isinstance(cat_data.get("has_cats"), bool):
        return False

    cat_count = cat_data.get("cat_count", 0)
    if not isinstance(cat_count, (int, float)) or cat_count < 0:
        return False

    confidence = cat_data.get("confidence", 0)
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 100):
        return False

    return True


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
    current_user=Depends(get_current_user),
    supabase=Depends(get_supabase_client),
    detection_service: CatDetectionService = Depends(get_cat_detection_service),
    storage_service: StorageService = Depends(get_storage_service),
):
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

        # Process and validate the uploaded image with optimization and security checks
        contents, content_type, file_extension = await process_uploaded_image(
            file,
            max_size_mb=config.UPLOAD_MAX_SIZE_MB,
            optimize=True,
            max_dimension=config.UPLOAD_MAX_DIMENSION,
            user_id=user_id,
        )

        # Parse and validate cat detection data if provided
        cat_data = None
        if cat_detection_data:
            try:
                cat_data = json.loads(cat_detection_data)

                # Validate the structure and values
                if not validate_cat_detection_data(cat_data):
                    log_security_event(
                        "invalid_cat_detection_data",
                        user_id=user_id,
                        details={"data": str(cat_data)[:200]},
                        severity="WARNING",
                    )
                    cat_data = None  # Force server-side detection

            except json.JSONDecodeError:
                log_security_event(
                    "cat_detection_json_parse_error",
                    user_id=user_id,
                    severity="WARNING",
                )
                cat_data = None

        # If no valid cat detection data provided, detect cats on server
        if not cat_data:
            await file.seek(0)
            detection_result = await detection_service.detect_cats(file)

            # Reject if no cats found
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

            cat_data = {
                "has_cats": detection_result.get("has_cats"),
                "cat_count": detection_result.get("cat_count", 0),
                "confidence": detection_result.get("confidence", 0),
                "suitable_for_cat_spot": detection_result.get("suitable_for_cat_spot", False),
                "cats_detected": detection_result.get("cats_detected", []),
                "detection_timestamp": datetime.now().isoformat(),
                "detection_source": "server",
            }

        # Validate that cats were detected (be lenient if client marked for server verification)
        requires_verification = cat_data.get("requires_server_verification", False)
        has_cats = cat_data.get("has_cats", False)
        cat_count = cat_data.get("cat_count", 0)

        # Allow upload if: (has_cats AND cat_count > 0) OR (requires_verification AND has_cats)
        if not has_cats or (cat_count == 0 and not requires_verification):
            log_security_event("upload_rejected_invalid_detection", user_id=user_id, severity="INFO")
            raise HTTPException(status_code=400, detail="Cannot upload: No cats detected in the image")

        # Use shared validation utilities for coordinates
        latitude, longitude = validate_coordinates(lat, lng)

        # Sanitize text inputs
        cleaned_location_name = sanitize_location_name(location_name)
        cleaned_description = sanitize_description(description) if description else ""

        # Validate location name after sanitization
        if not cleaned_location_name or len(cleaned_location_name) < 3:
            raise HTTPException(status_code=400, detail="Location name must be at least 3 characters")

        if len(cleaned_location_name) > 100:
            raise HTTPException(status_code=400, detail="Location name must be under 100 characters")

        # Process and sanitize tags
        parsed_tags = parse_and_sanitize_tags(tags)
        if parsed_tags:
            cleaned_description = format_tags_for_description(parsed_tags, cleaned_description)

        # Upload optimized file to S3
        try:
            image_url = await storage_service.upload_file(
                file_content=contents,
                content_type=content_type,
                file_extension=file_extension,
            )
        except Exception as s3_error:
            logger.error(f"S3 upload failed: {s3_error!s}")
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
        }

        # Use admin client to bypass RLS
        from dependencies import get_supabase_admin_client

        supabase_admin = get_supabase_admin_client()

        result = supabase_admin.table("cat_photos").insert(photo_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save cat photo")

        created_photo = result.data[0]

        # Invalidate gallery and tags cache after new upload
        invalidate_gallery_cache()
        invalidate_tags_cache()

        log_security_event(
            "cat_photo_upload_success",
            user_id=user_id,
            details={
                "photo_id": created_photo["id"],
                "location_name": cleaned_location_name,
            },
        )

        logger.info(f"Cat photo uploaded successfully: {created_photo['id']} by {current_user.email}")

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
        logger.error(f"Upload error: {e!s}", exc_info=True)
        log_security_event(
            "upload_error",
            user_id=user_id,
            details={"error": str(e)[:200]},
            severity="ERROR",
        )
        raise HTTPException(status_code=500, detail="Upload failed due to an internal error")


@router.get("/test")
async def test_upload_endpoint():
    """
    Test if upload endpoint is working
    """
    return {
        "message": "Upload endpoint is working!",
        "timestamp": datetime.now().isoformat(),
    }
