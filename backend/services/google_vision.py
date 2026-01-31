"""
Google Cloud Vision API service for cat detection
"""

import json

try:
    import google.cloud.vision as vision

    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    vision = None
import os

from fastapi import HTTPException, UploadFile

from logger import logger


class GoogleVisionService:
    # Detection Thresholds
    CAT_LABEL_KEYWORDS = ["cat", "kitten", "feline", "cat", "meow"]
    CAT_LABEL_SCORE_THRESHOLD = 0.6
    CAT_OBJECT_KEYWORDS = ["cat", "kitten"]
    CAT_OBJECT_SCORE_THRESHOLD = 0.6
    NON_CAT_ANIMALS = ["dog", "puppy", "canine", "bird", "reptile", "rodent"]
    NON_CAT_SCORE_THRESHOLD = 0.7
    HIGH_CONFIDENCE_THRESHOLD = 0.75

    def __init__(self):
        """Initialize Google Vision client"""
        self.client = None
        self.is_initialized = False

        if not VISION_AVAILABLE:
            logger.warning("Google Vision library not available, using fallback mode")
            return

        try:
            # 1. Try Environment Variable (JSON Content) - Preferred for Deployment
            service_account_json = os.getenv("GOOGLE_VISION_SERVICE_ACCOUNT")
            if service_account_json:
                try:
                    service_account_info = json.loads(service_account_json)
                    self.client = vision.ImageAnnotatorClient.from_service_account_info(service_account_info)
                    self.is_initialized = True
                    logger.info("Google Vision client initialized from GOOGLE_VISION_SERVICE_ACCOUNT")
                    return
                except Exception as env_error:
                    logger.error(f"Failed to initialize from environment variable: {env_error!s}")

            # 2. Try Key File Path
            env_key_path = os.getenv("GOOGLE_VISION_KEY_PATH")

            if env_key_path:
                key_path = env_key_path if os.path.isabs(env_key_path) else os.path.abspath(env_key_path)
            else:
                key_path = os.path.join(os.path.dirname(__file__), "..", "keys", "google_vision.json")

            logger.debug(f"Checking key file at: {key_path}")

            if os.path.exists(key_path):
                self.client = vision.ImageAnnotatorClient.from_service_account_json(key_path)
                self.is_initialized = True
                logger.info("Google Vision client initialized from key file")
            else:
                logger.warning(f"Google Vision key file not found at {key_path}. Using fallback mode.")

        except Exception as e:
            logger.error(f"Failed to initialize Google Vision client: {e!s}")
            logger.info("Using fallback mode for cat detection")

    def detect_cats(self, image_input: UploadFile | bytes) -> dict:
        """
        Detect cats in image using Google Vision API

        Args:
            image_input: UploadFile object or raw bytes

        Returns:
            Dict containing detection results
        """
        try:
            filename = "unknown"
            content = b""

            if isinstance(image_input, bytes):
                content = image_input
                filename = "raw_bytes"
                logger.debug(f"Cat detection started for raw bytes, size={len(content)}")
            else:
                filename = getattr(image_input, "filename", "unknown")
                logger.debug(f"Cat detection started for: {filename}, initialized={self.is_initialized}")

                # Read image content with memory-efficient chunked reading for large files
                MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB threshold
                chunks = []
                bytes_read = 0

                # Ensure we are at start of file
                image_input.file.seek(0)

                while True:
                    chunk = image_input.file.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    chunks.append(chunk)
                    bytes_read += len(chunk)

                    # Safety check for very large files
                    if bytes_read > MAX_MEMORY_SIZE:
                        logger.warning(f"Image exceeds {MAX_MEMORY_SIZE} bytes, may impact memory")
                        break

                content = b"".join(chunks)
                # Reset file pointer for potential reuse
                image_input.file.seek(0)

            # If client is not initialized, use fallback detection
            if not self.is_initialized or not self.client:
                logger.debug("Using fallback cat detection (Google Vision not available)")
                return self._fallback_cat_detection(image_input, content=content)

            logger.debug(f"Image size: {len(content)} bytes")

            image = vision.Image(content=content)

            # Send to Vision API with timeout to prevent hanging
            import concurrent.futures

            VISION_API_TIMEOUT = 10  # seconds

            def call_vision_api():
                label_resp = self.client.label_detection(image=image)
                object_resp = self.client.object_localization(image=image)
                return label_resp, object_resp

            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(call_vision_api)
                    label_response, object_response = future.result(timeout=VISION_API_TIMEOUT)
            except concurrent.futures.TimeoutError:
                logger.warning(f"Google Vision API timed out after {VISION_API_TIMEOUT}s, using fallback")
                return self._fallback_cat_detection(image_input, error="Vision API timeout")
            except Exception as api_error:
                logger.warning(f"Google Vision API call failed: {api_error}, using fallback")
                return self._fallback_cat_detection(image_input, error=str(api_error))

            logger.debug("Received response from Google Vision API")

            if label_response.error.message:
                logger.error(f"Label detection error: {label_response.error.message}")
                raise Exception(f"Vision API error: {label_response.error.message}")

            if object_response.error.message:
                logger.error(f"Object localization error: {object_response.error.message}")
                raise Exception(f"Vision API error: {object_response.error.message}")

            labels = label_response.label_annotations
            objects = object_response.localized_object_annotations

            logger.debug(f"Found {len(labels)} labels and {len(objects)} objects")
            logger.debug(f"Labels: {[label.description for label in labels]}")
            logger.debug(f"Objects: {[obj.name for obj in objects]}")

            # Check for cat-specific labels only
            cat_labels = [
                label
                for label in labels
                if any(keyword in label.description.lower() for keyword in self.CAT_LABEL_KEYWORDS)
                and label.score > self.CAT_LABEL_SCORE_THRESHOLD
            ]

            # Count cat objects for more accurate detection
            cat_objects = [
                obj
                for obj in objects
                if obj.name.lower() in self.CAT_OBJECT_KEYWORDS and obj.score > self.CAT_OBJECT_SCORE_THRESHOLD
            ]

            logger.debug(f"Cat labels: {len(cat_labels)}, Cat objects: {len(cat_objects)}")

            # Check for objects that are NOT cats (dogs, etc.) to reduce false positives
            non_cat_animals = [
                obj
                for obj in objects
                if obj.name.lower() in self.NON_CAT_ANIMALS and obj.score > self.NON_CAT_SCORE_THRESHOLD
            ]

            # If high confidence non-cat animals detected, reduce cat detection confidence
            if non_cat_animals:
                logger.info(f"Non-cat animals detected: {[obj.name for obj in non_cat_animals]}")
                result = {
                    "has_cats": False,
                    "cat_count": 0,
                    "confidence": 0.0,
                    "labels": [label.description for label in labels],
                    "cat_labels": [],
                    "cat_objects": [],
                    "image_quality": "Good",
                    "reasoning": f"Detected other animals (e.g., {non_cat_animals[0].name}) not cats",
                }
                return result

            has_high_confidence_labels = any(label.score > self.HIGH_CONFIDENCE_THRESHOLD for label in cat_labels)
            has_high_confidence_objects = any(obj.score > self.HIGH_CONFIDENCE_THRESHOLD for obj in cat_objects)

            logger.debug(
                f"High confidence - labels: {has_high_confidence_labels}, objects: {has_high_confidence_objects}"
            )

            # Consider labels or objects as sufficient for cat detection
            has_cats = len(cat_labels) > 0 or len(cat_objects) > 0

            # Count cats from objects if available, otherwise from labels
            if len(cat_objects) > 0:
                cat_count = len(cat_objects)
            elif len(cat_labels) > 0:
                cat_count = len(cat_labels)
            else:
                cat_count = 0

            # Calculate confidence from both labels and objects
            label_confidence = max([label.score for label in cat_labels], default=0.0)
            object_confidence = max([obj.score for obj in cat_objects], default=0.0)
            confidence = max(label_confidence, object_confidence) * 100

            # Reduce confidence slightly if only labels detected, no objects
            if len(cat_objects) == 0 and len(cat_labels) > 0:
                confidence = confidence * 0.85
                logger.debug(f"Confidence reduced (labels only): {confidence:.2f}%")

            # Determine image quality based on detection confidence
            if confidence >= 85:
                image_quality = "Good"
            elif confidence >= 75:
                image_quality = "Medium"
            else:
                image_quality = "Poor"

            result = {
                "has_cats": has_cats,
                "cat_count": cat_count,
                "confidence": round(confidence, 2),
                "labels": [label.description for label in labels],
                "cat_labels": [
                    {
                        "description": label.description,
                        "score": round(label.score * 100, 2),
                    }
                    for label in cat_labels
                ],
                "cat_objects": [
                    {
                        "name": obj.name,
                        "score": round(obj.score * 100, 2),
                        "bounding_box": {
                            "normalized_vertices": [
                                {"x": vertex.x, "y": vertex.y} for vertex in obj.bounding_poly.normalized_vertices
                            ]
                        },
                    }
                    for obj in cat_objects
                ],
                "image_quality": image_quality,
                "reasoning": f"Detected cats from Google Cloud Vision API with {round(confidence, 2)}% confidence",
            }

            logger.info(f"Detection complete: has_cats={has_cats}, count={cat_count}, confidence={confidence:.2f}%")
            return result

        except Exception as e:
            logger.error(f"Google Vision detection failed: {type(e).__name__}: {e!s}")
            return self._fallback_cat_detection(image_input, error=str(e))
        finally:
            # Reset file pointer for potential reuse
            if not isinstance(image_input, bytes):
                image_input.file.seek(0)

    def _fallback_cat_detection(self, image_input, error=None, content=None) -> dict:
        """
        Fallback cat detection when Google Vision is not available.
        This is more permissive to allow uploads when Vision API is unavailable,
        since the frontend has already validated the image contains cats.
        """
        try:
            logger.debug(f"Starting fallback cat detection (error: {error})")

            # Read image content if not provided
            if content is None:
                if isinstance(image_input, bytes):
                    content = image_input
                else:
                    content = image_input.file.read()
                    image_input.file.seek(0)

            logger.debug(f"Fallback processing image: {len(content)} bytes")

            # Basic image analysis using PIL
            import io

            from PIL import Image

            img = Image.open(io.BytesIO(content))

            # Get image dimensions and format
            width, height = img.size
            format_name = img.format

            logger.debug(f"Image dimensions: {width}x{height}, format: {format_name}")

            # Simple heuristic: check filename for cat keywords
            filename = ""
            if not isinstance(image_input, bytes):
                filename = getattr(image_input, "filename", "").lower()

            cat_keywords = list(set(self.CAT_LABEL_KEYWORDS + ["kitty"]))

            filename_has_cat = any(keyword in filename for keyword in cat_keywords)
            logger.debug(f"Filename '{filename}' contains cat keywords: {filename_has_cat}")

            # IMPORTANT: In fallback mode, be permissive and assume it's a cat
            # The frontend has already validated the image, so we trust it.
            # Only reject if the image is clearly problematic (very small, etc.)
            is_valid_image = width >= 50 and height >= 50

            # Always assume cats present in fallback mode if image is valid
            # This prevents blocking legitimate uploads when Vision API is unavailable
            has_cats = is_valid_image
            confidence = 75.0 if filename_has_cat else 60.0  # Higher default confidence

            result = {
                "has_cats": has_cats,
                "cat_count": 1 if has_cats else 0,
                "confidence": confidence if has_cats else 0.0,
                "labels": ["cat", "animal"] if has_cats else [],
                "cat_labels": [{"description": "cat", "score": confidence}] if has_cats else [],
                "cat_objects": [
                    {
                        "name": "cat",
                        "score": confidence,
                        "bounding_box": None,
                    }
                ]
                if has_cats
                else [],
                "image_quality": "Good" if width > 500 and height > 500 else "Medium",
                "reasoning": f"Fallback detection (Vision API unavailable) - Assumed cat present. Image size: {width}x{height}, Format: {format_name}"
                + (f" - Original error: {error}" if error else ""),
                "fallback_mode": True,
            }

            logger.info(f"Fallback detection complete: has_cats={has_cats}, confidence={confidence}")
            return result

        except Exception as fallback_error:
            logger.error(f"Fallback detection also failed: {fallback_error!s}")
            # Even in complete failure, be permissive for development
            # The upload will still be validated by other checks
            return {
                "has_cats": True,  # Allow upload to proceed
                "cat_count": 1,
                "confidence": 50.0,
                "labels": ["cat"],
                "cat_labels": [{"description": "cat", "score": 50.0}],
                "cat_objects": [],
                "image_quality": "Unknown",
                "reasoning": f"Emergency fallback: Both Vision API and image analysis failed ({fallback_error!s}). Allowing upload.",
                "fallback_mode": True,
                "emergency_fallback": True,
            }

    def analyze_cat_spot_suitability(self, image_input: UploadFile | bytes) -> dict:
        """
        Analyze if location is suitable for cats using Vision API labels
        """
        try:
            # Use Google Vision API to detect objects and labels
            vision_result = self.detect_cats(image_input)

            # Analyze the environment based on detected labels
            labels = vision_result.get("labels", [])
            has_cats = vision_result.get("has_cats", False)

            # Environment analysis based on labels
            environment_type = "Cannot be identified"
            safety_factors = {
                "safe_from_traffic": False,
                "has_shelter": False,
                "food_source_nearby": False,
                "water_access": False,
                "escape_routes": False,
            }

            pros = []
            cons = []
            recommendations = []
            best_times = ["Morning 06:00-08:00", "Evening 17:00-19:00"]

            # Analyze labels to determine environment type and safety factors
            if any(label in labels for label in ["park", "garden", "nature", "tree", "grass"]):
                environment_type = "Public park"
                safety_factors["has_shelter"] = True
                safety_factors["escape_routes"] = True
                pros.extend(["Has spacious area", "Has trees for shelter"])

            if any(label in labels for label in ["street", "road", "traffic", "car"]):
                environment_type = "Street or public road"
                safety_factors["safe_from_traffic"] = False
                cons.extend(["Near traffic roads", "Potential danger from vehicles"])
                recommendations.extend(["Should have safe shelter", "Install slow down signs"])

            if any(label in labels for label in ["building", "house", "shelter", "roof"]):
                environment_type = "Residential area"
                safety_factors["has_shelter"] = True
                safety_factors["escape_routes"] = True
                pros.extend(["Has shelter from weather", "Has multiple entry/exit routes"])

            if any(label in labels for label in ["food", "restaurant", "market"]):
                safety_factors["food_source_nearby"] = True
                pros.extend(["Has nearby food source"])

            if any(label in labels for label in ["water", "fountain", "river", "lake"]):
                safety_factors["water_access"] = True
                pros.extend(["Has nearby water source"])

            # Calculate suitability score
            score = 50  # Base score

            if has_cats:
                score += 20  # Bonus if cats are already present

            # Add/subtract based on safety factors
            if safety_factors["safe_from_traffic"]:
                score += 15
            else:
                score -= 15

            if safety_factors["has_shelter"]:
                score += 15

            if safety_factors["food_source_nearby"]:
                score += 10

            if safety_factors["water_access"]:
                score += 10

            if safety_factors["escape_routes"]:
                score += 10

            # Ensure score is within 0-100 range
            suitability_score = max(0, min(100, score))

            # Add general recommendations if none were added
            if not recommendations:
                recommendations = [
                    "Provide food and clean water regularly",
                    "Create safe shelter for cats",
                    "Check safety of surrounding area",
                ]

            logger.info(f"Spot analysis complete: score={suitability_score}, environment={environment_type}")

            return {
                "suitability_score": suitability_score,
                "safety_factors": safety_factors,
                "environment_type": environment_type,
                "pros": pros if pros else ["Requires further analysis"],
                "cons": cons if cons else ["No clear disadvantages found"],
                "recommendations": recommendations,
                "best_times": best_times,
            }

        except Exception as e:
            logger.error(f"Spot analysis failed: {e!s}")
            raise HTTPException(status_code=500, detail=f"Spot analysis failed: {e!s}")
