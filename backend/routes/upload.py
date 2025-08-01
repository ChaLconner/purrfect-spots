"""
Upload routes for cat photos
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from middleware.auth_middleware import get_current_user
from routes.cat_detection import CatDetectionService
from dependencies import get_supabase_client
import json
import uuid
import os
import boto3
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/upload", tags=["Upload"])

# AWS S3 configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
AWS_BUCKET = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

def get_cat_detection_service():
    return CatDetectionService()

@router.post("/cat")
async def upload_cat_photo(
    file: UploadFile = File(...),
    lat: str = Form(...),
    lng: str = Form(...),
    location_name: str = Form(...),
    description: Optional[str] = Form(""),
    cat_detection_data: Optional[str] = Form(None),
    current_user = Depends(get_current_user),
    supabase = Depends(get_supabase_client),
    detection_service: CatDetectionService = Depends(get_cat_detection_service)
):
    """
    อัพโหลดรูปภาพแมวพร้อมข้อมูลตำแหน่ง
    """
    try:
        print(f"🐱 Uploading cat photo for user: {getattr(current_user, 'email', getattr(current_user, 'id', 'unknown'))}")
        print(f"📁 File: {file.filename}, Location: {location_name}")
        
        # Validate file
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file contents
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Parse cat detection data if provided
        cat_data = None
        if cat_detection_data:
            try:
                cat_data = json.loads(cat_detection_data)
                print(f"🔍 Cat detection data: {cat_data}")
            except json.JSONDecodeError:
                print("⚠️ Invalid cat detection data format")
        
        # If no cat detection data provided, detect cats now
        if not cat_data:
            print("🔍 No cat detection data provided, detecting cats...")
            detection_result = await detection_service.detect_cats(contents)
            
            # Reject if no cats found
            if not detection_result.get('has_cats', False):
                raise HTTPException(
                    status_code=400, 
                    detail=f"No cats detected in image (confidence: {detection_result.get('confidence', 0)}%)"
                )
            
            cat_data = {
                "has_cats": detection_result.get('has_cats'),
                "cat_count": detection_result.get('cat_count', 0),
                "confidence": detection_result.get('confidence', 0),
                "suitable_for_cat_spot": detection_result.get('suitable_for_cat_spot', False),
                "cats_detected": detection_result.get('cats_detected', []),
                "detection_timestamp": datetime.now().isoformat()
            }
        
        # Validate that cats were detected
        if not cat_data.get('has_cats', False) or cat_data.get('cat_count', 0) == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot upload: No cats detected in the image"
            )
        
        # Validate coordinates
        try:
            latitude = float(lat)
            longitude = float(lng)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid coordinates")
        
        # Validate required fields
        if not location_name.strip():
            raise HTTPException(status_code=400, detail="Location name is required")
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        s3_key = f"upload/{unique_filename}"
        
        # Upload file to S3
        try:
            s3_client.put_object(
                Bucket=AWS_BUCKET,
                Key=s3_key,
                Body=contents,
                ContentType=file.content_type
            )
            
            # Create S3 public URL
            image_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
            print(f"✅ File uploaded to S3: {image_url}")
            
        except Exception as s3_error:
            print(f"❌ S3 upload failed: {s3_error}")
            raise HTTPException(status_code=500, detail=f"Failed to upload image to S3: {str(s3_error)}")
        
        # Insert into database (cat_photos table)
        photo_data = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.id,
            "location_name": location_name.strip(),
            "description": description.strip() if description else None,
            "latitude": latitude,
            "longitude": longitude,
            "image_url": image_url,
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Insert into cat_photos table
        result = supabase.table("cat_photos").insert(photo_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save cat photo")
        
        created_photo = result.data[0]
        
        # Log successful upload
        print(f"✅ Cat photo created successfully: {created_photo['id']}")
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Cat photo uploaded successfully!",
                "photo": {
                    "id": created_photo["id"],
                    "location_name": created_photo["location_name"],
                    "location": {
                        "latitude": created_photo["latitude"],
                        "longitude": created_photo["longitude"]
                    },
                    "image_url": created_photo["image_url"],
                    "uploaded_at": created_photo["uploaded_at"]
                },
                "cat_detection": cat_data,
                "uploaded_by": getattr(current_user, 'email', getattr(current_user, 'id', 'unknown'))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("/test")
async def test_upload_endpoint():
    """
    ทดสอบว่า upload endpoint ทำงานได้หรือไม่
    """
    return {"message": "Upload endpoint is working!", "timestamp": datetime.now().isoformat()}
