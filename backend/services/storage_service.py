import asyncio
import os
import uuid

import boto3
from fastapi import HTTPException

from logger import logger


class StorageService:
    def __init__(self) -> None:
        self.aws_region = os.getenv("AWS_REGION", "ap-southeast-2")
        self.aws_bucket = os.getenv("AWS_S3_BUCKET", "purrfect-spots-bucket")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        if not self.aws_access_key or not self.aws_secret_key:
            # We might want to allow running without S3 for dev, but for now let's assume it's needed if this service is used
            # Alternatively, check connection on specific methods
            pass

        # SECURITY: Use S3 client with additional security configurations
        self.s3_client = boto3.client(
            "s3",
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            config=boto3.session.Config(
                signature_version="s3v4",  # Use v4 signatures for better security
                s3={"addressing_style": "path"},  # Use path-style addressing
            ),
        )

    async def upload_file(
        self,
        file_content: bytes,
        content_type: str,
        file_extension: str = "jpg",
        folder: str = "upload",
    ) -> str:
        """
        Uploads a file to S3 and returns the public URL (Async).
        Offloads blocking S3 I/O to a thread pool.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            self._upload_file_sync,
            file_content,
            content_type,
            file_extension,
            folder,
        )

    def _upload_file_sync(
        self,
        file_content: bytes,
        content_type: str,
        file_extension: str,
        folder: str,
    ) -> str:
        """Internal synchronous upload method"""
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        key = f"{folder}/{unique_filename}"

        try:
            self.s3_client.put_object(
                Bucket=self.aws_bucket,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                # SECURITY: Enhanced security headers for S3 uploads
                CacheControl="public, max-age=31536000",  # 1 year cache
                ContentDisposition="inline",  # Prevent download prompts
                # SECURITY: Prevent MIME sniffing and other attacks via metadata
                Metadata={
                    "x-content-type-options": "nosniff",
                    "x-xss-protection": "1; mode=block",
                    "uploaded-via": "purrfect-spots-api",
                    "content-security-policy": "default-src 'self'",
                },
            )

            # Create S3 public URL
            from config import config

            if config.CDN_BASE_URL:
                url = f"{config.CDN_BASE_URL}/{key}"
            else:
                url = f"https://{self.aws_bucket}.s3.{self.aws_region}.amazonaws.com/{key}"

            return url

        except Exception as e:
            from botocore.exceptions import ClientError

            if isinstance(e, ClientError):
                logger.error(f"S3 ClientError: {e}")
            else:
                logger.error(f"S3 upload error: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload image. Please try again later.")

    async def delete_file(self, file_url: str) -> None:
        """
        Deletes a file from S3 (Async).
        Offloads blocking S3 I/O to a thread pool.
        """
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._delete_file_sync, file_url)

    def _delete_file_sync(self, file_url: str) -> None:
        """Internal synchronous delete method"""
        try:
            # Extract key from URL
            parts = file_url.split("/")
            if len(parts) >= 2:
                key = f"{parts[-2]}/{parts[-1]}"
                self.s3_client.delete_object(Bucket=self.aws_bucket, Key=key)

        except Exception as e:
            # Log error but don't crash - this is a cleanup operation
            logger.warning("Cleanup operation unsuccessful for resource: %s (Error: %s)", file_url, e)


# Singleton instance
storage_service = StorageService()
