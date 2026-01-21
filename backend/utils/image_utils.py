"""
Image optimization utilities for Purrfect Spots
Provides image compression, resizing, and format optimization before S3 upload
"""

import io

from PIL import Image

from logger import logger

# Configuration constants
MAX_IMAGE_DIMENSION = 1920  # Max width or height in pixels
JPEG_QUALITY = 85  # Quality for JPEG compression (1-100)
WEBP_QUALITY = 80  # Quality for WebP compression (1-100)
MAX_FILE_SIZE_MB = 5  # Target max file size after optimization


def optimize_image(
    image_content: bytes,
    content_type: str,
    max_dimension: int = MAX_IMAGE_DIMENSION,
    quality: int = JPEG_QUALITY,
    target_format: str | None = None,
) -> tuple[bytes, str]:
    """
    Optimize image for web delivery and storage.

    Args:
        image_content: Raw image bytes
        content_type: Original MIME type
        max_dimension: Maximum width or height
        quality: Compression quality (1-100)
        target_format: Force output format ('JPEG', 'WEBP', 'PNG') or None for auto

    Returns:
        Tuple of (optimized_bytes, new_content_type)
    """
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_content))
        original_format = img.format
        original_size = len(image_content)

        logger.debug(f"Original image: {img.size}, format={original_format}, size={original_size / 1024:.1f}KB")

        # Convert RGBA to RGB if saving as JPEG (JPEG doesn't support transparency)
        if img.mode in ("RGBA", "LA", "P"):
            # Create white background for transparent images
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # SECURITY: Strip EXIF metadata to protect user privacy
        # This removes GPS coordinates, camera info, timestamps, etc.
        # Paste image onto a new blank image to strip all metadata
        img_no_exif = Image.new(img.mode, img.size)
        img_no_exif.paste(img, (0, 0))
        img = img_no_exif
        logger.debug("Stripped EXIF metadata from image")

        # Resize if larger than max dimension (maintain aspect ratio)
        width, height = img.size
        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized image to: {img.size}")

        # Determine output format - Default to WEBP for best performance
        if target_format:
            output_format = target_format.upper()
        elif original_format == "GIF":
            output_format = "GIF"  # Keep GIF as-is (might be animated)
        else:
            output_format = "WEBP"  # Default to WEBP for best compression/performance

        # Save optimized image to bytes
        output_buffer = io.BytesIO()

        if output_format == "JPEG":
            img.save(
                output_buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
            )
            new_content_type = "image/jpeg"
        elif output_format == "WEBP":
            img.save(output_buffer, format="WEBP", quality=WEBP_QUALITY, optimize=True)
            new_content_type = "image/webp"
        elif output_format == "PNG":
            img.save(output_buffer, format="PNG", optimize=True)
            new_content_type = "image/png"
        elif output_format == "GIF":
            # For GIF, just return original to preserve animation
            return image_content, content_type
        else:
            img.save(output_buffer, format="JPEG", quality=quality, optimize=True)
            new_content_type = "image/jpeg"

        optimized_content = output_buffer.getvalue()
        optimized_size = len(optimized_content)

        # Log optimization results
        reduction = ((original_size - optimized_size) / original_size) * 100
        logger.info(
            f"Image optimized: {original_size / 1024:.1f}KB -> {optimized_size / 1024:.1f}KB "
            f"({reduction:.1f}% reduction), format: {output_format}"
        )

        # If optimized is larger than original (rare), return original
        if optimized_size > original_size and output_format == original_format:
            logger.debug("Optimized image larger than original, using original")
            return image_content, content_type

        return optimized_content, new_content_type

    except Exception as e:
        logger.error(f"Image optimization failed: {e!s}")
        # Return original image if optimization fails
        return image_content, content_type


def get_image_dimensions(image_content: bytes) -> tuple[int, int]:
    """
    Get image dimensions without full decode.

    Returns:
        Tuple of (width, height)
    """
    try:
        img = Image.open(io.BytesIO(image_content))
        return img.size
    except Exception as e:
        logger.error(f"Failed to get image dimensions: {e!s}")
        return (0, 0)


def is_valid_image(image_content: bytes) -> bool:
    """
    Verify that the content is a valid image.

    Returns:
        True if valid image, False otherwise
    """
    try:
        img = Image.open(io.BytesIO(image_content))
        img.verify()  # Verify image integrity
        return True
    except Exception:
        return False
