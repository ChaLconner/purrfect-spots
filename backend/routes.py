"""
API routes for Purrfect Spots backend
"""

import boto3
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import uuid
import datetime as dt
from typing import Optional, List
import logging
from botocore.exceptions import ClientError
from io import BytesIO

from database import get_db
from models import (
    CatImage, CatImageCreate, CatImageResponse, 
    PresignedUrlResponse, LocationResponse, 
    ImageListResponse, UploadResponse
)
from utils import (
    safe_decode, safe_encode, allowed_file, 
    generate_unique_filename, optimize_image, 
    get_sample_locations
)

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create router
router = APIRouter()

# AWS S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# API Routes
@router.post("/generate-presigned-url", response_model=PresignedUrlResponse)
def get_presigned_url(file_name: str):
    """Generate presigned URL for S3 upload"""
    key = f"uploads/{uuid.uuid4()}-{file_name}"
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": BUCKET_NAME, "Key": key},
        ExpiresIn=3600,
    )
    return {"upload_url": url, "s3_key": key}

@router.post("/images", response_model=CatImageResponse)
def create_cat_image(image: CatImageCreate, db: Session = Depends(get_db)):
    """Create a new cat image record in database"""
    db_image = CatImage(
        s3_key=image.s3_key,
        url=image.url,
        location=image.location,
        description=image.description,
        latitude=image.latitude,
        longitude=image.longitude,
        original_name=image.original_name
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

@router.get("/images", response_model=list[CatImageResponse])
def get_all_images(db: Session = Depends(get_db)):
    """Get all cat images from database"""
    images = db.query(CatImage).all()
    return images

@router.get("/images/{image_id}", response_model=CatImageResponse)
def get_image(image_id: str, db: Session = Depends(get_db)):
    """Get a specific cat image by ID"""
    image = db.query(CatImage).filter(CatImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@router.get("/locations", response_model=List[LocationResponse])
def get_locations():
    """Get all cat locations from images data"""
    try:
        if not s3:
            # Return sample data when S3 is not configured
            return get_sample_locations()
        
        logger.info(f"Getting locations from bucket: {BUCKET_NAME}")
        
        # Get all images first
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in response:
            # Return sample data when no data in S3
            return get_sample_locations()
        
        locations = []
        for obj in response['Contents']:
            try:
                # Get object metadata
                metadata_response = s3.head_object(
                    Bucket=BUCKET_NAME,
                    Key=obj['Key']
                )
                
                raw_metadata = metadata_response.get('Metadata', {})
                is_encoded = raw_metadata.get('is_encoded', 'false')
                
                # Decode metadata
                location = safe_decode(raw_metadata.get('location', ''), is_encoded)
                description = safe_decode(raw_metadata.get('description', ''), is_encoded)
                latitude = raw_metadata.get('latitude', '')
                longitude = raw_metadata.get('longitude', '')
                
                # Only add if coordinates exist
                if latitude and longitude:
                    image_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{obj['Key']}"
                    
                    locations.append({
                        'id': obj['Key'],
                        'name': location or 'Unknown Location',
                        'description': description or '',
                        'latitude': float(latitude),
                        'longitude': float(longitude),
                        'image_url': image_url
                    })
                    
            except (ClientError, ValueError) as e:
                logger.error(f"Failed to process location for {obj['Key']}: {e}")
                continue
        
        # If no locations found in S3, return sample data
        if not locations:
            return get_sample_locations()
        
        return locations
        
    except ClientError as e:
        logger.error(f"Get locations AWS error: {e}")
        # Return sample data on AWS error
        return get_sample_locations()
    except Exception as e:
        logger.error(f"Get locations error: {e}")
        # Return sample data on any error
        return get_sample_locations()

@router.get("/images_list", response_model=List[ImageListResponse])
def list_images():
    """List all images from S3 bucket"""
    try:
        if not s3:
            raise HTTPException(status_code=500, detail="S3 is not configured")
        
        logger.info(f"Listing objects in bucket: {BUCKET_NAME}")
        
        # List objects in bucket
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        
        if 'Contents' not in response:
            return []
        
        images = []
        for obj in response['Contents']:
            # Get object metadata
            try:
                metadata_response = s3.head_object(
                    Bucket=BUCKET_NAME,
                    Key=obj['Key']
                )
                
                image_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{obj['Key']}"
                
                # Decode metadata if it was encoded
                raw_metadata = metadata_response.get('Metadata', {})
                is_encoded = raw_metadata.get('is_encoded', 'false')
                
                decoded_metadata = {}
                for key, value in raw_metadata.items():
                    if key in ['location', 'description', 'original_filename']:
                        decoded_metadata[key] = safe_decode(value, is_encoded)
                    else:
                        decoded_metadata[key] = value
                
                image_info = {
                    'filename': obj['Key'],
                    'url': image_url,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'metadata': decoded_metadata
                }
                
                images.append(image_info)
                
            except ClientError as e:
                logger.error(f"Failed to get metadata for {obj['Key']}: {e}")
                continue
        
        return images
        
    except ClientError as e:
        logger.error(f"List images AWS error: {e}")
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS Error Code: {error_code}, Message: {error_message}")
        raise HTTPException(status_code=500, detail=f"AWS Error: {error_code}")
    except Exception as e:
        logger.error(f"List images error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    latitude: Optional[str] = Form(None),
    longitude: Optional[str] = Form(None)
):
    """Upload image to S3 bucket"""
    try:
        # Check if S3 is configured
        if not s3:
            raise HTTPException(status_code=500, detail="S3 is not configured")
        
        # Check if file type is allowed
        if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        
        # Read file content
        file_content = await file.read()
        file_obj = BytesIO(file_content)
        
        # Optimize image
        optimized_file = optimize_image(file_obj)
        
        # Create metadata (encode Thai/Unicode to base64 for S3 compatibility)
        metadata = {
            'location': safe_encode(location or ''),
            'description': safe_encode(description or ''),
            'latitude': latitude or '',
            'longitude': longitude or '',
            'upload_timestamp': dt.datetime.now().isoformat(),
            'original_filename': safe_encode(file.filename),
            'is_encoded': 'true' if any(ord(char) > 127 for char in ((location or '') + (description or ''))) else 'false'
        }
        
        # Upload to S3
        try:
            s3.upload_fileobj(
                optimized_file,
                BUCKET_NAME,
                filename,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'Metadata': metadata
                }
            )
            
            # Generate public URL
            image_url = f"https://{BUCKET_NAME}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{filename}"
            
            logger.info(f"Successfully uploaded {filename} to S3")
            
            return {
                'message': 'Image uploaded successfully',
                'filename': filename,
                'url': image_url,
                'metadata': metadata
            }
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload to S3")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/images/{filename}")
def delete_image(filename: str, db: Session = Depends(get_db)):
    """Delete a cat image from database and S3"""
    try:
        # First try to delete from database
        image = db.query(CatImage).filter(CatImage.s3_key == filename).first()
        if image:
            db.delete(image)
            db.commit()
        
        # Delete from S3
        if s3:
            try:
                s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
                logger.info(f"Successfully deleted {filename} from S3")
            except ClientError as e:
                logger.error(f"S3 delete failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to delete from S3")
        
        return {"message": "Image deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
