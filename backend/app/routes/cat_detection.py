"""
Cat detection API routes using Google Cloud Vision
"""

from typing import Annotated, Any, Literal, NoReturn, cast

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import config
from app.dependencies import get_cat_detection_service
from app.limiter import get_strict_limit, strict_limiter
from app.logger import logger
from app.middleware.auth_middleware import get_current_user
from app.utils.file_processing import process_uploaded_image
from app.utils.upload_verification import create_upload_verification_token

router = APIRouter(prefix="/detect", tags=["Cat Detection"])


from app.schemas.cat_detection import (
    CatDetectionResult,
    CombinedAnalysisResult,
    SpotAnalysisResult,
    VisionJobAccepted,
    VisionJobStatus,
)
from app.schemas.user import User
from app.services.cat_detection_service import CatDetectionService
from app.services.queue_service import QueueBackpressure, QueueUnavailable, queue_service


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


async def _enqueue_vision_job(
    *,
    operation: Literal["spot-analysis", "combined"],
    current_user: User,
    filename: str | None,
    contents: bytes,
) -> JSONResponse | None:
    if not config.ENABLE_VISION_ANALYSIS_QUEUE:
        return None
    try:
        job = await queue_service.enqueue_vision_job(
            operation=operation,
            user_id=str(current_user.id),
            analyzed_by=current_user.email,
            filename=filename,
            contents=contents,
        )
    except (QueueUnavailable, QueueBackpressure) as exc:
        raise HTTPException(status_code=503, detail="Vision analysis queue temporarily unavailable") from exc
    accepted = VisionJobAccepted(
        status="queued",
        job_id=str(job["job_id"]),
        operation=operation,
        created_at=str(job["created_at"]),
    )
    return JSONResponse(status_code=202, content=accepted.model_dump())


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


@router.post("/spot-analysis", response_model=SpotAnalysisResult | VisionJobAccepted)
@strict_limiter.limit(get_strict_limit)
async def analyze_cat_spot(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any] | JSONResponse:
    """
    Analyze suitability of locations for cats using Google Cloud Vision.
    Rate Limit: 5 requests per minute per user.

    Raises:
        HTTPException: 413 - If file size exceeds 10MB.
        HTTPException: 415 - If file type is unsupported.
        HTTPException: 500 - If spot analysis fails due to an internal error.
    """
    contents = await _process_cat_image(file, str(current_user.id))

    queued_response = await _enqueue_vision_job(
        operation="spot-analysis",
        current_user=current_user,
        filename=file.filename,
        contents=contents,
    )
    if queued_response is not None:
        return queued_response

    try:
        # Analyze spot using pre-read contents
        result = await detection_service.analyze_cat_spot_suitability(contents)

        # Add metadata
        result.update({"filename": file.filename, "analyzed_by": current_user.email})

        logger.info(f"Spot analysis completed for {file.filename} by {current_user.email}")
        return result

    except Exception as e:
        _handle_detection_error(e, "Spot analysis")


@router.post("/combined", response_model=CombinedAnalysisResult | VisionJobAccepted)
@strict_limiter.limit(get_strict_limit)
async def combined_cat_and_spot_analysis(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    detection_service: Annotated[CatDetectionService, Depends(get_cat_detection_service)],
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any] | JSONResponse:
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

    # This queue is for analysis only. Upload admission still uses /cats and
    # remains synchronous so the verification token cannot be bypassed.
    queued_response = await _enqueue_vision_job(
        operation="combined",
        current_user=current_user,
        filename=file.filename,
        contents=contents,
    )
    if queued_response is not None:
        return queued_response

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


@router.get("/jobs/{job_id}", response_model=VisionJobStatus)
async def get_vision_job_status(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
) -> VisionJobStatus:
    """Return a Vision analysis result owned by the authenticated user."""
    try:
        job = await queue_service.get_vision_job(job_id, str(current_user.id))
    except QueueUnavailable as exc:
        raise HTTPException(status_code=503, detail="Vision analysis queue temporarily unavailable") from exc
    if not job:
        raise HTTPException(status_code=404, detail="Vision analysis job not found")
    return VisionJobStatus(**job)


# Test endpoints removed for security
