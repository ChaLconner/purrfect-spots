"""
Cat detection service using Google AI Studio (Gemini)
"""
import os
import base64
import io
import json
from typing import Dict, List, Optional, Tuple
from PIL import Image
import google.generativeai as genai
from fastapi import HTTPException

class CatDetectionService:
    def __init__(self):
        """Initialize Google AI Studio client"""
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_AI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def prepare_image(self, image_data: bytes) -> Image.Image:
        """Prepare image for analysis"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 4MB for Gemini)
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    
    async def detect_cats(self, image_data: bytes) -> Dict:
        """
        Detect cats in image using Google AI Studio
        """
        try:
            # Prepare image
            image = self.prepare_image(image_data)
            
            # Create prompt for cat detection
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
            
            # Send to Gemini
            response = self.model.generate_content([prompt, image])
            
            # Parse JSON response
            try:
                # Clean response text
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                result = json.loads(response_text)
                
                # Validate required fields
                required_fields = ['has_cats', 'cat_count', 'confidence']
                for field in required_fields:
                    if field not in result:
                        result[field] = False if field == 'has_cats' else 0
                
                return result
                
            except json.JSONDecodeError as e:
                # Fallback response
                print(f"⚠️ JSON parse error: {e}")
                print(f"📝 Raw response: {response.text}")
                
                # Try to extract basic info
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
                    "raw_ai_response": response.text
                }
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cat detection failed: {str(e)}"
            )
    
    async def analyze_cat_spot_suitability(self, image_data: bytes) -> Dict:
        """
        Analyze if location is suitable for cats
        """
        try:
            image = self.prepare_image(image_data)
            
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
            
            response = self.model.generate_content([prompt, image])
            
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
                    "raw_ai_response": response.text
                }
                
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Spot analysis failed: {str(e)}"
            )