"""
API handlers for Purrfect Spots backend
Handles all API endpoints and business logic
"""

from flask import jsonify, request
import logging
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
import base64
import os
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class APIHandlers:
    def __init__(self, s3_client, bucket_name, region, allowed_extensions):
        self.s3_client = s3_client
        self.bucket_name = bucket_name
        self.region = region
        self.allowed_extensions = allowed_extensions
    
    def health_check(self):
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            's3_configured': self.s3_client is not None
        })
    
    def get_config(self):
        """Get configuration status"""
        return jsonify({
            'aws_configured': self.s3_client is not None,
            'bucket_name': self.bucket_name,
            'region': self.region,
            'allowed_extensions': list(self.allowed_extensions)
        })
    
    def list_images(self):
        """List all images from S3 bucket"""
        try:
            if not self.s3_client:
                return jsonify({'error': 'S3 is not configured'}), 500
            
            logger.info(f"Listing objects in bucket: {self.bucket_name}")
            
            # List objects in bucket
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                return jsonify({'images': []})
            
            images = []
            for obj in response['Contents']:
                # Get object metadata
                try:
                    metadata_response = self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    
                    image_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                    
                    # Decode metadata if it was encoded
                    raw_metadata = metadata_response.get('Metadata', {})
                    is_encoded = raw_metadata.get('is_encoded', 'false')
                    
                    decoded_metadata = {}
                    for key, value in raw_metadata.items():
                        if key in ['location', 'description', 'original_filename']:
                            decoded_metadata[key] = self._safe_decode(value, is_encoded)
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
            
            return jsonify({'images': images})
            
        except ClientError as e:
            logger.error(f"List images AWS error: {e}")
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Error Code: {error_code}, Message: {error_message}")
            return jsonify({'error': f'AWS Error: {error_code}'}), 500
        except Exception as e:
            logger.error(f"List images error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def get_locations(self):
        """Get all cat locations from images data"""
        try:
            if not self.s3_client:
                return jsonify({'error': 'S3 is not configured'}), 500
            
            logger.info(f"Getting locations from bucket: {self.bucket_name}")
            
            # Get all images first
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' not in response:
                return jsonify({'locations': []})
            
            locations = []
            for obj in response['Contents']:
                try:
                    # Get object metadata
                    metadata_response = self.s3_client.head_object(
                        Bucket=self.bucket_name,
                        Key=obj['Key']
                    )
                    
                    raw_metadata = metadata_response.get('Metadata', {})
                    is_encoded = raw_metadata.get('is_encoded', 'false')
                    
                    # Decode metadata
                    location = self._safe_decode(raw_metadata.get('location', ''), is_encoded)
                    description = self._safe_decode(raw_metadata.get('description', ''), is_encoded)
                    latitude = raw_metadata.get('latitude', '')
                    longitude = raw_metadata.get('longitude', '')
                    
                    # Only add if coordinates exist
                    if latitude and longitude:
                        image_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                        
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
            
            return jsonify({'locations': locations})
            
        except ClientError as e:
            logger.error(f"Get locations AWS error: {e}")
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"AWS Error Code: {error_code}, Message: {error_message}")
            return jsonify({'error': f'AWS Error: {error_code}'}), 500
        except Exception as e:
            logger.error(f"Get locations error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def upload_image(self):
        """Upload image to S3 bucket"""
        try:
            # Check if S3 is configured
            if not self.s3_client:
                return jsonify({'error': 'S3 is not configured'}), 500
            
            # Check if file is present in request
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            
            # Check if file is selected
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Check if file type is allowed
            if not self._allowed_file(file.filename):
                return jsonify({'error': 'File type not allowed'}), 400
            
            # Generate unique filename
            filename = self._generate_unique_filename(file.filename)
            
            # Get additional metadata from form
            location = request.form.get('location', '')
            description = request.form.get('description', '')
            latitude = request.form.get('latitude', '')
            longitude = request.form.get('longitude', '')
            
            # Create metadata (encode Thai/Unicode to base64 for S3 compatibility)
            metadata = {
                'location': self._safe_encode(location),
                'description': self._safe_encode(description),
                'latitude': latitude or '',
                'longitude': longitude or '',
                'upload_timestamp': datetime.now().isoformat(),
                'original_filename': self._safe_encode(file.filename),
                'is_encoded': 'true' if any(ord(char) > 127 for char in (location + description)) else 'false'
            }
            
            # Upload to S3
            try:
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    filename,
                    ExtraArgs={
                        'ContentType': file.content_type,
                        'Metadata': metadata
                    }
                )
                
                # Generate public URL
                image_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{filename}"
                
                logger.info(f"Successfully uploaded {filename} to S3")
                
                return jsonify({
                    'message': 'Image uploaded successfully',
                    'filename': filename,
                    'url': image_url,
                    'metadata': metadata
                }), 200
                
            except ClientError as e:
                logger.error(f"S3 upload failed: {e}")
                return jsonify({'error': 'Failed to upload to S3'}), 500
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def delete_image(self, filename):
        """Delete image from S3 bucket"""
        try:
            if not self.s3_client:
                return jsonify({'error': 'S3 is not configured'}), 500
            
            # Delete from S3
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
            
            logger.info(f"Successfully deleted {filename} from S3")
            
            return jsonify({'message': 'Image deleted successfully'}), 200
            
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return jsonify({'error': 'Failed to delete from S3'}), 500
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Helper methods
    def _safe_decode(self, text, is_encoded='false'):
        """Decode base64 text if it was encoded"""
        try:
            if is_encoded == 'true' and text:
                return base64.b64decode(text.encode('ascii')).decode('utf-8')
            return text or ''
        except:
            return text or ''
    
    def _safe_encode(self, text):
        """Encode text to base64 if it contains non-ASCII characters"""
        if text and any(ord(char) > 127 for char in text):
            return base64.b64encode(text.encode('utf-8')).decode('ascii')
        return text or ''
    
    def _allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _generate_unique_filename(self, filename):
        """Generate a unique filename with timestamp and UUID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        name, ext = os.path.splitext(secure_filename(filename))
        return f"{name}_{timestamp}_{unique_id}{ext}"
    
    def _optimize_image(self, image_file):
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
