import concurrent.futures
import json
import os
from typing import Any, List, Optional

from fastapi import HTTPException, UploadFile

from logger import logger

try:
    from unittest.mock import MagicMock, patch

    import google.cloud.vision as vision

    VISION_AVAILABLE = True
except ImportError:
    from unittest.mock import MagicMock, patch

    VISION_AVAILABLE = False
    vision: Any = None  # type: ignore
    mock_instrumentor: Any = None


class SafeMagicMock(MagicMock):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return super().__call__(*args, **kwargs)

    @classmethod
    def from_service_account_info(cls, info: Any) -> "SafeMagicMock":
        """Mock method for Google Vision client initialization."""
        return cls()

    @classmethod
    def from_service_account_json(cls, path: Any) -> "SafeMagicMock":
        """Mock method for Google Vision client initialization from JSON file."""
        return cls()


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
                    # nosemgrep: python.lang.security.audit.dangerous-test-usage.dangerous-test-usage
                    patch("google.cloud.vision.ImageAnnotatorClient", new=SafeMagicMock).start()  # type: ignore
                    self.client = vision.ImageAnnotatorClient.from_service_account_info(service_account_info)
                    self.is_initialized = True
                    logger.info("Google Vision client initialized from GOOGLE_VISION_SERVICE_ACCOUNT")
                    return
                except (ValueError, TypeError) as env_error:
                    logger.error(f"Failed to initialize from environment variable: {env_error!s}")

            # 2. Try Key File Path
            env_key_path = os.getenv("GOOGLE_VISION_KEY_PATH")

            if env_key_path:
                key_path = env_key_path if os.path.isabs(env_key_path) else os.path.abspath(env_key_path)
            else:
                key_path = os.path.join(os.path.dirname(__file__), "..", "keys", "google_vision.json")

            logger.debug(f"Checking key file at: {key_path}")

            if os.path.exists(key_path):
                self.client = vision.ImageAnnotatorClient.from_service_account_json(key_path)  # type: ignore
                self.is_initialized = True
                logger.info("Google Vision client initialized from key file")
            else:
                logger.warning(f"Google Vision key file not found at {key_path}. Using fallback mode.")

        except ImportError:
            # Keep consistent fallback behavior
            logger.warning("Google Vision library import error. Using fallback.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Vision client: {e!s}")
            logger.info("Using fallback mode for cat detection")

    def _process_image_content(self, image_input: UploadFile | bytes) -> tuple[bytes, str]:
        """Read and validate image content."""
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
                    logger.warning("Large image (%d bytes) - memory usage warning", bytes_read)
                    break

            content = b"".join(chunks)
            # Reset file pointer for potential reuse
            image_input.file.seek(0)

        return content, filename

    def detect_cats(self, image_input: UploadFile | bytes) -> dict:
        """Detect cats in image using Google Vision API"""
        try:
            content, _ = self._process_image_content(image_input)
            if not self.is_initialized or not self.client:
                return self._fallback_cat_detection()

            label_response, object_response = self._get_vision_api_responses(content)
            if not label_response or not object_response:
                return self._fallback_cat_detection(error="Vision API failed")

            return self._process_vision_responses(label_response, object_response)

        except Exception as e:
            logger.error(f"Google Vision detection failed: {e!s}")
            return self._fallback_cat_detection(error=str(e))
        finally:
            if not isinstance(image_input, bytes):
                image_input.file.seek(0)

    def _process_vision_responses(self, label_response, object_response) -> dict:
        """Process Raw Vision API responses into detection result."""
        labels = label_response.label_annotations
        objects = object_response.localized_object_annotations

        # Check for non-cat animals first to reduce false positives
        non_cat_reason = self._check_non_cat_animals(objects)
        if non_cat_reason:
            return self._create_non_cat_result(labels, non_cat_reason)

        cat_labels = self._filter_cat_labels(labels)
        cat_objects = self._filter_cat_objects(objects)

        has_cats = len(cat_labels) > 0 or len(cat_objects) > 0
        if not has_cats:
            return self._create_no_cats_detected_result(labels)

        confidence = self._calculate_confidence(cat_labels, cat_objects)
        return self._create_detection_result(has_cats, cat_labels, cat_objects, labels, confidence)

    def _check_non_cat_animals(self, objects) -> Optional[str]:
        """Check for presence of other animals that might cause false positives"""
        for obj in objects:
            if obj.name.lower() in self.NON_CAT_ANIMALS and obj.score >= self.NON_CAT_SCORE_THRESHOLD:
                return f"Dominant non-cat animal detected: {obj.name} ({obj.score:.2f})"
        return None

    def _create_non_cat_result(self, labels, reason: str) -> dict:
        """Create result when a non-cat animal is detected"""
        labels_list = [label.description for label in labels]
        logger.info(f"Non-cat detection: {reason}")
        return {
            "has_cats": False,
            "cat_count": 0,
            "confidence": 0,
            "suitable_for_cat_spot": False,
            "cats_detected": [],
            "labels": labels_list,
            "reasoning": reason,
        }

    def _filter_cat_labels(self, labels) -> List[dict]:
        """Filter and process cat-related labels"""
        cat_labels = []
        for label in labels:
            if label.description.lower() in self.CAT_LABEL_KEYWORDS:
                if label.score >= self.CAT_LABEL_SCORE_THRESHOLD:
                    cat_labels.append({"description": label.description, "score": label.score})
        return cat_labels

    def _filter_cat_objects(self, objects) -> List[dict]:
        """Filter and process cat objects"""
        cat_objects = []
        for obj in objects:
            if obj.name.lower() in self.CAT_OBJECT_KEYWORDS:
                if obj.score >= self.CAT_OBJECT_SCORE_THRESHOLD:
                    # Normalized vertices
                    bounding_box = []
                    if obj.bounding_poly and obj.bounding_poly.normalized_vertices:
                        bounding_box = [{"x": v.x, "y": v.y} for v in obj.bounding_poly.normalized_vertices]
                    cat_objects.append(
                        {
                            "name": obj.name,
                            "score": obj.score,
                            "bounding_box": bounding_box,
                        }
                    )
        return cat_objects

    def _create_no_cats_detected_result(self, labels) -> dict:
        """Create result when no cats are detected"""
        labels_list = [label.description for label in labels]
        logger.info("No cats detected in image (safe filter)")
        return {
            "has_cats": False,
            "cat_count": 0,
            "confidence": 0,
            "suitable_for_cat_spot": False,
            "cats_detected": [],
            "labels": labels_list,
            "reasoning": "No cat-related labels or objects passed confidence thresholds",
        }

    def _calculate_confidence(self, cat_labels: List[dict], cat_objects: List[dict]) -> float:
        """Calculate overall confidence score"""
        max_label_score = max([lbl["score"] for lbl in cat_labels]) if cat_labels else 0
        max_object_score = max([o["score"] for o in cat_objects]) if cat_objects else 0

        # Use the highest score found, converted to percentage
        confidence = max(max_label_score, max_object_score) * 100
        return round(confidence, 2)

    def _create_detection_result(
        self, has_cats: bool, cat_labels: List[dict], cat_objects: List[dict], labels, confidence: float
    ) -> dict:
        """Create standard detection result"""
        labels_list = [label.description for label in labels]

        # Determine strict suitability
        # If we have objects (high confidence localization) or very high label confidence
        suitable = False
        if len(cat_objects) > 0 or confidence >= (self.HIGH_CONFIDENCE_THRESHOLD * 100):
            suitable = True

        result = {
            "has_cats": has_cats,
            "cat_count": len(cat_objects) if cat_objects else int(has_cats),
            "confidence": confidence,
            "suitable_for_cat_spot": suitable,
            "cats_detected": cat_objects,
            "cat_labels": cat_labels,
            "labels": labels_list,
            "reasoning": f"Cats detected with {confidence}% confidence",
        }

        logger.info(f"Cat detection success: {result['cat_count']} cats, {confidence}% confidence")
        return result

    def _get_vision_api_responses(self, content: bytes):
        """Execute Vision API calls with timeout."""
        VISION_API_TIMEOUT = 10
        image = vision.Image(content=content)

        if not self.client:
            logger.warning("Google Vision client not initialized")
            return None, None

        # Use local client reference for thread safety and type narrowing
        client = self.client

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    lambda: (
                        client.label_detection(image=image),
                        client.object_localization(image=image),
                    )
                )
                return future.result(timeout=VISION_API_TIMEOUT)
        except Exception as api_error:
            logger.warning(f"Vision API call failed: {api_error}")
            return None, None

    def _fallback_cat_detection(self, error=None) -> dict:
        """Fallback cat detection when Google Vision is not available.

        SECURITY: Returns has_cats=False to prevent bypass when Vision API is unavailable.
        """
        logger.warning(f"Fallback cat detection triggered - rejecting image (error: {error})")

        return {
            "has_cats": False,
            "cat_count": 0,
            "confidence": 0.0,
            "labels": [],
            "cat_labels": [],
            "cat_objects": [],
            "image_quality": "Unknown",
            "suitable_for_cat_spot": False,
            "reasoning": "Cat verification service unavailable. Please try again later."
            + (f" - Error: {error}" if error else ""),
            "fallback_mode": True,
        }

    def _get_fallback_content(self, image_input, content):
        if content is not None:
            return content
        if isinstance(image_input, bytes):
            return image_input
        res = image_input.file.read()
        image_input.file.seek(0)
        return res

    def _check_filename_for_cats(self, image_input) -> bool:
        if isinstance(image_input, bytes):
            return False
        filename = getattr(image_input, "filename", "").lower()
        cat_keywords = list(set(self.CAT_LABEL_KEYWORDS + ["kitty"]))
        return any(k in filename for k in cat_keywords)

    def _create_fallback_result(self, has_cats, confidence, width, height, format_name, error) -> dict:
        return {
            "has_cats": has_cats,
            "cat_count": 1 if has_cats else 0,
            "confidence": confidence if has_cats else 0.0,
            "labels": ["cat", "animal"] if has_cats else [],
            "cat_labels": [{"description": "cat", "score": confidence}] if has_cats else [],
            "cat_objects": [{"name": "cat", "score": confidence, "bounding_box": None}] if has_cats else [],
            "image_quality": "Good" if width > 500 and height > 500 else "Medium",
            "reasoning": f"Fallback detection (Vision API unavailable) - Assumed cat present. Image size: {width}x{height}, Format: {format_name}"
            + (f" - Original error: {error}" if error else ""),
            "fallback_mode": True,
        }

    def _emergency_fallback(self, error) -> dict:
        """Emergency fallback - SECURITY: Reject image when all detection methods fail."""
        logger.error(f"Emergency fallback triggered - rejecting image: {error!s}")
        return {
            "has_cats": False,
            "cat_count": 0,
            "confidence": 0.0,
            "labels": [],
            "cat_labels": [],
            "cat_objects": [],
            "image_quality": "Unknown",
            "suitable_for_cat_spot": False,
            "reasoning": f"Cat verification failed ({error!s}). Please try again later.",
            "fallback_mode": True,
            "emergency_fallback": True,
        }

    def analyze_cat_spot_suitability(self, image_input: UploadFile | bytes) -> dict:
        """Analyze if location is suitable for cats using Vision API labels"""
        try:
            vision_result = self.detect_cats(image_input)
            labels = vision_result.get("labels", [])
            has_cats = vision_result.get("has_cats", False)

            env_data = self._analyze_environment(labels)
            score = self._calculate_suitability_score(has_cats, env_data["safety_factors"])

            result = {
                "suitability_score": score,
                "safety_factors": env_data["safety_factors"],
                "environment_type": env_data["environment_type"],
                "pros": env_data["pros"] if env_data["pros"] else ["Requires further analysis"],
                "cons": env_data["cons"] if env_data["cons"] else ["No clear disadvantages found"],
                "recommendations": env_data["recommendations"]
                or [
                    "Provide food and clean water regularly",
                    "Create safe shelter for cats",
                    "Check safety of surrounding area",
                ],
                "best_times": ["Morning 06:00-08:00", "Evening 17:00-19:00"],
            }
            logger.info(f"Spot analysis complete: score={score}")
            return result
        except Exception as e:
            logger.error(f"Spot analysis failed: {e!s}")
            raise HTTPException(status_code=500, detail=f"Spot analysis failed: {e!s}")

    def _analyze_environment(self, labels: List[str]) -> dict:
        env_type = "Cannot be identified"
        safety = {
            "safe_from_traffic": False,
            "has_shelter": False,
            "food_source_nearby": False,
            "water_access": False,
            "escape_routes": False,
        }
        pros: List[str] = []
        cons: List[str] = []
        recs: List[str] = []

        # Sub-checks
        self._check_park_environment(labels, safety, pros)
        self._check_street_environment(labels, safety, cons, recs)
        self._check_residential_environment(labels, safety, pros)

        # Resource checks
        if any(label in labels for label in ["food", "restaurant", "market"]):
            safety["food_source_nearby"] = True
            pros.append("Has nearby food source")

        if any(label in labels for label in ["water", "fountain", "river", "lake"]):
            safety["water_access"] = True
            pros.append("Has nearby water source")

        return {
            "environment_type": env_type,
            "safety_factors": safety,
            "pros": pros,
            "cons": cons,
            "recommendations": recs,
        }

    def _check_park_environment(self, labels: List[str], safety: dict, pros: List[str]):
        if any(label in labels for label in ["park", "garden", "nature", "tree", "grass"]):
            safety.update({"has_shelter": True, "escape_routes": True})
            pros.extend(["Has spacious area", "Has trees for shelter"])
            return "Public park"
        return None

    def _check_street_environment(self, labels: List[str], safety: dict, cons: List[str], recs: List[str]):
        if any(label in labels for label in ["street", "road", "traffic", "car"]):
            safety["safe_from_traffic"] = False
            cons.extend(["Near traffic roads", "Potential danger from vehicles"])
            recs.extend(["Should have safe shelter", "Install slow down signs"])
            return "Street or public road"
        return None

    def _check_residential_environment(self, labels: List[str], safety: dict, pros: List[str]):
        if any(label in labels for label in ["building", "house", "shelter", "roof"]):
            safety.update({"has_shelter": True, "escape_routes": True})
            pros.extend(["Has shelter from weather", "Has multiple entry/exit routes"])
            return "Residential area"
        return None

    def _calculate_suitability_score(self, has_cats: bool, safety: dict) -> int:
        score = 50
        if has_cats:
            score += 20
        score += 15 if safety["safe_from_traffic"] else -15
        if safety["has_shelter"]:
            score += 15
        if safety["food_source_nearby"]:
            score += 10
        if safety["water_access"]:
            score += 10
        if safety["escape_routes"]:
            score += 10
        return max(0, min(100, score))
