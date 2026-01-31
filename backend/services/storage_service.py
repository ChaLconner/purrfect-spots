import os
import uuid

import boto3
from fastapi import HTTPException

from logger import logger


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
            # Generate public URL (S3 or CDN)
            from config import config

            if config.CDN_BASE_URL:
                url = f"{config.CDN_BASE_URL}/{key}"
            else:
                url = f"https://{self.aws_bucket}.s3.{self.aws_region}.amazonaws.com/{key}"

            return url

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image to S3: {e!s}")

    def delete_file(self, file_url: str):
        """
        Deletes a file from S3 (optional, for cleanup)

        Args:
            file_url: Full public URL of the file
        """
        try:
            # Extract key from URL
            # Expected format: https://bucket.s3.region.amazonaws.com/folder/filename
            # or CDN URL

            # Simple heuristic: Split by / and take the last two parts (folder/filename)
            # This is fragile if URL structure changes, but works for current implementation
            parts = file_url.split("/")
            if len(parts) >= 2:
                key = f"{parts[-2]}/{parts[-1]}"

                self.s3_client.delete_object(Bucket=self.aws_bucket, Key=key)

        except Exception as e:
            # Log error but don't crash - this is a cleanup operation
            logger.warning("Cleanup operation unsuccessful for resource: %s (Error: %s)", file_url, e)


# Singleton instance
storage_service = StorageService()
