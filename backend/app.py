from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import boto3
from botocore.exceptions import ClientError
import os
import uuid
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import logging
from io import BytesIO
from PIL import Image
import mimetypes
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

# Initialize S3 client
s3_client = None
try:
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and S3_BUCKET_NAME:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        logger.info("S3 client initialized successfully")
    else:
        logger.warning("AWS credentials not configured")
except Exception as e:
    logger.error(f"Failed to initialize S3 client: {e}")

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def safe_decode(text, is_encoded='false'):
    """Decode base64 text if it was encoded"""
    try:
        if is_encoded == 'true' and text:
            return base64.b64decode(text.encode('ascii')).decode('utf-8')
        return text or ''
    except:
        return text or ''

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Generate a unique filename with timestamp and UUID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    name, ext = os.path.splitext(secure_filename(filename))
    return f"{name}_{timestamp}_{unique_id}{ext}"

def optimize_image(image_file):
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        's3_configured': s3_client is not None
    })

@app.route('/upload', methods=['POST'])
def upload_image():
    """Upload image to S3 bucket"""
    try:
        # Check if S3 is configured
        if not s3_client:
            return jsonify({'error': 'S3 is not configured'}), 500
        
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        
        # Get additional metadata from form
        location = request.form.get('location', '')
        description = request.form.get('description', '')
        latitude = request.form.get('latitude', '')
        longitude = request.form.get('longitude', '')
        
        # Create metadata (encode Thai/Unicode to base64 for S3 compatibility)
        
        def safe_encode(text):
            """Encode text to base64 if it contains non-ASCII characters"""
            if text and any(ord(char) > 127 for char in text):
                return base64.b64encode(text.encode('utf-8')).decode('ascii')
            return text or ''
        
        metadata = {
            'location': safe_encode(location),
            'description': safe_encode(description),
            'latitude': latitude or '',
            'longitude': longitude or '',
            'upload_timestamp': datetime.now().isoformat(),
            'original_filename': safe_encode(file.filename),
            'is_encoded': 'true' if any(ord(char) > 127 for char in (location + description)) else 'false'
        }
        
        # Upload to S3
        try:
            s3_client.upload_fileobj(
                file,
                S3_BUCKET_NAME,
                filename,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'Metadata': metadata
                }
            )
            
            # Generate public URL
            image_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{filename}"
            
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

@app.route('/images', methods=['GET'])
def list_images():
    """List all images from S3 bucket"""
    try:
        if not s3_client:
            return jsonify({'error': 'S3 is not configured'}), 500
        
        # List objects in bucket
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME)
        
        if 'Contents' not in response:
            return jsonify({'images': []})
        
        images = []
        for obj in response['Contents']:
            # Get object metadata
            try:
                metadata_response = s3_client.head_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=obj['Key']
                )
                
                image_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{obj['Key']}"
                
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
        
        return jsonify({'images': images})
        
    except Exception as e:
        logger.error(f"List images error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    """Delete image from S3 bucket"""
    try:
        if not s3_client:
            return jsonify({'error': 'S3 is not configured'}), 500
        
        # Delete from S3
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=filename)
        
        logger.info(f"Successfully deleted {filename} from S3")
        
        return jsonify({'message': 'Image deleted successfully'}), 200
        
    except ClientError as e:
        logger.error(f"S3 delete failed: {e}")
        return jsonify({'error': 'Failed to delete from S3'}), 500
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Get configuration status"""
    return jsonify({
        'aws_configured': bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY),
        'bucket_name': S3_BUCKET_NAME,
        'region': AWS_REGION,
        'allowed_extensions': list(ALLOWED_EXTENSIONS)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
