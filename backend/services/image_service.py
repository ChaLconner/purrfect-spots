"""
Service for image processing, optimization, and CDN management.
"""

from typing import Any

from config import config


class ImageService:
    @staticmethod
    def optimize_image_url(url: str | None, width: int = 300) -> str | None:
        """
        Optimize image URL:
        1. Rewrite to CDN if configured
        2. Append transformation parameters if supported (Supabase)
        """
        if not url:
            return url

        # 1. CDN Rewrite
        # Fallback values if config doesn't have these specific attributes directly but they are in env
        s3_bucket = getattr(config, "aws_bucket", "purrfect-spots-bucket")
        aws_region = getattr(config, "aws_region", "ap-southeast-2")
        s3_domain = f"{s3_bucket}.s3.{aws_region}.amazonaws.com"

        final_url = url
        if config.CDN_BASE_URL and s3_domain in url:
            final_url = url.replace(f"https://{s3_domain}", config.CDN_BASE_URL)
        
        # 2. Resizing and Compression
        # Supabase Storage Native Transformation
        if "supabase.co/storage/v1/object/public" in final_url:
            separator = "&" if "?" in final_url else "?"
            return f"{final_url}{separator}width={width}&quality=80&resize=cover&format=webp"

        # S3 / External Storage Proxy (using wsrv.nl)
        # This gives S3 'superpowers' to resize images on the fly
        # Only proxy if a specific width is requested and enabled in config
        if width and config.ENABLE_IMAGE_PROXY:
            from urllib.parse import quote
            encoded_url = quote(final_url)
            return f"https://wsrv.nl/?url={encoded_url}&w={width}&q=80&output=webp"

        return final_url

    @classmethod
    def process_photos(cls, photos: list[dict[str, Any]], width: int = 500) -> list[dict[str, Any]]:
        """Process a list of photos with optimizations"""
        for photo in photos:
            if "image_url" in photo:
                photo["image_url"] = cls.optimize_image_url(photo["image_url"], width)
        return photos
