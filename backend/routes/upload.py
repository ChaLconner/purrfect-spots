import os
import uuid
from typing import List
from io import BytesIO

import boto3
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from pydantic import BaseModel
from PIL import Image
import torch
import numpy as np

from dependencies import get_supabase_client

router = APIRouter(
    prefix="/upload",
    tags=["upload"]
)

# AWS configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_BUCKET = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    config=boto3.session.Config(signature_version="s3v4"),
)

# Load the model with error handling
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_yolo_model():
    """Load YOLOv5 model with error handling and fallback options"""
    try:
        print("🔄 Attempting to load YOLOv5 model...")
        
        # Method 1: Try downloading fresh model (clear cache first)
        try:
            print("📦 Downloading YOLOv5 model from ultralytics...")
            # Clear cache to avoid outdated cache issues
            import shutil
            cache_dir = torch.hub.get_dir()
            yolo_cache = os.path.join(cache_dir, "ultralytics_yolov5_master")
            if os.path.exists(yolo_cache):
                shutil.rmtree(yolo_cache)
                print("🗑️ Cleared YOLOv5 cache")
            
            model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, force_reload=True, trust_repo=True)
            model.to(device).eval()
            print(f"✅ YOLOv5 model downloaded and loaded successfully on {device}")
            return model
        except Exception as e1:
            print(f"⚠️ Download with cache clear failed: {e1}")
        
        # Method 2: Try using local file with different approach
        try:
            model_path = os.path.abspath("yolov5s.pt")
            if os.path.exists(model_path):
                print(f"� Trying to load local model: {model_path}")
                # Try loading as a regular PyTorch model with weights_only=False
                model = torch.load(model_path, map_location=device, weights_only=False)
                if hasattr(model, 'eval'):
                    model.eval()
                print(f"✅ Local model loaded successfully on {device}")
                return model
            else:
                print("❌ Local model file not found")
        except Exception as e2:
            print(f"⚠️ Local model loading failed: {e2}")
        
        # Method 3: Try without force_reload
        try:
            print("� Trying standard YOLOv5 download...")
            model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, trust_repo=True)
            model.to(device).eval()
            print(f"✅ YOLOv5 model loaded successfully on {device}")
            return model
        except Exception as e3:
            print(f"⚠️ Standard download failed: {e3}")
        
        # If all methods fail, disable cat detection
        print("❌ All model loading methods failed")
        print("⚠️ YOLOv5 model not available - cat detection will be disabled")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error in load_yolo_model: {str(e)}")
        print("⚠️ YOLOv5 model not available - cat detection will be disabled")
        return None

# Initialize the model
model = load_yolo_model()

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to S3 and return its public URL."""
    try:
        file_extension = file.filename.split(".")[-1]
        key = f"uploads/{uuid.uuid4()}.{file_extension}"
        file_content = await file.read()
        try:
            s3_client.put_object(
                Bucket=AWS_BUCKET,
                Key=key,
                Body=file_content,
                ContentType=file.content_type,
            )
        except Exception as s3_error:
            raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(s3_error)}")
        s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
        return {"url": s3_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/cat")
async def upload_cat(
    file: UploadFile = File(...),
    lat: float = Form(...),
    lng: float = Form(...),
    description: str = Form(...),
    location_name: str = Form(...),
    supabase = Depends(get_supabase_client),
):
    """Upload an image to S3 and save its metadata to Supabase — only if it's a cat."""
    contents = await file.read()
    detected_labels = []
    
    # ตรวจสอบว่าเป็นภาพแมวหรือไม่
    try:
        # Check if model is available
        if model is None:
            print("⚠️  YOLOv5 model not available - skipping cat detection")
            # Skip cat detection if model is not available
        else:
            image = Image.open(BytesIO(contents)).convert("RGB")
            img_np = np.array(image)
            results = model(img_np)
            detected_labels = results.pandas().xyxy[0]['name'].tolist()
            is_cat = any("cat" in label.lower() for label in detected_labels)
            if not is_cat:
                raise HTTPException(status_code=400, detail="Please upload a cat image only.")
    except HTTPException:
        # Re-raise HTTP exceptions (like "not a cat")
        raise
    except Exception as e:
        print(f"❌ Image classification failed: {str(e)}")
        # In production, you might want to continue without cat detection
        # or return a specific error. For now, we'll skip the detection.
        print("⚠️  Skipping cat detection due to error")
    
    # อัปโหลดภาพขึ้น S3
    ext = (file.filename.split(".")[-1] if "." in file.filename else "bin")
    key = f"uploads/{uuid.uuid4()}.{ext}"
    try:
        s3_client.put_object(
            Bucket=AWS_BUCKET,
            Key=key,
            Body=contents,
            ContentType=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")
    s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    
    # บันทึกข้อมูลลง Supabase
    payload = {
        "image_url": s3_url,
        "latitude": lat,
        "longitude": lng,
        "description": description,
        "location_name": location_name,
    }
    result = supabase.table("cat_photos").insert(payload).execute()
    if getattr(result, "error", None):
        s3_client.delete_object(Bucket=AWS_BUCKET, Key=key)
        raise HTTPException(500, f"Supabase insert failed: {result.error}")
    
    return {
        "message": "Uploaded",
        "image_url": s3_url,
        "row": result.data[0],
        "classification": detected_labels
    }
