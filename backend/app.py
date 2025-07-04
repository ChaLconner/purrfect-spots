"""
Purrfect Spots Backend API
A Flask API for managing cat photos and locations
"""

from flask import Flask
from flask_cors import CORS
import logging
from aws_config import AWSConfig
from api_handlers import APIHandlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize AWS configuration
aws_config = AWSConfig()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialize API handlers
api_handlers = APIHandlers(
    s3_client=aws_config.get_client(),
    bucket_name=aws_config.get_bucket_name(),
    region=aws_config.get_region(),
    allowed_extensions=ALLOWED_EXTENSIONS
)

# Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return api_handlers.health_check()

@app.route('/config', methods=['GET'])
def get_config():
    """Get configuration status"""
    return api_handlers.get_config()

@app.route('/images', methods=['GET'])
def list_images():
    """List all images from S3 bucket"""
    return api_handlers.list_images()

@app.route('/locations', methods=['GET'])
def get_locations():
    """Get all cat locations from images data"""
    return api_handlers.get_locations()

@app.route('/upload', methods=['POST'])
def upload_image():
    """Upload image to S3 bucket"""
    return api_handlers.upload_image()

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    """Delete image from S3 bucket"""
    return api_handlers.delete_image(filename)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return {'error': 'Endpoint not found'}, 404

@app.errorhandler(405)
def method_not_allowed(error):
    return {'error': 'Method not allowed'}, 405

@app.errorhandler(413)
def payload_too_large(error):
    return {'error': 'File too large. Maximum size is 16MB'}, 413

@app.errorhandler(500)
def internal_server_error(error):
    return {'error': 'Internal server error'}, 500

if __name__ == '__main__':
    # Log startup information
    logger.info("Starting Purrfect Spots Backend API")
    logger.info(f"AWS configured: {aws_config.is_configured()}")
    logger.info(f"Bucket: {aws_config.get_bucket_name()}")
    logger.info(f"Region: {aws_config.get_region()}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
