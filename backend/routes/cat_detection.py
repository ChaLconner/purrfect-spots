"""
Cat detection API routes using Google Cloud Vision
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from middleware.auth_middleware import get_current_user
import logging
from typing import Dict, Any, List, Optional
import asyncio
import os
import json
import io
from PIL import Image
from pydantic import BaseModel

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
    confidence: int
    cats_detected: List[CatDetected]
    image_quality: str
    suitable_for_cat_spot: bool
    reasoning: str
    note: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    detected_by: Optional[str] = None

class SafetyFactors(BaseModel):
    safe_from_traffic: bool
    has_shelter: bool
    food_source_nearby: bool
    water_access: bool
    escape_routes: bool

class SpotAnalysisResult(BaseModel):
    suitability_score: int
    safety_factors: Optional[SafetyFactors] = None
    environment_type: str
    pros: List[str]
    cons: List[str]
    recommendations: List[str]
    best_times: List[str]
    note: Optional[str] = None
    filename: Optional[str] = None
    analyzed_by: Optional[str] = None

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

class CatDetectionService:
    """Service for cat detection and spot analysis using Google Cloud Vision API"""
    
    def __init__(self):
        """Initialize the service"""
        from services.google_vision import GoogleVisionService
        self.vision_service = GoogleVisionService()
    
    def prepare_image(self, image_data: bytes) -> Image.Image:
        """Prepare image for analysis"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 1024x1024)
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    
    async def detect_cats(self, file: UploadFile) -> Dict[str, Any]:
        """
        Detect cats in image using Google Cloud Vision API
        
        Args:
            file: UploadFile object containing the image
            
        Returns:
            Dict containing detection results
        """
        try:
            # Use Google Vision API to detect cats
            vision_result = self.vision_service.detect_cats(file)
            
            # Convert Vision API result to our expected format
            cats_detected = []
            if vision_result.get("cat_objects"):
                for obj in vision_result.get("cat_objects", []):
                    cats_detected.append({
                        "description": f"Detected {obj.get('name', 'cat')}",
                        "breed_guess": "Domestic cat",
                        "position": "Center of image",
                        "size": "Medium"
                    })
            elif vision_result.get("cat_labels"):
                for label in vision_result.get("cat_labels", []):
                    cats_detected.append({
                        "description": f"Detected {label.get('description', 'cat')}",
                        "breed_guess": "Domestic cat",
                        "position": "Center of image",
                        "size": "Medium"
                    })
            
            # Format the result
            result = {
                "has_cats": vision_result.get("has_cats", False),
                "cat_count": vision_result.get("cat_count", 0),
                "confidence": int(vision_result.get("confidence", 0)),
                "cats_detected": cats_detected,
                "image_quality": vision_result.get("image_quality", "Medium"),
                "suitable_for_cat_spot": vision_result.get("has_cats", False),
                "reasoning": vision_result.get("reasoning", "Cannot analyze")
            }
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cat detection failed: {str(e)}")
    
    async def analyze_cat_spot_suitability(self, file: UploadFile) -> Dict[str, Any]:
        """
        Analyze spot suitability for cats using Google Cloud Vision
        
        Args:
            file: UploadFile object containing the image
            
        Returns:
            Dict containing suitability analysis
        """
        try:
            # Use Google Vision API to analyze spot suitability
            result = self.vision_service.analyze_cat_spot_suitability(file)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Spot analysis failed: {str(e)}")

def get_cat_detection_service():
    return CatDetectionService()

@router.post("/cats", response_model=CatDetectionResult)
async def detect_cats_in_image(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    Detect cats in images using Google Cloud Vision API
    """
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size (max 10MB)
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Reset file position before passing to service
        await file.seek(0)
        
        # Detect cats using Google Cloud Vision
        result = await detection_service.detect_cats(file)
        
        # Add metadata
        result.update({
            "filename": file.filename,
            "file_size": len(contents),
            "detected_by": current_user.email
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.post("/spot-analysis", response_model=SpotAnalysisResult)
async def analyze_cat_spot(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    Analyze suitability of locations for cats using Google Cloud Vision
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        # Reset file position before passing to service
        await file.seek(0)
        
        # Analyze spot using Google Cloud Vision
        result = await detection_service.analyze_cat_spot_suitability(file)
        
        # Add metadata
        result.update({
            "filename": file.filename,
            "analyzed_by": current_user.email
        })
        
        return result
        
    except Exception as e:
        logging.error(f"Spot analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/combined", response_model=CombinedAnalysisResult)
async def combined_cat_and_spot_analysis(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    Analyze both cat detection and location suitability using Google Cloud Vision
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        # Reset file position before passing to service
        await file.seek(0)
        
        # Run both analyses using Google Cloud Vision
        cat_detection = await detection_service.detect_cats(file)
        
        # Reset file position again for second analysis
        await file.seek(0)
        spot_analysis = await detection_service.analyze_cat_spot_suitability(file)
        
        # Combine results
        result = {
            "cat_detection": cat_detection,
            "spot_analysis": spot_analysis,
            "overall_recommendation": {
                "suitable_for_cat_spot": cat_detection.get("suitable_for_cat_spot", False),
                "confidence": (cat_detection.get("confidence", 0) + spot_analysis.get("suitability_score", 0)) / 2,
                "summary": f"Found cats: {cat_detection.get('cat_count', 0)}, Suitability score: {spot_analysis.get('suitability_score', 0)}/100"
            },
            "metadata": {
                "filename": file.filename,
                "file_size": len(contents),
                "analyzed_by": current_user.email
            }
        }
        
        return result
        
    except Exception as e:
        logging.error(f"Combined analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoints without authentication
@router.post("/test-cats")
async def test_detect_cats(
    file: UploadFile = File(...),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    Test cat detection using Google Cloud Vision (no authentication required)
    """
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Reset file position before passing to service
        await file.seek(0)
        
        result = await detection_service.detect_cats(file)
        
        result.update({
            "filename": file.filename,
            "file_size": len(contents),
            "detected_by": "test_user"
        })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.post("/test-spot")
async def test_analyze_spot(
    file: UploadFile = File(...),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    Test location analysis using Google Cloud Vision (no authentication required)
    """
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Reset file position before passing to service
        await file.seek(0)
        
        result = await detection_service.analyze_cat_spot_suitability(file)
        result.update({
            "filename": file.filename,
            "analyzed_by": "test_user"
        })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")