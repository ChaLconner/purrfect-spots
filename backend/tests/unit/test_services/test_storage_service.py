"""
Tests for Storage Service
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from services.storage_service import StorageService


class TestStorageService:
    """Test suite for StorageService"""

    @pytest.fixture
    def mock_boto3_client(self):
        """Mock boto3 S3 client"""
        with patch("boto3.client") as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3
            yield mock_s3

    @pytest.fixture
    def storage_service(self, mock_boto3_client):
        """Create StorageService instance with mocked S3"""
        with patch.dict(
            os.environ,
            {
                "AWS_REGION": "us-east-1",
                "AWS_S3_BUCKET": "test-bucket",
                "AWS_ACCESS_KEY_ID": "test-key",
                "AWS_SECRET_ACCESS_KEY": "test-secret",
            },
        ):
            service = StorageService()
            service.s3_client = mock_boto3_client
            return service

    def test_init_with_env_vars(self, mock_boto3_client):
        """Test StorageService initialization with environment variables"""
        with patch.dict(
            os.environ,
            {
                "AWS_REGION": "us-west-2",
                "AWS_S3_BUCKET": "my-bucket",
                "AWS_ACCESS_KEY_ID": "my-key",
                "AWS_SECRET_ACCESS_KEY": "my-secret",
            },
        ):
            service = StorageService()
            assert service.aws_region == "us-west-2"
            assert service.aws_bucket == "my-bucket"
            assert service.aws_access_key == "my-key"
            assert service.aws_secret_key == "my-secret"

    def test_init_with_defaults(self, mock_boto3_client):
        """Test StorageService uses defaults when env vars not set"""
        with patch.dict(os.environ, {}, clear=True):
            service = StorageService()
            assert service.aws_region == "ap-southeast-2"
            assert service.aws_bucket == "purrfect-spots-bucket"

    def test_init_without_credentials(self, mock_boto3_client):
        """Test StorageService initialization without AWS credentials"""
        with patch.dict(os.environ, {"AWS_REGION": "us-east-1"}, clear=True):
            # Should not raise an exception even without credentials
            service = StorageService()
            assert service.aws_access_key is None
            assert service.aws_secret_key is None

    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage_service):
        """Test successful file upload"""
        file_content = b"test image content"
        content_type = "image/jpeg"

        with patch("config.config") as mock_config:
            mock_config.CDN_BASE_URL = None

            url = await storage_service.upload_file(file_content, content_type, "jpg", "uploads")

            # Verify S3 client was called
            storage_service.s3_client.put_object.assert_called_once()
            call_kwargs = storage_service.s3_client.put_object.call_args[1]

            assert call_kwargs["Bucket"] == "test-bucket"
            assert call_kwargs["Body"] == file_content
            assert call_kwargs["ContentType"] == content_type
            assert "uploads/" in call_kwargs["Key"]
            assert call_kwargs["CacheControl"] == "public, max-age=31536000"
            assert call_kwargs["ContentDisposition"] == "inline"

            # Verify URL format
            assert "https://test-bucket.s3.us-east-1.amazonaws.com/uploads/" in url
            assert url.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_upload_file_with_cdn(self, storage_service):
        """Test file upload with CDN URL"""
        file_content = b"test content"

        with patch("config.config") as mock_config:
            mock_config.CDN_BASE_URL = "https://cdn.example.com"

            url = await storage_service.upload_file(file_content, "image/png", "png")

            assert url.startswith("https://cdn.example.com/upload/")
            assert url.endswith(".png")

    @pytest.mark.asyncio
    async def test_upload_file_custom_folder(self, storage_service):
        """Test file upload to custom folder"""
        file_content = b"test"

        with patch("config.config") as mock_config:
            mock_config.CDN_BASE_URL = None

            url = await storage_service.upload_file(file_content, "image/webp", "webp", "avatars")

            call_kwargs = storage_service.s3_client.put_object.call_args[1]
            assert "avatars/" in call_kwargs["Key"]
            assert "avatars/" in url

    @pytest.mark.asyncio
    async def test_upload_file_s3_error(self, storage_service):
        """Test upload file when S3 raises an error"""
        storage_service.s3_client.put_object.side_effect = Exception("S3 error")

        with pytest.raises(HTTPException) as exc:
            await storage_service.upload_file(b"test", "image/jpeg")

        assert exc.value.status_code == 500
        assert "Failed to upload image" in exc.value.detail

    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_service):
        """Test successful file deletion"""
        file_url = "https://test-bucket.s3.us-east-1.amazonaws.com/upload/test.jpg"

        await storage_service.delete_file(file_url)

        storage_service.s3_client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="upload/test.jpg")

    @pytest.mark.asyncio
    async def test_delete_file_cdn_url(self, storage_service):
        """Test file deletion with CDN URL"""
        file_url = "https://cdn.example.com/avatars/image.png"

        await storage_service.delete_file(file_url)

        storage_service.s3_client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="avatars/image.png")

    @pytest.mark.asyncio
    async def test_delete_file_s3_error(self, storage_service):
        """Test delete file handles S3 errors gracefully"""
        storage_service.s3_client.delete_object.side_effect = Exception("Delete error")

        # Should not raise exception, just log warning
        await storage_service.delete_file("https://example.com/upload/test.jpg")

        # Verify it tried to delete
        storage_service.s3_client.delete_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_file_invalid_url(self, storage_service):
        """Test delete file with invalid URL (too short)"""
        # URL with less than 2 parts after split - should handle gracefully
        await storage_service.delete_file("invalid")

        # Should not crash, may or may not call s3_client depending on implementation
        # Just verify it doesn't raise an exception
