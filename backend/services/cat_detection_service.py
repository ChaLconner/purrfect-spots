"""
Service for cat detection and spot analysis using Google Cloud Vision API
"""

import io
from typing import Any

from fastapi import HTTPException, UploadFile
from PIL import Image


class CatDetectionService:
    """Service for cat detection and spot analysis using Google Cloud Vision API"""

    def __init__(self) -> None:
        """Initialize the service"""
        from services.google_vision import GoogleVisionService

        self.vision_service = GoogleVisionService()

    def prepare_image(self, image_data: bytes) -> Image.Image:
        """Prepare image for analysis"""
        try:
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize if too large (max 1024x1024)
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            from PIL import UnidentifiedImageError

            if isinstance(e, UnidentifiedImageError):
                raise HTTPException(status_code=400, detail="Invalid image file format")
            raise HTTPException(status_code=400, detail=f"Image processing failed: {e!s}")

    def detect_cats(self, file: UploadFile | bytes) -> dict[str, Any]:
        """
        Detect cats in image using Google Cloud Vision API

        Args:
            file: UploadFile object or raw bytes

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
                    cats_detected.append(
                        {
                            "description": f"Detected {obj.get('name', 'cat')}",
                            "breed_guess": "Domestic cat",
                            "position": "Center of image",
                            "size": "Medium",
                        }
                    )
            elif vision_result.get("cat_labels"):
                for label in vision_result.get("cat_labels", []):
                    cats_detected.append(
                        {
                            "description": f"Detected {label.get('description', 'cat')}",
                            "breed_guess": "Domestic cat",
                            "position": "Center of image",
                            "size": "Medium",
                        }
                    )

            # Format the result
            return {
                "has_cats": vision_result.get("has_cats", False),
                "cat_count": vision_result.get("cat_count", 0),
                "confidence": int(vision_result.get("confidence", 0)),
                "cats_detected": cats_detected,
                "image_quality": vision_result.get("image_quality", "Medium"),
                "suitable_for_cat_spot": vision_result.get("has_cats", False),
                "reasoning": vision_result.get("reasoning", "Cannot analyze"),
            }


        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Cat detection failed: {e!s}")

    def analyze_cat_spot_suitability(self, file: UploadFile | bytes) -> dict[str, Any]:
        """
        Analyze spot suitability for cats using Google Cloud Vision

        Args:
            file: UploadFile object or raw bytes

        Returns:
            Dict containing suitability analysis
        """
        try:
            # Use Google Vision API to analyze spot suitability
            return self.vision_service.analyze_cat_spot_suitability(file)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Spot analysis failed: {e!s}")


# Singleton instance
cat_detection_service = CatDetectionService()
