import os
from typing import List

import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import authentication modules
from routes import auth_manual, auth_google, profile, upload
from dependencies import get_supabase_client

load_dotenv()

app = FastAPI(
    title="PurrFect Spots API",
    description="API for sharing cat photos with locations and OAuth authentication",
    version="2.0.0"
)

# ✅ CORS middleware must be added BEFORE including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include routers AFTER middleware
app.include_router(auth_manual.router)
app.include_router(auth_google.router)
app.include_router(profile.router)
app.include_router(upload.router)

# AWS configuration for gallery
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_BUCKET = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize S3 client for gallery
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    config=boto3.session.Config(signature_version="s3v4"),
)

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
                image_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{obj['Key']}"
                images.append({
                    "id": obj["Key"].split("/")[-1].rsplit(".", 1)[0],
                    "url": image_url,
                    "filename": obj["Key"].split("/")[-1],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                })
        
        images.sort(key=lambda x: x["last_modified"], reverse=True)
        return {"images": images}
        
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch gallery images: {str(e)}"
        )

# Pydantic models
class CatLocation(BaseModel):
    id: str
    image_url: str
    latitude: float
    longitude: float
    description: str | None = None
    location_name: str | None = None
    uploaded_at: str | None = None


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