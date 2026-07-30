import hashlib
import io
from typing import Any, cast

from fastapi import HTTPException, UploadFile
from PIL import Image

from app.logger import logger

# Set explicit max pixel limit to prevent Decompression Bomb Attacks
Image.MAX_IMAGE_PIXELS = 89_478_485

_detection_cache: dict[str, dict[str, Any]] = {}


def clear_detection_cache() -> None:
    _detection_cache.clear()


def _compute_perceptual_hash(image_bytes: bytes) -> str | None:
    """Compute 64-bit average perceptual hash (aHash) for image similarity deduplication"""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("L").resize((8, 8), Image.Resampling.BILINEAR)
            pixels = list(img.getdata())
            avg = sum(pixels) / 64.0
            bits = "".join("1" if p > avg else "0" for p in pixels)
            return f"phash_{int(bits, 2):016x}"
    except Exception:
        return None


class CatDetectionService:
    """Service for cat detection and spot analysis using Google Cloud Vision API"""

    def __init__(self, vision_service: Any = None) -> None:
        """Initialize the service"""
        if vision_service:
            self.vision_service = vision_service
        else:
            from app.services.google_vision import GoogleVisionService

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

    async def detect_cats(self, file: UploadFile | bytes) -> dict[str, Any]:
        """
        Detect cats in image using Google Cloud Vision API (Async)

        Args:
            file: UploadFile object or raw bytes

        Returns:
            Dict containing detection results
        """
        try:
            # Check cache by image hash & perceptual hash first to avoid duplicate Vision API cost
            content_bytes: bytes | None = None
            if isinstance(file, (bytes, bytearray)):
                content_bytes = bytes(file)
            elif isinstance(file, UploadFile):
                try:
                    content_bytes = await file.read()
                    await file.seek(0)
                except Exception:
                    content_bytes = None

            image_hash = (
                hashlib.sha256(content_bytes).hexdigest()
                if isinstance(content_bytes, (bytes, bytearray)) and len(content_bytes) > 0
                else None
            )
            phash = _compute_perceptual_hash(content_bytes) if content_bytes else None

            if image_hash and image_hash in _detection_cache:
                logger.info("Cat detection cache hit for SHA256 hash")
                return _detection_cache[image_hash]
            if phash and phash in _detection_cache:
                logger.info("Cat detection cache hit for perceptual hash")
                return _detection_cache[phash]

            # Use Google Vision API to detect cats
            vision_result = await self.vision_service.detect_cats(file)

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
            fallback_active = bool(
                vision_result.get("fallback_mode")
                or vision_result.get("fallback_active")
                or vision_result.get("emergency_fallback")
            )
            result = {
                "has_cats": vision_result.get("has_cats", False),
                "cat_count": vision_result.get("cat_count", 0),
                "confidence": int(vision_result.get("confidence", 0)),
                "cats_detected": cats_detected,
                "image_quality": vision_result.get("image_quality", "Medium"),
                "suitable_for_cat_spot": vision_result.get("has_cats", False),
                "reasoning": vision_result.get("reasoning", "Cannot analyze"),
                "service_available": not fallback_active,
                "fallback_active": fallback_active,
            }

            if result.get("service_available"):
                if image_hash:
                    _detection_cache[image_hash] = result
                if phash:
                    _detection_cache[phash] = result

            return result

        except Exception as e:
            logger.error(f"Cat detection failed: {e}")
            # Fail closed when verification is unavailable.
            return {
                "has_cats": False,
                "cat_count": 0,
                "confidence": 0,
                "cats_detected": [],
                "image_quality": "Unknown",
                "suitable_for_cat_spot": False,
                "reasoning": "Cat verification service unavailable. Please try again later.",
                "service_available": False,
                "fallback_active": True,
            }

    async def analyze_cat_spot_suitability(self, file: UploadFile | bytes) -> dict[str, Any]:
        """
        Analyze spot suitability for cats using Google Cloud Vision (Async)

        Args:
            file: UploadFile object or raw bytes

        Returns:
            Dict containing suitability analysis
        """
        try:
            # Use Google Vision API to analyze spot suitability
            return cast(dict[str, Any], await self.vision_service.analyze_cat_spot_suitability(file))

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Spot analysis failed: {e!s}")


# Singleton instance
cat_detection_service = CatDetectionService()


def get_cat_detection_service() -> CatDetectionService:
    """Get service instance"""
    return cat_detection_service
