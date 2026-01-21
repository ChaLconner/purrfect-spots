"""
Shared file processing utilities for Purrfect Spots
Consolidates common file handling patterns across routes
Enhanced with security features: magic bytes validation, input sanitization
"""

from fastapi import HTTPException, UploadFile

from logger import logger
from utils.file_utils import get_safe_file_extension, validate_image_file
from utils.image_utils import is_valid_image, optimize_image
from utils.security import (
    is_safe_filename,
    log_security_event,
    sanitize_description,
    sanitize_location_name,
    validate_content_type_matches,
    validate_image_magic_bytes,
)


async def process_uploaded_image(
    file: UploadFile,
    max_size_mb: int = 10,
    optimize: bool = True,
    max_dimension: int = 1920,
    user_id: str | None = None,
) -> tuple[bytes, str, str]:
    """
    Process an uploaded image file with validation and optional optimization.
    Enhanced with magic bytes validation for security.

    This consolidates the common pattern of:
    1. Reading file contents
    2. Validating file type and size (with magic bytes)
    3. Optionally optimizing the image
    4. Determining safe file extension

    Args:
        file: FastAPI UploadFile object
        max_size_mb: Maximum allowed file size in MB
        optimize: Whether to optimize the image
        max_dimension: Maximum image dimension for optimization
        user_id: Optional user ID for security logging

    Returns:
        Tuple of (processed_bytes, content_type, file_extension)

    Raises:
        HTTPException: If file validation fails
    """
    try:
        # Read file contents
        contents = await file.read()
        original_size = len(contents)

        logger.debug(f"Processing uploaded file: {file.filename}, size={original_size / 1024:.1f}KB")

        # Log upload attempt
        log_security_event(
            "upload_attempt",
            user_id=user_id,
            details={
                "filename": file.filename or "unknown",
                "size_kb": original_size / 1024,
                "claimed_type": file.content_type,
            },
        )

        # Validate filename
        if file.filename and not is_safe_filename(file.filename):
            log_security_event(
                "unsafe_filename_blocked",
                user_id=user_id,
                details={"filename": file.filename},
                severity="WARNING",
            )
            raise HTTPException(status_code=400, detail="Invalid filename")

        # Validate file type and size using Content-Type header (first check)
        try:
            validate_image_file(file.content_type, original_size, max_size_mb)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # CRITICAL: Validate using magic bytes (more secure than Content-Type)
        is_valid_magic, detected_mime, magic_error = validate_image_magic_bytes(contents)
        if not is_valid_magic:
            log_security_event(
                "magic_bytes_validation_failed",
                user_id=user_id,
                details={
                    "claimed_type": file.content_type,
                    "detected_type": detected_mime,
                    "error": magic_error,
                },
                severity="WARNING",
            )
            raise HTTPException(status_code=400, detail="Invalid image file type")

        # Check Content-Type matches actual file content
        content_match, actual_mime = validate_content_type_matches(file.content_type, contents)
        if not content_match:
            log_security_event(
                "content_type_mismatch",
                user_id=user_id,
                details={"claimed_type": file.content_type, "actual_type": actual_mime},
                severity="WARNING",
            )
            # Use the actual detected MIME type instead of claimed
            file.content_type = actual_mime

        # Verify it's actually a valid image (PIL verification)
        if not is_valid_image(contents):
            log_security_event(
                "corrupted_image_blocked",
                user_id=user_id,
                details={"filename": file.filename},
                severity="WARNING",
            )
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file")

        # Optimize image if requested (also strips EXIF metadata)
        content_type = actual_mime if content_match else file.content_type
        if optimize:
            contents, content_type = optimize_image(contents, content_type, max_dimension=max_dimension)

        # Get safe file extension based on final content type
        file_extension = get_safe_file_extension(file.filename or "", content_type)

        log_security_event(
            "upload_processed_successfully",
            user_id=user_id,
            details={"final_type": content_type, "final_size_kb": len(contents) / 1024},
        )

        return contents, content_type, file_extension.lstrip(".")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File processing error: {e!s}")
        log_security_event(
            "file_processing_error",
            user_id=user_id,
            details={"error": str(e)},
            severity="ERROR",
        )
        raise HTTPException(status_code=500, detail="Failed to process uploaded file")
    finally:
        # Reset file position for potential reuse
        await file.seek(0)


async def read_file_for_detection(file: UploadFile, max_size_mb: int = 10) -> bytes:
    """
    Read file contents for detection services without optimization.
    Validates and returns raw bytes for AI processing.

    Args:
        file: FastAPI UploadFile object
        max_size_mb: Maximum allowed file size in MB

    Returns:
        Raw file bytes

    Raises:
        HTTPException: If validation fails
    """
    try:
        contents = await file.read()

        try:
            validate_image_file(file.content_type, len(contents), max_size_mb)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Reset for subsequent reads
        await file.seek(0)

        return contents

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File read error: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to read uploaded file")


def validate_coordinates(lat: str, lng: str) -> tuple[float, float]:
    """
    Validate and parse latitude/longitude coordinates.

    Args:
        lat: Latitude as string
        lng: Longitude as string

    Returns:
        Tuple of (latitude, longitude) as floats

    Raises:
        HTTPException: If coordinates are invalid
    """
    try:
        latitude = float(lat)
        longitude = float(lng)

        if not (-90 <= latitude <= 90):
            raise HTTPException(status_code=400, detail="Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="Longitude must be between -180 and 180")

        return latitude, longitude

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid coordinate format")


def validate_location_data(location_name: str, description: str | None = None) -> tuple[str, str]:
    """
    Validate and sanitize location name and description.
    Enhanced with XSS prevention and input sanitization.

    Args:
        location_name: Location name from form
        description: Optional description

    Returns:
        Tuple of (cleaned_location_name, cleaned_description)

    Raises:
        HTTPException: If validation fails
    """
    # Sanitize inputs to prevent XSS
    cleaned_name = sanitize_location_name(location_name) if location_name else ""

    if not cleaned_name:
        raise HTTPException(status_code=400, detail="Location name is required")

    if len(cleaned_name) < 3:
        raise HTTPException(status_code=400, detail="Location name must be at least 3 characters")

    if len(cleaned_name) > 100:
        raise HTTPException(status_code=400, detail="Location name must be under 100 characters")

    # Sanitize description
    cleaned_description = sanitize_description(description) if description else ""

    if cleaned_description and len(cleaned_description) > 1000:
        raise HTTPException(status_code=400, detail="Description is too long")

    return cleaned_name, cleaned_description
