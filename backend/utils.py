"""
Utility functions for the Purrfect Spots backend
"""

import base64
import os
import uuid
import datetime as dt
from typing import List
from PIL import Image
from io import BytesIO
import logging

# Configure logging
logger = logging.getLogger(__name__)

def safe_decode(text: str, is_encoded: str = 'false') -> str:
    """Decode base64 text if it was encoded"""
    try:
        if is_encoded == 'true' and text:
            return base64.b64decode(text.encode('ascii')).decode('utf-8')
        return text or ''
    except:
        return text or ''

def safe_encode(text: str) -> str:
    """Encode text to base64 if it contains non-ASCII characters"""
    if text and any(ord(char) > 127 for char in text):
        return base64.b64encode(text.encode('utf-8')).decode('ascii')
    return text or ''

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(filename: str) -> str:
    """Generate a unique filename with timestamp and UUID"""
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(filename)
    # Clean filename of special characters
    clean_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
    return f"{clean_name}_{timestamp}_{unique_id}{ext}"

def optimize_image(image_file: BytesIO) -> BytesIO:
    """Optimize image for web"""
    try:
        # Open image with PIL
        image = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize if image is too large
        max_size = (1920, 1080)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save optimized image to bytes
        output = BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        logger.error(f"Image optimization failed: {e}")
        # Return original if optimization fails
        image_file.seek(0)
        return image_file

def get_sample_locations() -> List[dict]:
    """Get sample cat locations for demonstration"""
    return [
        {
            'id': 'sample-1',
            'name': 'วัดพระสิงห์ - แมวพระราช',
            'description': 'แมวสีส้มน่ารักที่วัดพระสิงห์ ชอบนอนใต้ต้นไผ่',
            'latitude': 18.7883,
            'longitude': 98.9853,
            'image_url': 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400&h=300&fit=crop'
        },
        {
            'id': 'sample-2',
            'name': 'ถนนคนเดิน - แมวนักเดินทาง',
            'description': 'แมวขาวดำที่ถนนคนเดิน มักเดินไปมาหาของกิน',
            'latitude': 18.7869,
            'longitude': 98.9856,
            'image_url': 'https://images.unsplash.com/photo-1571566882372-1598d88abd90?w=400&h=300&fit=crop'
        },
        {
            'id': 'sample-3',
            'name': 'วัดเจดีย์หลวง - แมววัด',
            'description': 'แมวสีเทาที่วัดเจดีย์หลวง เป็นแมวเก่าแก่ของวัด',
            'latitude': 18.7880,
            'longitude': 98.9916,
            'image_url': 'https://images.unsplash.com/photo-1533743983669-94fa5c4338ec?w=400&h=300&fit=crop'
        },
        {
            'id': 'sample-4',
            'name': 'ประตูท่าแพ - แมวคาเฟ่',
            'description': 'แมวสีน้ำตาลที่ประตูท่าแพ ชอบนั่งดูผู้คนสัญจร',
            'latitude': 18.7844,
            'longitude': 98.9944,
            'image_url': 'https://images.unsplash.com/photo-1596854407944-bf87f6fdd49e?w=400&h=300&fit=crop'
        },
        {
            'id': 'sample-5',
            'name': 'ประตูเชียงใหม่ - แมวผู้พิทักษ์',
            'description': 'แมวสีดำที่ประตูเชียงใหม่ เป็นแมวที่ดูดีและเข้าถึงได้ง่าย',
            'latitude': 18.7919,
            'longitude': 98.9856,
            'image_url': 'https://images.unsplash.com/photo-1513245543132-31f507417b26?w=400&h=300&fit=crop'
        },
        {
            'id': 'sample-6',
            'name': 'ตลาดวโรรส - แมวนักค้า',
            'description': 'แมวสีขาวที่ตลาดวโรรส เป็นแมวที่ชอบอยู่ในตลาด',
            'latitude': 18.7908,
            'longitude': 98.9900,
            'image_url': 'https://images.unsplash.com/photo-1518791841217-8f162f1e1131?w=400&h=300&fit=crop'
        }
    ]
