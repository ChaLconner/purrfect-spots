"""
AWS S3 Configuration for Purrfect Spots
"""

import boto3
from botocore.exceptions import ClientError
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class AWSConfig:
    def __init__(self):
        # AWS S3 Configuration
        self.access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
        self.secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.bucket_name = os.environ.get('S3_BUCKET_NAME', 'purrfect-spots-bucket')
        
        # Initialize S3 client
        self.s3_client = None
        self._initialize_s3_client()
    
    def _initialize_s3_client(self):
        """Initialize S3 client with credentials"""
        try:
            if self.access_key_id and self.secret_access_key and self.bucket_name:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name=self.region
                )
                logger.info("S3 client initialized successfully")
                logger.info(f"Using bucket: {self.bucket_name}")
                logger.info(f"Region: {self.region}")
                
                # Test connection
                if self._test_connection():
                    logger.info("✅ S3 connection test passed")
                else:
                    logger.warning("⚠️ S3 connection test failed")
                    
            else:
                missing = []
                if not self.access_key_id: missing.append("AWS_ACCESS_KEY_ID")
                if not self.secret_access_key: missing.append("AWS_SECRET_ACCESS_KEY")
                if not self.bucket_name: missing.append("S3_BUCKET_NAME")
                logger.warning(f"AWS credentials missing: {', '.join(missing)}")
                
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def _test_connection(self):
        """Test S3 connection"""
        try:
            if self.s3_client:
                # Try to list objects to test connection
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket {self.bucket_name} not found")
            elif error_code == '403':
                logger.error(f"Access denied to bucket {self.bucket_name}")
            else:
                logger.error(f"S3 connection error: {error_code}")
            return False
        except Exception as e:
            logger.error(f"S3 connection test failed: {e}")
            return False
    
    def get_client(self):
        """Get S3 client"""
        return self.s3_client
    
    def get_bucket_name(self):
        """Get bucket name"""
        return self.bucket_name
    
    def get_region(self):
        """Get region"""
        return self.region
    
    def is_configured(self):
        """Check if AWS is properly configured"""
        return self.s3_client is not None
    
    def get_config_status(self):
        """Get configuration status"""
        return {
            'aws_configured': self.is_configured(),
            'bucket_name': self.bucket_name,
            'region': self.region,
            'has_credentials': bool(self.access_key_id and self.secret_access_key)
        }
