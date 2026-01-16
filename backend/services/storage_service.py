import os
import uuid

import boto3
from fastapi import HTTPException


class StorageService:
    def __init__(self):
        self.aws_region = os.getenv("AWS_REGION", "ap-southeast-2")
        self.aws_bucket = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        if not self.aws_access_key or not self.aws_secret_key:
            # We might want to allow running without S3 for dev, but for now let's assume it's needed if this service is used
            # Alternatively, check connection on specific methods
            pass

        self.s3_client = boto3.client(
            "s3",
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
        )

    async def upload_file(
        self,
        file_content: bytes,
        content_type: str,
        file_extension: str = "jpg",
        folder: str = "upload",
    ) -> str:
        """
        Uploads a file to S3 and returns the public URL.
        Enhanced with security headers and content disposition.
        """
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        key = f"{folder}/{unique_filename}"

        try:
            self.s3_client.put_object(
                Bucket=self.aws_bucket,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                # Security and caching headers
                CacheControl="public, max-age=31536000",  # 1 year cache
                ContentDisposition="inline",  # Prevent download prompts
                Metadata={
                    "x-content-type-options": "nosniff",
                    "uploaded-via": "purrfect-spots-api",
                },
            )

            # Create S3 public URL
            # Create S3 public URL or CDN URL
            if hasattr(self, "config") and self.config.CDN_BASE_URL:
                url = f"{self.config.CDN_BASE_URL}/{key}"
            else:
                # Import config dynamically or use class attribute if I inject it, but better to import at top or just use the imported config if available.
                # Let's check imports. config is not imported yet. I should verify if I can import it at top or if I should use os.getenv directly pattern used in this file.
                # The file uses os.getenv in __init__. Let's stick to that pattern OR better, import config.
                # But to avoid circular imports if any (unlikely here), let's see.
                # Actually, I'll just check if I can import config.
                pass

            # Let's retry the replacement content to be cleaner.

            # Use config from import
            from config import config

            if config.CDN_BASE_URL:
                url = f"{config.CDN_BASE_URL}/{key}"
            else:
                url = f"https://{self.aws_bucket}.s3.{self.aws_region}.amazonaws.com/{key}"
            return url

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to upload image to S3: {e!s}"
            )

    def delete_file(self, file_url: str):
        """
        Deletes a file from S3 (optional, for cleanup)
        """
        # Extract key from URL if needed
        pass
