import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.config import config
from app.logger import logger
from app.utils.supabase_client import get_async_supabase_admin_client

try:
    import google.cloud.vision as vision

    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    vision: Any = None  # type: ignore


class GoogleVisionService:
    # Detection Thresholds
    CAT_LABEL_KEYWORDS = ["cat", "kitten", "feline", "cat", "meow"]
    CAT_LABEL_SCORE_THRESHOLD = 0.6
    CAT_OBJECT_KEYWORDS = ["cat", "kitten"]
    CAT_OBJECT_SCORE_THRESHOLD = 0.6
    NON_CAT_ANIMALS = ["dog", "puppy", "canine", "bird", "reptile", "rodent"]
    NON_CAT_SCORE_THRESHOLD = 0.7
    HIGH_CONFIDENCE_THRESHOLD = 0.75

    def __init__(self) -> None:
        """Initialize Google Vision client"""
        self.client = None
        self.is_initialized = False
        self._inflight_tasks: dict[str, asyncio.Task[dict[str, Any]]] = {}

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
                except (ValueError, TypeError, KeyError) as env_error:
                    logger.error(f"Failed to initialize from environment variable: {env_error!s}")

            # 2. Try Key File Path
            env_key_path = os.getenv("GOOGLE_VISION_KEY_PATH")

            if env_key_path:
                key_path = Path(env_key_path).resolve()
            else:
                # Default location: backend/keys/google_vision.json
                key_path = Path(__file__).parent.parent / "keys" / "google_vision.json"

            if key_path.exists():
                self.client = vision.ImageAnnotatorClient.from_service_account_json(str(key_path))
                self.is_initialized = True
                logger.info("Google Vision client initialized from key file")
            else:
                if env_key_path:
                    logger.warning(f"Google Vision key file not found at {key_path}")
                elif config.is_production():
                    logger.info("Google Vision API not configured (no service account or key file found)")
                else:
                    logger.debug(f"Google Vision key file not found at {key_path}")

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

    def _calculate_image_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of image content."""
        return hashlib.sha256(content).hexdigest()

    async def _get_cached_result(self, image_hash: str) -> dict | None:
        """Try to retrieve cached analysis result. (Async)"""
        try:
            client = await get_async_supabase_admin_client()
            response = (
                await client.table("vision_analysis_cache")
                .select("response")
                .eq("image_hash", image_hash)
                .maybe_single()
                .execute()
            )
            if response and hasattr(response, "data") and response.data:
                logger.info(f"Vision API Cache Hit: {image_hash[:8]}...")
                from typing import Any, cast

                data = cast(dict[str, Any], response.data)
                return cast(dict[str, Any] | None, data["response"])
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        return None

    async def _cache_result(self, image_hash: str, result: dict) -> None:
        """Cache analysis result. (Async)"""
        try:
            client = await get_async_supabase_admin_client()
            await client.table("vision_analysis_cache").upsert({"image_hash": image_hash, "response": result}).execute()
            logger.debug(f"Cached vision result for {image_hash[:8]}...")
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    async def detect_cats(self, image_input: UploadFile | bytes) -> dict:
        """Detect cats in image using Google Vision API (Async)"""
        try:
            content, _ = self._process_image_content(image_input)
            # 1. Check Cache
            image_hash = self._calculate_image_hash(content)
            cached_result = await self._get_cached_result(image_hash)
            if cached_result:
                return cached_result

            existing_task = self._inflight_tasks.get(image_hash)
            if existing_task is not None:
                return await asyncio.shield(existing_task)

            task = asyncio.create_task(self._detect_uncached(content, image_hash))
            self._inflight_tasks[image_hash] = task
            try:
                # A cancelled request must not cancel shared work needed by
                # other callers waiting for the same image hash.
                return await asyncio.shield(task)
            finally:
                if self._inflight_tasks.get(image_hash) is task:
                    self._inflight_tasks.pop(image_hash, None)

        except Exception as e:
            logger.error(f"Google Vision detection failed: {e!s}")
            return self._fallback_cat_detection(error=str(e))
        finally:
            if not isinstance(image_input, bytes):
                image_input.file.seek(0)

    async def _detect_uncached(self, content: bytes, image_hash: str) -> dict[str, Any]:
        """Run one uncached Vision request for a content hash."""
        if not self.is_initialized or not self.client:
            return self._fallback_cat_detection()

        label_response, object_response = await self._get_vision_api_responses(content)
        if not label_response or not object_response:
            return self._fallback_cat_detection(error="Vision API failed")

        result = self._process_vision_responses(label_response, object_response)
        await self._cache_result(image_hash, result)
        return result

    def _process_vision_responses(self, label_response: Any, object_response: Any) -> dict:
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

    def _filter_cat_labels(self, labels: Any) -> list[dict]:
        cat_labels = []
        for label in labels:
            desc = getattr(label, "description", "").lower()
            score = getattr(label, "score", 0.0)
            if any(kw in desc for kw in self.CAT_LABEL_KEYWORDS) and score >= self.CAT_LABEL_SCORE_THRESHOLD:
                cat_labels.append({"description": getattr(label, "description", ""), "score": score})
        return cat_labels

    def _filter_cat_objects(self, objects: Any) -> list[dict]:
        cat_objects = []
        for obj in objects:
            name = getattr(obj, "name", "").lower()
            score = getattr(obj, "score", 0.0)
            if any(kw in name for kw in self.CAT_OBJECT_KEYWORDS) and score >= self.CAT_OBJECT_SCORE_THRESHOLD:
                cat_objects.append({"name": getattr(obj, "name", ""), "score": score})
        return cat_objects

    def _check_non_cat_animals(self, objects: Any) -> str | None:
        """Check for presence of other animals that might cause false positives"""
        for obj in objects:
            if obj.name.lower() in self.NON_CAT_ANIMALS and obj.score >= self.NON_CAT_SCORE_THRESHOLD:
                return f"Dominant non-cat animal detected: {obj.name} ({obj.score:.2f})"
        return None

    def _create_negative_result(self, labels: Any, reason: str, log_message: str | None = None) -> dict:
        """Create result when no cats or non-cat animals are detected."""
        labels_list = [label.description for label in labels]
        if log_message:
            logger.info(log_message)
        return {
            "has_cats": False,
            "cat_count": 0,
            "confidence": 0,
            "suitable_for_cat_spot": False,
            "cats_detected": [],
            "labels": labels_list,
            "reasoning": reason,
        }

    def _create_non_cat_result(self, labels: Any, reason: str) -> dict:
        """Create result when a non-cat animal is detected"""
        return self._create_negative_result(labels, reason, log_message=f"Non-cat detection: {reason}")

    def _create_no_cats_detected_result(self, labels: Any) -> dict:
        """Create result when no cats are detected"""
        return self._create_negative_result(
            labels,
            "No cat-related labels or objects passed confidence thresholds",
            log_message="No cats detected in image (safe filter)",
        )

    def _calculate_confidence(self, cat_labels: list[dict], cat_objects: list[dict]) -> float:
        """Calculate overall confidence score"""
        max_label_score = max([lbl["score"] for lbl in cat_labels]) if cat_labels else 0
        max_object_score = max([o["score"] for o in cat_objects]) if cat_objects else 0

        # Use the highest score found, converted to percentage
        confidence = max(max_label_score, max_object_score) * 100
        return round(confidence, 2)

    def _create_detection_result(
        self, has_cats: bool, cat_labels: list[dict], cat_objects: list[dict], labels: Any, confidence: float
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

    async def _get_vision_api_responses(self, content: bytes) -> tuple[Any, Any] | tuple[None, None]:
        """Execute Vision API calls with timeout (Async/Non-blocking)."""
        VISION_API_TIMEOUT = 10
        image = vision.Image(content=content)

        if not self.client:
            logger.warning("Google Vision client not initialized")
            return None, None

        # Use local client reference for thread safety and type narrowing
        client = self.client

        try:
            # Execute both calls in parallel using thread pool to avoid blocking ASGI loop
            label_task = run_in_threadpool(client.label_detection, image=image)
            object_task = run_in_threadpool(client.object_localization, image=image)

            # Wait for both with a timeout
            results = await asyncio.wait_for(asyncio.gather(label_task, object_task), timeout=VISION_API_TIMEOUT)

            return results[0], results[1]

        except TimeoutError:
            logger.warning("Vision API call timed out")
            return None, None
        except Exception as api_error:
            logger.warning(f"Vision API call failed: {api_error}")
            return None, None

    def _rejected_fallback_dict(self, reasoning: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        """Helper to construct rejected fallback responses."""
        res = {
            "has_cats": False,
            "cat_count": 0,
            "confidence": 0.0,
            "labels": [],
            "cat_labels": [],
            "cat_objects": [],
            "image_quality": "Unknown",
            "suitable_for_cat_spot": False,
            "reasoning": reasoning,
            "fallback_mode": True,
        }
        if extra:
            res.update(extra)
        return res

    def _fallback_cat_detection(self, error: str | None = None) -> dict:
        """Fallback cat detection when Google Vision is not available."""
        logger.warning(f"Fallback cat detection triggered - rejecting image (error: {error})")
        reasoning = "Cat verification service unavailable. Please try again later." + (
            f" - Error: {error}" if error else ""
        )
        return self._rejected_fallback_dict(reasoning)

    def _emergency_fallback(self, error: Any) -> dict:
        """Emergency fallback - SECURITY: Reject image when all detection methods fail."""
        logger.error(f"Emergency fallback triggered - rejecting image: {error!s}")
        reasoning = f"Cat verification failed ({error!s}). Please try again later."
        return self._rejected_fallback_dict(reasoning, {"emergency_fallback": True})

    async def analyze_cat_spot_suitability(self, image_input: UploadFile | bytes) -> dict:
        """Analyze if location is suitable for cats using Vision API labels (Async)"""
        try:
            vision_result = await self.detect_cats(image_input)
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

    def _analyze_environment(self, labels: list[str]) -> dict:
        env_type = "Cannot be identified"
        safety = {
            "safe_from_traffic": False,
            "has_shelter": False,
            "food_source_nearby": False,
            "water_access": False,
            "escape_routes": False,
        }
        pros: list[str] = []
        cons: list[str] = []
        recs: list[str] = []

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

    def _check_park_environment(self, labels: list[str], safety: dict, pros: list[str]) -> str | None:
        if any(label in labels for label in ["park", "garden", "nature", "tree", "grass"]):
            safety.update({"has_shelter": True, "escape_routes": True})
            pros.extend(["Has spacious area", "Has trees for shelter"])
            return "Public park"
        return None

    def _check_street_environment(
        self, labels: list[str], safety: dict, cons: list[str], recs: list[str]
    ) -> str | None:
        if any(label in labels for label in ["street", "road", "traffic", "car"]):
            safety["safe_from_traffic"] = False
            cons.extend(["Near traffic roads", "Potential danger from vehicles"])
            recs.extend(["Should have safe shelter", "Install slow down signs"])
            return "Street or public road"
        return None

    def _check_residential_environment(self, labels: list[str], safety: dict, pros: list[str]) -> str | None:
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


# Reuse one credentialed client per application process through FastAPI dependencies.
vision_service = GoogleVisionService()
