import os
import uuid
from typing import List

import boto3
from boto3.s3.transfer import TransferConfig
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import Client, create_client

load_dotenv()

app = FastAPI()

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS and Supabase configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_BUCKET = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SUPA_URL = os.getenv("SUPABASE_URL")
SUPA_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client
supabase: Client = None
if SUPA_URL and SUPA_KEY:
    supabase = create_client(SUPA_URL, SUPA_KEY)

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    config=boto3.session.Config(signature_version="s3v4"),
)


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
def get_locations():
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
):
    """Upload an image to S3 and save its metadata to Supabase."""
    ext = (file.filename.split(".")[-1] if "." in file.filename else "bin")
    key = f"uploads/{uuid.uuid4()}.{ext}"
    try:
        s3_client.put_object(
            Bucket=AWS_BUCKET,
            Key=key,
            Body=await file.read(),
            ContentType=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")
    s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
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
    return {"message": "Uploaded", "image_url": s3_url, "row": result.data[0]}