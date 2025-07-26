"""
Cat detection API routes
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
    """Service for cat detection and spot analysis using Google AI Studio"""
    
    def __init__(self):
        """Initialize the service"""
        self.google_ai_api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not self.google_ai_api_key:
            logging.warning("GOOGLE_AI_API_KEY not found, using placeholder responses")
    
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
    
    async def detect_cats(self, image_contents: bytes) -> Dict[str, Any]:
        """
        Detect cats in image
        
        Args:
            image_contents: Image file contents as bytes
            
        Returns:
            Dict containing detection results
        """
        try:
            # Prepare image
            image = self.prepare_image(image_contents)
            
            # If Google AI API is available, use it
            if self.google_ai_api_key:
                try:
                    import google.generativeai as genai
                    
                    genai.configure(api_key=self.google_ai_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = """
                    วิเคราะห์รูปภาพนี้และตอบเป็น JSON format ดังนี้:
                    {
                        "has_cats": true/false,
                        "cat_count": จำนวนแมวที่พบ,
                        "confidence": ระดับความมั่นใจ (0-100),
                        "cats_detected": [
                            {
                                "description": "คำอธิบายแมวตัวนี้",
                                "breed_guess": "พันธุ์แมวที่คาดว่าเป็น (ถ้ามี)",
                                "position": "ตำแหน่งในรูป (เช่น ซ้าย, กลาง, ขวา)",
                                "size": "ขนาดในรูป (เช่น ใหญ่, กลาง, เล็ก)"
                            }
                        ],
                        "image_quality": "คุณภาพรูปภาพ (ดี/ปานกลาง/ไม่ดี)",
                        "suitable_for_cat_spot": true/false,
                        "reasoning": "เหตุผลที่เหมาะ/ไม่เหมาะสำหรับเป็น cat spot"
                    }
                    
                    ตอบเป็นภาษาไทยในส่วน description และ reasoning
                    ถ้าไม่มีแมวในรูป ให้ has_cats เป็น false และ cat_count เป็น 0
                    """
                    
                    response = model.generate_content([prompt, image])
                    
                    # Parse JSON response
                    try:
                        response_text = response.text.strip()
                        if response_text.startswith('```json'):
                            response_text = response_text[7:]
                        if response_text.endswith('```'):
                            response_text = response_text[:-3]
                        
                        result = json.loads(response_text)
                        
                        # Validate and format the result
                        formatted_result = {
                            "has_cats": result.get("has_cats", False),
                            "cat_count": result.get("cat_count", 0),
                            "confidence": result.get("confidence", 0),
                            "cats_detected": [
                                {
                                    "description": cat.get("description", ""),
                                    "breed_guess": cat.get("breed_guess", ""),
                                    "position": cat.get("position", ""),
                                    "size": cat.get("size", "")
                                } for cat in result.get("cats_detected", [])
                            ],
                            "image_quality": result.get("image_quality", "ปานกลาง"),
                            "suitable_for_cat_spot": result.get("suitable_for_cat_spot", False),
                            "reasoning": result.get("reasoning", "")
                        }
                        return formatted_result
                        
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        text = response.text.lower()
                        has_cats = any(word in text for word in ['แมว', 'cat', 'kitten', 'feline'])
                        
                        return {
                            "has_cats": has_cats,
                            "cat_count": 1 if has_cats else 0,
                            "confidence": 70 if has_cats else 30,
                            "cats_detected": [],
                            "image_quality": "ปานกลาง",
                            "suitable_for_cat_spot": has_cats,
                            "reasoning": "ไม่สามารถวิเคราะห์รายละเอียดได้ แต่พบการตรวจจับแมวขั้นพื้นฐาน",
                            "note": f"Raw AI response: {response.text}"
                        }
                
                except ImportError:
                    logging.warning("google-generativeai not installed, using placeholder")
                except Exception as e:
                    logging.error(f"Google AI API error: {str(e)}")
            
            # Fallback placeholder response
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                "has_cats": True,
                "cat_count": 1,
                "confidence": 85,
                "cats_detected": [
                    {
                        "description": "แมวสีเทาขนาดกลาง",
                        "breed_guess": "แมวบ้าน",
                        "position": "กลางรูป",
                        "size": "กลาง"
                    }
                ],
                "image_quality": "ดี",
                "suitable_for_cat_spot": True,
                "reasoning": "พบแมวในรูปภาพ เหมาะสมสำหรับการเป็น cat spot",
                "note": "ผลลัพธ์จำลอง - กรุณาตั้งค่า GOOGLE_AI_API_KEY สำหรับการวิเคราะห์จริง"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cat detection failed: {str(e)}")
    
    async def analyze_cat_spot_suitability(self, image_contents: bytes) -> Dict[str, Any]:
        """
        Analyze spot suitability for cats
        
        Args:
            image_contents: Image file contents as bytes
            
        Returns:
            Dict containing suitability analysis
        """
        try:
            # Prepare image
            image = self.prepare_image(image_contents)
            
            # If Google AI API is available, use it
            if self.google_ai_api_key:
                try:
                    import google.generativeai as genai
                    
                    genai.configure(api_key=self.google_ai_api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = """
                    วิเคราะห์สถานที่ในรูปภาพนี้ว่าเหมาะสำหรับแมวหรือไม่ และตอบเป็น JSON:
                    {
                        "suitability_score": 0-100,
                        "safety_factors": {
                            "safe_from_traffic": true/false,
                            "has_shelter": true/false,
                            "food_source_nearby": true/false,
                            "water_access": true/false,
                            "escape_routes": true/false
                        },
                        "environment_type": "ประเภทสถานที่ (เช่น สวน, ตรอกซอย, ร้านอาหาร)",
                        "pros": ["ข้อดีของสถานที่นี้สำหรับแมว"],
                        "cons": ["ข้อเสียของสถานที่นี้สำหรับแมว"],
                        "recommendations": ["ข้อเสนอแนะในการปรับปรุง"],
                        "best_times": ["เวลาที่เหมาะสมที่สุดสำหรับแมว"]
                    }
                    """
                    
                    response = model.generate_content([prompt, image])
                    
                    try:
                        response_text = response.text.strip()
                        if response_text.startswith('```json'):
                            response_text = response_text[7:]
                        if response_text.endswith('```'):
                            response_text = response_text[:-3]
                        
                        return json.loads(response_text)
                        
                    except json.JSONDecodeError:
                        return {
                            "suitability_score": 50,
                            "environment_type": "ไม่สามารถระบุได้",
                            "pros": ["ต้องการการวิเคราะห์เพิ่มเติม"],
                            "cons": ["ไม่สามารถวิเคราะห์รายละเอียดได้"],
                            "recommendations": ["อัพโหลดรูปภาพที่ชัดเจนมากขึ้น"],
                            "best_times": [],
                            "note": f"Raw AI response: {response.text}"
                        }
                
                except ImportError:
                    logging.warning("google-generativeai not installed, using placeholder")
                except Exception as e:
                    logging.error(f"Google AI API error: {str(e)}")
            
            # Fallback placeholder response
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                "suitability_score": 75,
                "safety_factors": {
                    "safe_from_traffic": True,
                    "has_shelter": True,
                    "food_source_nearby": False,
                    "water_access": False,
                    "escape_routes": True
                },
                "environment_type": "สวนสาธารณะ",
                "pros": [
                    "มีที่กำบังแสงแดดและฝน",
                    "ปลอดภัยจากรถยนต์",
                    "มีทางหนีได้หลายเส้นทาง"
                ],
                "cons": [
                    "ไม่มีแหล่งอาหาร",
                    "ไม่มีแหล่งน้ำ"
                ],
                "recommendations": [
                    "วางภาชนะน้ำสะอาด",
                    "ให้อาหารแมวเป็นประจำ",
                    "สร้างบ้านแมวเล็กๆ เพิ่มเติม"
                ],
                "best_times": [
                    "เช้า 06:00-08:00",
                    "เย็น 17:00-19:00"
                ],
                "note": "ผลลัพธ์จำลอง - กรุณาตั้งค่า GOOGLE_AI_API_KEY สำหรับการวิเคราะห์จริง"
            }
            
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
    ตรวจจับแมวในรูปภาพ
    """
    print(f"🔍 Detecting cats for user: {current_user.get('email', 'unknown')}")
    print(f"📁 File: {file.filename}, Type: {file.content_type}, Size: {file.size}")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size (max 10MB)
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        print(f"📊 File size: {len(contents)} bytes")
        
        # Detect cats
        result = await detection_service.detect_cats(contents)
        
        # Add metadata
        result.update({
            "filename": file.filename,
            "file_size": len(contents),
            "detected_by": current_user.get("email", "unknown")
        })
        
        print(f"✅ Cat detection completed: {result.get('has_cats', False)}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Cat detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.post("/spot-analysis", response_model=SpotAnalysisResult)
async def analyze_cat_spot(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    วิเคราะห์ความเหมาะสมของสถานที่สำหรับแมว
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        # Analyze spot
        result = await detection_service.analyze_cat_spot_suitability(contents)
        
        # Add metadata
        result.update({
            "filename": file.filename,
            "analyzed_by": current_user.get("email", "unknown")
        })
        
        return result
        
    except Exception as e:
        logging.error(f"❌ Spot analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/combined", response_model=CombinedAnalysisResult)
async def combined_cat_and_spot_analysis(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    วิเคราะห์ทั้งการตรวจจับแมวและความเหมาะสมของสถานที่
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    try:
        # Run both analyses
        cat_detection = await detection_service.detect_cats(contents)
        spot_analysis = await detection_service.analyze_cat_spot_suitability(contents)
        
        # Combine results
        result = {
            "cat_detection": cat_detection,
            "spot_analysis": spot_analysis,
            "overall_recommendation": {
                "suitable_for_cat_spot": cat_detection.get("suitable_for_cat_spot", False),
                "confidence": (cat_detection.get("confidence", 0) + spot_analysis.get("suitability_score", 0)) / 2,
                "summary": f"พบแมว: {cat_detection.get('cat_count', 0)} ตัว, คะแนนความเหมาะสม: {spot_analysis.get('suitability_score', 0)}/100"
            },
            "metadata": {
                "filename": file.filename,
                "file_size": len(contents),
                "analyzed_by": current_user.get("email", "unknown")
            }
        }
        
        return result
        
    except Exception as e:
        logging.error(f"❌ Combined analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoints without authentication
@router.post("/test-cats")
async def test_detect_cats(
    file: UploadFile = File(...),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    ทดสอบการตรวจจับแมว (ไม่ต้อง authentication)
    """
    print(f"🧪 Testing cat detection for file: {file.filename}")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        result = await detection_service.detect_cats(contents)
        result.update({
            "filename": file.filename,
            "file_size": len(contents),
            "detected_by": "test_user"
        })
        
        return result
        
    except Exception as e:
        print(f"❌ Test detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.post("/test-spot")
async def test_analyze_spot(
    file: UploadFile = File(...),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    ทดสอบการวิเคราะห์สถานที่ (ไม่ต้อง authentication)
    """
    print(f"🧪 Testing spot analysis for file: {file.filename}")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        result = await detection_service.analyze_cat_spot_suitability(contents)
        result.update({
            "filename": file.filename,
            "analyzed_by": "test_user"
        })
        
        return result
        
    except Exception as e:
        print(f"❌ Test spot analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")