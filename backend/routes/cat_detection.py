"""
Cat detection API routes using Google Cloud Vision
"""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from limiter import get_strict_limit, strict_limiter
from logger import logger
from middleware.auth_middleware import get_current_user
from utils.file_processing import read_file_for_detection
from dependencies import get_cat_detection_service

router = APIRouter(prefix="/detect", tags=["Cat Detection"])


from schemas.cat_detection import (
    CatDetectionResult,
    CombinedAnalysisResult,
    SpotAnalysisResult,
)
from schemas.user import User
from services.cat_detection_service import CatDetectionService

# local function removed


from typing import Annotated


@router.post("/cats", response_model=CatDetectionResult)
@strict_limiter.limit(get_strict_limit)
async def detect_cats_in_image(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    """
    Detect cats in images using Google Cloud Vision API.
    Rate Limit: 5 requests per minute per user.

    Raises:
        HTTPException: 413 - If file size exceeds 10MB.
        HTTPException: 415 - If file type is unsupported.
        HTTPException: 500 - If detection fails due to an internal error.
    """
    # Validate and read file using shared utility
    contents = await read_file_for_detection(file, max_size_mb=10)
    file_size = len(contents)

    try:
        # Detect cats using pre-read contents
        result = await detection_service.detect_cats(contents)

        # Add metadata
        result.update(
            {
                "filename": file.filename,
                "file_size": file_size,
                "detected_by": current_user.email,
            }
        )

        logger.info(f"Cat detection completed for {file.filename} by {current_user.email}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection failed: {e!s}")
        raise HTTPException(status_code=500, detail="Detection failed due to an internal error")


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
    # Validate and read file using shared utility
    contents = await read_file_for_detection(file, max_size_mb=10)

    try:
        # Analyze spot using pre-read contents
        result = await detection_service.analyze_cat_spot_suitability(contents)

        # Add metadata
        result.update({"filename": file.filename, "analyzed_by": current_user.email})

        logger.info(f"Spot analysis completed for {file.filename} by {current_user.email}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Spot analysis error: {e!s}")
        raise HTTPException(status_code=500, detail="Spot analysis failed due to an internal error")


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
    # Validate and read file using shared utility
    contents = await read_file_for_detection(file, max_size_mb=10)
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Combined analysis error: {e!s}")
        raise HTTPException(status_code=500, detail="Combined analysis failed due to an internal error")


@router.post("/test-cats")
@strict_limiter.limit(get_strict_limit)
async def test_detect_cats(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Test cat detection using Google Cloud Vision (authentication required).
    Rate Limit: 10 requests per minute per user.

    Raises:
        HTTPException: 500 - If test detection fails.
    """
    # Validate and read file using shared utility
    contents = await read_file_for_detection(file, max_size_mb=10)
    file_size = len(contents)

    try:
        result = await detection_service.detect_cats(contents)

        result.update(
            {
                "filename": file.filename,
                "file_size": file_size,
                "detected_by": current_user.email,
            }
        )

        return result

    except Exception as e:
        logger.error(f"Test detection failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Test failed: {e!s}")


@router.post("/test-spot")
@strict_limiter.limit(get_strict_limit)
async def test_analyze_spot(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """
    Test location analysis using Google Cloud Vision (authentication required).
    Rate Limit: 10 requests per minute per user.

    Raises:
        HTTPException: 500 - If test spot analysis fails.
    """
    # Validate and read file using shared utility
    contents = await read_file_for_detection(file, max_size_mb=10)

    try:
        result = await detection_service.analyze_cat_spot_suitability(contents)
        result.update({"filename": file.filename, "analyzed_by": current_user.email})

        return result

    except Exception as e:
        logger.error(f"Test spot analysis failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Test failed: {e!s}")
