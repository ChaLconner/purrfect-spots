"""
Cat detection API routes using Google Cloud Vision
"""

from typing import Any, NoReturn, cast

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.config import config
from app.dependencies import get_cat_detection_service
from app.limiter import get_strict_limit, strict_limiter
from app.logger import logger
from app.middleware.auth_middleware import get_current_user
from app.utils.file_processing import process_uploaded_image
from app.utils.upload_verification import create_upload_verification_token

router = APIRouter(prefix="/detect", tags=["Cat Detection"])


# local function removed
from typing import Annotated

from app.schemas.cat_detection import (
    CatDetectionResult,
    CombinedAnalysisResult,
    SpotAnalysisResult,
)
from app.schemas.user import User
from app.services.cat_detection_service import CatDetectionService


async def _process_cat_image(file: UploadFile, user_id: str) -> bytes:
    """Validate and process uploaded cat image with standard bounds."""
    contents, _, _ = await process_uploaded_image(
        file,
        max_size_mb=config.UPLOAD_MAX_SIZE_MB,
        optimize=True,
        max_dimension=config.UPLOAD_MAX_DIMENSION,
        user_id=user_id,
    )
    return cast(bytes, contents)


def _handle_detection_error(e: Exception, action_name: str) -> NoReturn:
    """Handle and log errors for cat detection endpoints."""
    if isinstance(e, HTTPException):
        raise e
    logger.error("%s error: %s", action_name, e)
    raise HTTPException(status_code=500, detail=f"{action_name} failed due to an internal error")


@router.post("/cats", response_model=CatDetectionResult)
@strict_limiter.limit(get_strict_limit)
async def detect_cats_endpoint(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    """
    Detect cats in an uploaded image using Google Cloud Vision API.
    Rate Limit: 5 requests per minute per user.

    Raises:
        HTTPException: 413 - If file size exceeds 10MB.
        HTTPException: 415 - If file type is unsupported.
        HTTPException: 500 - If cat detection fails due to an internal error.
    """
    contents = await _process_cat_image(file, str(current_user.id))
    file_size = len(contents)

    try:
        # Detect cats using pre-read contents
        result = await detection_service.detect_cats(contents)

        if result.get("service_available") is False or result.get("fallback_active"):
            raise HTTPException(
                status_code=503,
                detail="Cat verification service unavailable. Please try again later.",
            )

        # Add metadata
        result.update(
            {
                "filename": file.filename,
                "file_size": file_size,
                "detected_by": current_user.email,
                "verification_token": create_upload_verification_token(
                    contents,
                    str(current_user.id),
                    result,
                ),
            }
        )

        logger.info(f"Cat detection completed for {file.filename} by {current_user.email}")
        return result

    except Exception as e:
        _handle_detection_error(e, "Detection")


@router.post("/spot-analysis", response_model=SpotAnalysisResult)
@strict_limiter.limit(get_strict_limit)
async def analyze_cat_spot(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    """
    Analyze suitability of locations for cats using Google Cloud Vision.
    Rate Limit: 5 requests per minute per user.

    Raises:
        HTTPException: 413 - If file size exceeds 10MB.
        HTTPException: 415 - If file type is unsupported.
        HTTPException: 500 - If spot analysis fails due to an internal error.
    """
    contents = await _process_cat_image(file, str(current_user.id))

    try:
        # Analyze spot using pre-read contents
        result = await detection_service.analyze_cat_spot_suitability(contents)

        # Add metadata
        result.update({"filename": file.filename, "analyzed_by": current_user.email})

        logger.info(f"Spot analysis completed for {file.filename} by {current_user.email}")
        return result

    except Exception as e:
        _handle_detection_error(e, "Spot analysis")


@router.post("/combined", response_model=CombinedAnalysisResult)
@strict_limiter.limit(get_strict_limit)
async def combined_cat_and_spot_analysis(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    """
    Analyze both cat detection and location suitability using Google Cloud Vision.
    Rate Limit: 3 requests per minute per user.

    Raises:
        HTTPException: 413 - If file size exceeds 10MB.
        HTTPException: 415 - If file type is unsupported.
        HTTPException: 500 - If combined analysis fails due to an internal error.
    """
    contents = await _process_cat_image(file, str(current_user.id))
    file_size = len(contents)

    try:
        # Run cat detection using pre-read contents
        cat_detection = await detection_service.detect_cats(contents)

        # Run spot analysis using same contents (no file seek needed)
        spot_analysis = await detection_service.analyze_cat_spot_suitability(contents)

        # Combine results
        result = {
            "cat_detection": cat_detection,
            "spot_analysis": spot_analysis,
            "overall_recommendation": {
                "suitable_for_cat_spot": cat_detection.get("suitable_for_cat_spot", False),
                "confidence": (cat_detection.get("confidence", 0) + spot_analysis.get("suitability_score", 0)) / 2,
                "summary": f"Found cats: {cat_detection.get('cat_count', 0)}, Suitability score: {spot_analysis.get('suitability_score', 0)}/100",
            },
            "metadata": {
                "filename": file.filename,
                "file_size": file_size,
                "analyzed_by": current_user.email,
            },
        }

        logger.info(f"Combined analysis completed for {file.filename} by {current_user.email}")
        return result

    except Exception as e:
        _handle_detection_error(e, "Combined analysis")


# Test endpoints removed for security
