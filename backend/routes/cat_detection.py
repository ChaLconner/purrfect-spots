"""
Cat detection API routes using Google Cloud Vision
"""


from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from limiter import limiter
from logger import logger
from middleware.auth_middleware import get_current_user
from utils.file_processing import read_file_for_detection

router = APIRouter(prefix="/detect", tags=["Cat Detection"])


# Pydantic models for response validation
class CatDetected(BaseModel):
    description: str
    breed_guess: str
    position: str
    size: str


class CatDetectionResult(BaseModel):
    has_cats: bool
    cat_count: int
    confidence: float
    cats_detected: list[CatDetected]
    image_quality: str
    suitable_for_cat_spot: bool
    reasoning: str
    note: str | None = None
    filename: str | None = None
    file_size: int | None = None
    detected_by: str | None = None


class SafetyFactors(BaseModel):
    safe_from_traffic: bool
    has_shelter: bool
    food_source_nearby: bool
    water_access: bool
    escape_routes: bool


class SpotAnalysisResult(BaseModel):
    suitability_score: int
    safety_factors: SafetyFactors | None = None
    environment_type: str
    pros: list[str]
    cons: list[str]
    recommendations: list[str]
    best_times: list[str]
    note: str | None = None
    filename: str | None = None
    analyzed_by: str | None = None


class OverallRecommendation(BaseModel):
    suitable_for_cat_spot: bool
    confidence: float
    summary: str


class AnalysisMetadata(BaseModel):
    filename: str
    file_size: int
    analyzed_by: str


class CombinedAnalysisResult(BaseModel):
    cat_detection: CatDetectionResult
    spot_analysis: SpotAnalysisResult
    overall_recommendation: OverallRecommendation
    metadata: AnalysisMetadata


from services.cat_detection_service import CatDetectionService


def get_cat_detection_service() -> CatDetectionService:
    return CatDetectionService()


@router.post("/cats", response_model=CatDetectionResult)
@limiter.limit("5/minute")
async def detect_cats_in_image(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service),
):
    """
    Detect cats in images using Google Cloud Vision API.
    Rate Limit: 5 requests per minute per user.
    """
    # Validate and read file using shared utility
    contents = await read_file_for_detection(file, max_size_mb=10)
    file_size = len(contents)

    try:
        # Detect cats
        result = await detection_service.detect_cats(file)

        # Add metadata
        result.update(
            {
                "filename": file.filename,
                "file_size": file_size,
                "detected_by": current_user.email,
            }
        )

        logger.info(
            f"Cat detection completed for {file.filename} by {current_user.email}"
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection failed: {e!s}")
        raise HTTPException(
            status_code=500, detail="Detection failed due to an internal error"
        )


@router.post("/spot-analysis", response_model=SpotAnalysisResult)
@limiter.limit("5/minute")
async def analyze_cat_spot(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service),
):
    """
    Analyze suitability of locations for cats using Google Cloud Vision.
    Rate Limit: 5 requests per minute per user.
    """
    # Validate and read file using shared utility
    await read_file_for_detection(file, max_size_mb=10)

    try:
        # Analyze spot
        result = await detection_service.analyze_cat_spot_suitability(file)

        # Add metadata
        result.update({"filename": file.filename, "analyzed_by": current_user.email})

        logger.info(
            f"Spot analysis completed for {file.filename} by {current_user.email}"
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Spot analysis error: {e!s}")
        raise HTTPException(
            status_code=500, detail="Spot analysis failed due to an internal error"
        )


@router.post("/combined", response_model=CombinedAnalysisResult)
@limiter.limit("3/minute")
async def combined_cat_and_spot_analysis(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service),
):
    """
    Analyze both cat detection and location suitability using Google Cloud Vision.
    Rate Limit: 3 requests per minute per user.
    """
    # Validate and read file using shared utility
    contents = await read_file_for_detection(file, max_size_mb=10)
    file_size = len(contents)

    try:
        # Run cat detection
        cat_detection = await detection_service.detect_cats(file)

        # Reset file pointer for second analysis
        await file.seek(0)
        spot_analysis = await detection_service.analyze_cat_spot_suitability(file)

        # Combine results
        result = {
            "cat_detection": cat_detection,
            "spot_analysis": spot_analysis,
            "overall_recommendation": {
                "suitable_for_cat_spot": cat_detection.get(
                    "suitable_for_cat_spot", False
                ),
                "confidence": (
                    cat_detection.get("confidence", 0)
                    + spot_analysis.get("suitability_score", 0)
                )
                / 2,
                "summary": f"Found cats: {cat_detection.get('cat_count', 0)}, Suitability score: {spot_analysis.get('suitability_score', 0)}/100",
            },
            "metadata": {
                "filename": file.filename,
                "file_size": file_size,
                "analyzed_by": current_user.email,
            },
        }

        logger.info(
            f"Combined analysis completed for {file.filename} by {current_user.email}"
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Combined analysis error: {e!s}")
        raise HTTPException(
            status_code=500, detail="Combined analysis failed due to an internal error"
        )


@router.post("/test-cats")
@limiter.limit("10/minute")
async def test_detect_cats(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service),
):
    """
    Test cat detection using Google Cloud Vision (authentication required).
    Rate Limit: 10 requests per minute per user.
    """
    # Validate and read file using shared utility
    contents = await read_file_for_detection(file, max_size_mb=10)
    file_size = len(contents)

    try:
        result = await detection_service.detect_cats(file)

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
@limiter.limit("10/minute")
async def test_analyze_spot(
    request: Request,
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service),
):
    """
    Test location analysis using Google Cloud Vision (authentication required).
    Rate Limit: 10 requests per minute per user.
    """
    # Validate and read file using shared utility
    await read_file_for_detection(file, max_size_mb=10)

    try:
        result = await detection_service.analyze_cat_spot_suitability(file)
        result.update({"filename": file.filename, "analyzed_by": current_user.email})

        return result

    except Exception as e:
        logger.error(f"Test spot analysis failed: {e!s}")
        raise HTTPException(status_code=500, detail=f"Test failed: {e!s}")
