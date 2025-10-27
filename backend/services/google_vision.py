"""
Google Cloud Vision API service for cat detection
"""
import io
import json
from typing import Dict, List
try:
    import google.cloud.vision as vision
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    vision = None
from fastapi import UploadFile, HTTPException
import os

class GoogleVisionService:
    def __init__(self):
        """Initialize Google Vision client"""
        self.client = None
        self.is_initialized = False
        
        if not VISION_AVAILABLE:
            print("Google Vision library not available, using fallback mode")
            return
            
        try:
            # Try to get the service account key path from environment
            # Use absolute path from project root
            env_key_path = os.getenv("GOOGLE_VISION_KEY_PATH")
            print(f"🔑 Environment GOOGLE_VISION_KEY_PATH: {env_key_path}")
            
            if env_key_path:
                # If environment variable is set, use it directly (could be relative or absolute)
                if os.path.isabs(env_key_path):
                    key_path = env_key_path
                    print(f"🔑 Using absolute path from env: {key_path}")
                else:
                    # Convert relative path to absolute path from current working directory
                    key_path = os.path.abspath(env_key_path)
                    print(f"🔑 Converted relative to absolute: {key_path}")
            else:
                # Fallback to relative path from this file's location
                key_path = os.path.join(os.path.dirname(__file__), "..", "keys", "google_vision.json")
                print(f"🔑 Using fallback path: {key_path}")
            
            print(f"🔑 Final key path: {key_path}")
            print(f"🔑 Current working directory: {os.getcwd()}")
            print(f"🔑 File exists: {os.path.exists(key_path)}")
            
            # Check if the key file exists
            print(f"🔑 Checking if key file exists at: {key_path}")
            if os.path.exists(key_path):
                print(f"🔑 Key file found! Initializing Google Vision client...")
                self.client = vision.ImageAnnotatorClient.from_service_account_json(key_path)
                self.is_initialized = True
                print("Google Vision client initialized successfully")
            else:
                print(f"Google Vision key file not found at: {key_path}")
                print("Using fallback mode for cat detection")
                
                # Try to use environment variable for service account JSON
                service_account_json = os.getenv("GOOGLE_VISION_SERVICE_ACCOUNT")
                if service_account_json:
                    try:
                        import json
                        service_account_info = json.loads(service_account_json)
                        self.client = vision.ImageAnnotatorClient.from_service_account_info(service_account_info)
                        self.is_initialized = True
                        print("Google Vision client initialized successfully from environment variable")
                    except Exception as env_error:
                        print(f"Failed to initialize from environment variable: {str(env_error)}")
                  
        except Exception as e:
            print(f"Failed to initialize Google Vision client: {str(e)}")
            print("Using fallback mode for cat detection")
    
    def detect_cats(self, image_file: UploadFile) -> Dict:
        """
        Detect cats in image using Google Vision API
        
        Args:
            image_file: UploadFile object
            
        Returns:
            Dict containing detection results
        """
        try:
            print(f"[DEBUG] Starting cat detection process with Google Cloud Vision")
            print(f"[DEBUG] Google Vision client initialized: {self.is_initialized}")
            print(f"[DEBUG] Image file: {getattr(image_file, 'filename', 'unknown')}")
            
            # If client is not initialized, use fallback detection
            if not self.is_initialized or not self.client:
                print("[DEBUG] Using fallback cat detection (Google Vision not available)")
                return self._fallback_cat_detection(image_file)
            
            # Read image content
            content = image_file.file.read()
            print(f"[DEBUG] Image content size: {len(content)} bytes")
            
            image = vision.Image(content=content)
            print("[DEBUG] Sending requests to Google Vision API...")

            # Send to Vision API for both label detection and object localization
            label_response = self.client.label_detection(image=image)
            object_response = self.client.object_localization(image=image)
            
            print("[DEBUG] Received response from Google Vision API")

            if label_response.error.message:
                print(f"[DEBUG] Label detection error: {label_response.error.message}")
                raise Exception(f"Vision API error: {label_response.error.message}")
            
            if object_response.error.message:
                print(f"[DEBUG] Object localization error: {object_response.error.message}")
                raise Exception(f"Vision API error: {object_response.error.message}")

            labels = label_response.label_annotations
            objects = object_response.localized_object_annotations
            
            print(f"[DEBUG] Found {len(labels)} labels and {len(objects)} objects")

            print(f"[DEBUG] All labels found: {[label.description for label in labels]}")
            print(f"[DEBUG] All objects found: {[obj.name for obj in objects]}")
            
            # Check for cat-specific labels only
            cat_labels = [
                label for label in labels
                if any(keyword in label.description.lower() for keyword in ["cat", "kitten", "feline", "cat", "meow"])
                and label.score > 0.6
            ]

            # Count cat objects for more accurate detection
            cat_objects = [
                obj for obj in objects
                if obj.name.lower() in ["cat", "kitten"]
                and obj.score > 0.6
            ]
            
            print(f"[DEBUG] Cat labels found: {len(cat_labels)}")
            print(f"[DEBUG] Cat objects found: {len(cat_objects)}")
            
            # Check for objects that are NOT cats (dogs, etc.) to reduce false positives
            non_cat_animals = [
                obj for obj in objects
                if obj.name.lower() in ["dog", "puppy", "canine", "bird", "reptile", "rodent"]
                and obj.score > 0.7
            ]
            
            print(f"[DEBUG] Non-cat animals found: {len(non_cat_animals)}")
            
            # If high confidence non-cat animals detected, reduce cat detection confidence
            if non_cat_animals:
                print(f"[DEBUG] Detected non-cat animals: {[obj.name for obj in non_cat_animals]}")
                result = {
                    "has_cats": False,
                    "cat_count": 0,
                    "confidence": 0.0,
                    "labels": [label.description for label in labels],
                    "cat_labels": [],
                    "cat_objects": [],
                    "image_quality": "Good",
                    "reasoning": f"Detected other animals (e.g., {non_cat_animals[0].name}) not cats"
                }
                print(f"[DEBUG] Returning non-cat result: {result}")
                return result

            has_high_confidence_labels = any(label.score > 0.75 for label in cat_labels)
            has_high_confidence_objects = any(obj.score > 0.75 for obj in cat_objects)
            
            print(f"[DEBUG] High confidence labels: {has_high_confidence_labels}")
            print(f"[DEBUG] High confidence objects: {has_high_confidence_objects}")
            
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
            
            print(f"[DEBUG] Label confidence: {label_confidence}, Object confidence: {object_confidence}")
            print(f"[DEBUG] Final confidence: {confidence}")
            
            # Reduce confidence slightly if only labels detected, no objects
            if len(cat_objects) == 0 and len(cat_labels) > 0:
                confidence = confidence * 0.85
                print(f"[DEBUG] Reduced confidence due to no objects: {confidence}")

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
                        "score": round(label.score * 100, 2)
                    } for label in cat_labels
                ],
                "cat_objects": [
                    {
                        "name": obj.name,
                        "score": round(obj.score * 100, 2),
                        "bounding_box": {
                            "normalized_vertices": [
                                {"x": vertex.x, "y": vertex.y}
                                for vertex in obj.bounding_poly.normalized_vertices
                            ]
                        }
                    } for obj in cat_objects
                ],
                "image_quality": image_quality,
                "reasoning": f"Detected cats from Google Cloud Vision API with {round(confidence, 2)}% confidence"
            }
            
            print(f"[DEBUG] Final detection result: {result}")
            return result
            
        except Exception as e:
            print(f"[DEBUG] Google Vision detection failed: {str(e)}")
            print(f"[DEBUG] Error type: {type(e).__name__}")
            print(f"[DEBUG] Falling back to fallback detection mode")
            # Return fallback response when error occurs
            return self._fallback_cat_detection(image_file, error=str(e))
        finally:
            # Reset file pointer for potential reuse
            image_file.file.seek(0)
    
    def _fallback_cat_detection(self, image_file, error=None) -> Dict:
        """
        Fallback cat detection when Google Vision is not available
        This performs basic filename-based detection only
        """
        try:
            print(f"[DEBUG] Starting fallback cat detection")
            print(f"[DEBUG] Original error: {error}")
            
            # Read image content
            content = image_file.file.read()
            image_file.file.seek(0)
            
            print(f"[DEBUG] Image content size for fallback: {len(content)} bytes")
            
            # Basic image analysis using PIL
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(content))
            
            # Get image dimensions and format
            width, height = img.size
            format_name = img.format
            
            print(f"[DEBUG] Image dimensions: {width}x{height}, format: {format_name}")
            
            # Simple heuristic: assume it's a cat if the filename contains cat-related keywords
            filename = getattr(image_file, 'filename', '').lower()
            cat_keywords = ['cat', 'kitten', 'kitty', 'cat', 'meow', 'kitten']
            
            print(f"[DEBUG] Filename: {filename}")
            
            filename_has_cat = any(keyword in filename for keyword in cat_keywords)
            print(f"[DEBUG] Filename contains cat keywords: {filename_has_cat}")
            
            # Fallback: basic filename-based detection only
            has_cats = filename_has_cat
            
            result = {
                "has_cats": has_cats,
                "cat_count": 1 if has_cats else 0,
                "confidence": 75.0 if filename_has_cat else 25.0,
                "labels": ["cat", "animal"] if has_cats else [],
                "cat_labels": [
                    {
                        "description": "cat",
                        "score": 75.0 if filename_has_cat else 25.0
                    }
                ] if has_cats else [],
                "cat_objects": [
                    {
                        "name": "cat",
                        "score": 75.0 if filename_has_cat else 25.0,
                        "bounding_box": None
                    }
                ] if has_cats else [],
                "image_quality": "Good" if width > 500 and height > 500 else "Medium",
                "reasoning": f"Detection from fallback mode ({'Found cat keywords in filename' if filename_has_cat else 'No specific cat characteristics found in image'}) - Image size: {width}x{height}, Format: {format_name}" +
                          (f" - Error: {error}" if error else " - Google Cloud Vision API not available")
            }
            
            print(f"[DEBUG] Final fallback result: {result}")
            return result
            
        except Exception as fallback_error:
            print(f"Fallback detection also failed: {str(fallback_error)}")
            return {
                "has_cats": False,
                "cat_count": 0,
                "confidence": 0.0,
                "labels": [],
                "cat_labels": [],
                "cat_objects": [],
                "image_quality": "Cannot be determined",
                "reasoning": f"Cannot detect cats: Both Google Cloud Vision API and fallback mode failed ({str(fallback_error)})"
            }
    
    def analyze_cat_spot_suitability(self, image_file: UploadFile) -> Dict:
        """
        Analyze if location is suitable for cats using Vision API labels
        """
        try:
            # Use Google Vision API to detect objects and labels
            vision_result = self.detect_cats(image_file)
            
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
                "escape_routes": False
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
                    "Check safety of surrounding area"
                ]
            
            return {
                "suitability_score": suitability_score,
                "safety_factors": safety_factors,
                "environment_type": environment_type,
                "pros": pros if pros else ["Requires further analysis"],
                "cons": cons if cons else ["No clear disadvantages found"],
                "recommendations": recommendations,
                "best_times": best_times
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Spot analysis failed: {str(e)}"
            )