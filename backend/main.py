import os
import uuid
from typing import List
from io import BytesIO

import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import torch
import numpy as np

# Import authentication modules
from routes import auth_manual, auth_google, profile
from dependencies import get_supabase_client

load_dotenv()

app = FastAPI(
    title="PurrFect Spots API",
    description="API for sharing cat photos with locations and OAuth authentication",
    version="2.0.0"
)

# รวม route ทั้งหมด
app.include_router(auth_manual.router)
app.include_router(auth_google.router)
app.include_router(profile.router)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        # Try to load from local file first
        if os.path.exists("yolov5s.pt"):
            print("✅ Loading YOLOv5 from local file...")
            model = torch.hub.load("ultralytics/yolov5", "custom", path="yolov5s.pt", source="local")
        else:
            print("📦 Downloading YOLOv5 model...")
            # Clear cache first to avoid corrupted files
            torch.hub._get_cache_dir()
            cache_dir = torch.hub._get_cache_dir()
            yolo_cache = os.path.join(cache_dir, "ultralytics_yolov5_master")
            if os.path.exists(yolo_cache):
                import shutil
                shutil.rmtree(yolo_cache)
                print("🗑️  Cleared old YOLOv5 cache")
            
            # Download fresh model
            model = torch.hub.load("ultralytics/yolov5", "yolov5s", force_reload=True)
        
        model.to(device).eval()
        print(f"✅ YOLOv5 model loaded successfully on {device}")
        return model
        
    except Exception as e:
        print(f"❌ Error loading YOLOv5 model: {str(e)}")
        print("🔄 Falling back to local model file...")
        
        # Fallback: try to use local file
        if os.path.exists("yolov5s.pt"):
            try:
                model = torch.hub.load("ultralytics/yolov5", "custom", path="yolov5s.pt", source="local")
                model.to(device).eval()
                print("✅ YOLOv5 model loaded from local file")
                return model
            except Exception as e2:
                print(f"❌ Local model also failed: {str(e2)}")
        
        # Last resort: return None and handle gracefully
        print("⚠️  YOLOv5 model not available - cat detection will be disabled")
        return None

# Load the model
model = load_yolo_model()

# Pydantic models
class PresignReq(BaseModel):
    filename: str
    content_type: str


class AddCatReq(BaseModel):
    name: str
    description: str | None = None
    latitude: float
    longitude: float
    image_url: str


class CatLocation(BaseModel):
    id: str
    image_url: str
    latitude: float
    longitude: float
    description: str | None = None
    location_name: str | None = None
    uploaded_at: str | None = None


@app.get("/api/gallery")
async def get_gallery():
    """Get all cat images from S3 and return their URLs for gallery display."""
    PREFIX = "uploads/"        

    try:
        response = s3_client.list_objects_v2(
            Bucket=AWS_BUCKET,
            Prefix=PREFIX         
        )

        if "Contents" not in response:
            return {"images": []}

        images = []
        for obj in response["Contents"]:
            if obj["Key"].lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
                image_url = (
                    f"https://{AWS_BUCKET}.s3-{AWS_REGION}.amazonaws.com/{obj['Key']}"
                )
                images.append(
                    {
                        "id": obj["Key"].split("/")[-1].rsplit(".", 1)[0],
                        "url": image_url,
                        "filename": obj["Key"].split("/")[-1],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                    }
                )

        images.sort(key=lambda x: x["last_modified"], reverse=True)
        return {"images": images}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch gallery images: {str(e)}"
        )


@app.get("/locations", response_model=List[CatLocation])
def get_locations(supabase = Depends(get_supabase_client)):
    """Get all cat locations from Supabase."""
    try:
        resp = (
            supabase.table("cat_photos")
            .select("*")
            .order("uploaded_at", desc=True)
            .execute()
        )
        if not resp.data:
            raise HTTPException(status_code=404, detail="No data returned from Supabase")
        return resp.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
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


@app.post("/upload-cat")
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