"""
SQLAlchemy models for Purrfect Spots
"""

from sqlalchemy import Column, String, Float, DateTime
from database import Base
import uuid
import datetime as dt
from typing import Optional, List
from pydantic import BaseModel

# SQLAlchemy Model
class CatImage(Base):
    __tablename__ = "cat_images"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    s3_key = Column(String, nullable=False)
    url = Column(String, nullable=False)
    location = Column(String)
    description = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    original_name = Column(String)
    uploaded_at = Column(DateTime, default=dt.datetime.utcnow)

# Pydantic models for API
class CatImageCreate(BaseModel):
    s3_key: str
    url: str
    location: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    original_name: Optional[str] = None

class CatImageResponse(BaseModel):
    id: str
    s3_key: str
    url: str
    location: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    original_name: Optional[str] = None
    uploaded_at: dt.datetime

    class Config:
        from_attributes = True

class PresignedUrlResponse(BaseModel):
    upload_url: str
    s3_key: str

class LocationResponse(BaseModel):
    id: str
    name: str
    description: str
    latitude: float
    longitude: float
    image_url: str

class ImageListResponse(BaseModel):
    filename: str
    url: str
    size: int
    last_modified: str
    metadata: dict

class UploadResponse(BaseModel):
    message: str
    filename: str
    url: str
    metadata: dict
