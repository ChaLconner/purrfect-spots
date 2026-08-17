"""
Image optimization utilities for Purrfect Spots
Provides image compression, resizing, and format optimization before S3 upload
"""

import contextlib
import io
import warnings
from typing import Any

from PIL import Image, ImageOps, ImageSequence

from app.logger import logger
from app.utils.security import MAX_IMAGE_PIXELS

# Configuration constants
MAX_IMAGE_DIMENSION = 1920  # Max width or height in pixels
JPEG_QUALITY = 85  # Quality for JPEG compression (1-100)
WEBP_QUALITY = 80  # Quality for WebP compression (1-100)
MAX_ANIMATED_GIF_FRAMES = 200
MAX_ANIMATED_GIF_TOTAL_PIXELS = MAX_IMAGE_PIXELS * 4


def _enforce_image_pixel_limit(img: Image.Image) -> None:
    """Reject images that exceed the configured maximum decoded pixel count."""
    width, height = img.size
    if width * height > MAX_IMAGE_PIXELS:
        raise ValueError(f"Image exceeds maximum allowed pixel count ({MAX_IMAGE_PIXELS})")


def _open_image_safely(image_source: bytes | Any) -> Image.Image:
    """Open an image while converting decompression bomb warnings into hard failures."""
    source = io.BytesIO(image_source) if isinstance(image_source, bytes) else image_source
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        img = Image.open(source)
        _enforce_image_pixel_limit(img)
        return img


def _validate_image_geometry(img: Image.Image) -> None:
    width, height = img.size
    if width < 10 or height < 10:
        raise ValueError("Image dimensions too small (minimum 10x10 required)")
    aspect_ratio = max(width, height) / max(min(width, height), 1)
    if aspect_ratio > 20.0:
        raise ValueError("Extreme aspect ratio rejected (maximum 20:1 ratio allowed)")


def _is_blank_image(img: Image.Image) -> bool:
    extrema = img.getextrema()
    if isinstance(extrema, list):
        return all(isinstance(e, tuple) and e[0] == e[1] for e in extrema)
    return (
        isinstance(extrema, tuple)
        and len(extrema) == 2
        and isinstance(extrema[0], (int, float))
        and extrema[0] == extrema[1]
    )


def _convert_image_to_rgb(img: Image.Image) -> Image.Image:
    if img.mode not in ("RGBA", "LA", "P"):
        return img if img.mode == "RGB" else img.convert("RGB")
    background = Image.new("RGB", img.size, (255, 255, 255))
    if img.mode == "P":
        img = img.convert("RGBA")
    background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
    return background


def _preprocess_image(image_content: bytes) -> tuple[Image.Image, str | None, int]:
    """Open image, apply EXIF orientation transpose, strip EXIF, check aspect ratio, convert mode."""
    img = _open_image_safely(image_content)
    original_format = img.format
    original_size = len(image_content)

    # Edge Case #2: Apply EXIF orientation transpose BEFORE stripping EXIF
    try:
        img = ImageOps.exif_transpose(img)
    except Exception as exc:
        logger.debug("ImageOps.exif_transpose skipped: %s", exc)

    # Edge Case #3 & Animated Images: Select 1st frame if animated GIF/WebP/TIFF
    if getattr(img, "is_animated", False):
        with contextlib.suppress(Exception):
            img.seek(0)

    # Edge Case #15: Reject extreme aspect ratios (ratio > 20:1) or tiny images (< 10px)
    _validate_image_geometry(img)

    # Edge Case #15: Reject solid color / blank images (e.g. solid black or solid white)
    if _is_blank_image(img):
        raise ValueError("Solid color or blank image rejected")

    logger.debug(f"Original image: {img.size}, format={original_format}, size={original_size / 1024:.1f}KB")

    # Edge Case #5: Convert RGBA/CMYK/LA/P/HSV/LAB safely to RGB
    img = _convert_image_to_rgb(img)

    # SECURITY: Strip EXIF & comment metadata to protect user privacy
    img_no_exif = Image.new(img.mode, img.size)
    img_no_exif.paste(img, (0, 0))
    img = img_no_exif
    logger.debug("Stripped EXIF metadata and normalized image canvas")

    return img, original_format, original_size


def _resize_image(img: Image.Image, max_dimension: int) -> Image.Image:
    """Resize image if dimensions exceed max."""
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
    return img


def _save_optimized_image(img: Image.Image, output_format: str, quality: int) -> tuple[io.BytesIO, str]:
    """Save the image to the target format."""
    output_buffer = io.BytesIO()
    new_content_type = ""

    if output_format == "GIF":
        img.save(output_buffer, format="GIF", optimize=True)
        new_content_type = "image/gif"
    elif output_format == "WEBP":
        img.save(output_buffer, format="WEBP", quality=WEBP_QUALITY, optimize=True)
        new_content_type = "image/webp"
    elif output_format == "PNG":
        img.save(output_buffer, format="PNG", optimize=True)
        new_content_type = "image/png"
    else:
        # Default or JPEG
        img.save(
            output_buffer,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
        )
        new_content_type = "image/jpeg"

    return output_buffer, new_content_type


def _prepare_gif_frame(frame: Image.Image) -> Image.Image:
    """Normalize one GIF frame while removing metadata and unsafe dimensions."""
    frame = frame.copy()
    try:
        frame = ImageOps.exif_transpose(frame)
    except Exception as exc:
        logger.debug("GIF frame EXIF transpose skipped: %s", exc)

    _enforce_image_pixel_limit(frame)
    width, height = frame.size
    if width < 10 or height < 10:
        raise ValueError("Image dimensions too small (minimum 10x10 required)")
    aspect_ratio = max(width, height) / max(min(width, height), 1)
    if aspect_ratio > 20.0:
        raise ValueError("Extreme aspect ratio rejected (maximum 20:1 ratio allowed)")

    if frame.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", frame.size, (255, 255, 255))
        if frame.mode == "P":
            frame = frame.convert("RGBA")
        background.paste(frame, mask=frame.split()[-1] if frame.mode == "RGBA" else None)
        frame = background
    elif frame.mode != "RGB":
        frame = frame.convert("RGB")

    # Construct a fresh canvas so GIF comments, palettes, and other metadata
    # from every frame are not copied into the optimized output.
    clean_frame = Image.new("RGB", frame.size)
    clean_frame.paste(frame, (0, 0))
    return clean_frame


def _is_animated_gif(image_content: bytes) -> bool:
    """Return whether the input is a multi-frame GIF."""
    try:
        img = _open_image_safely(image_content)
        return img.format == "GIF" and bool(getattr(img, "is_animated", False)) and getattr(img, "n_frames", 1) > 1
    except Exception:
        return False


def _optimize_animated_gif(image_content: bytes, max_dimension: int) -> tuple[bytes, str]:
    """Optimize every GIF frame without flattening the animation."""
    frames: list[Image.Image] = []
    durations: list[int] = []
    total_pixels = 0
    with io.BytesIO(image_content) as source:
        source_image = _open_image_safely(source)
        if source_image.format != "GIF" or not getattr(source_image, "is_animated", False):
            raise ValueError("Animated GIF expected")

        loop = int(source_image.info.get("loop", 0) or 0)
        for frame_number, frame in enumerate(ImageSequence.Iterator(source_image), start=1):
            if frame_number > MAX_ANIMATED_GIF_FRAMES:
                raise ValueError(f"Animated GIF exceeds maximum frame count ({MAX_ANIMATED_GIF_FRAMES})")
            width, height = frame.size
            total_pixels += width * height
            if total_pixels > MAX_ANIMATED_GIF_TOTAL_PIXELS:
                raise ValueError("Animated GIF exceeds maximum decoded pixel budget")
            prepared = _prepare_gif_frame(frame)
            frames.append(_resize_image(prepared, max_dimension))
            duration = frame.info.get("duration", source_image.info.get("duration", 100))
            durations.append(max(20, int(duration or 100)))

    if not frames:
        raise ValueError("Animated GIF contains no frames")

    output = io.BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=loop,
        disposal=2,
        optimize=True,
    )
    return output.getvalue(), "image/gif"


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
        logger.debug("Optimizing image declared as %s", content_type)
        # Preserve multi-frame GIFs unless the caller explicitly requests a
        # different output format. The normal preprocessing path intentionally
        # selects the first frame for other animated formats.
        if (target_format is None or target_format.upper() == "GIF") and _is_animated_gif(image_content):
            optimized_content, new_content_type = _optimize_animated_gif(image_content, max_dimension)
            logger.info(
                "Animated GIF optimized: %.1fKB -> %.1fKB (%.1f%% reduction)",
                len(image_content) / 1024,
                len(optimized_content) / 1024,
                ((len(image_content) - len(optimized_content)) / len(image_content)) * 100,
            )
            return optimized_content, new_content_type

        # Preprocess (open, strip EXIF, convert mode)
        img, original_format, original_size = _preprocess_image(image_content)

        # Resize if needed
        img = _resize_image(img, max_dimension)

        # Determine output format - Default to WEBP for best performance
        if target_format:
            output_format = target_format.upper()
        elif original_format == "GIF":
            output_format = "GIF"  # Keep GIF as-is (might be animated)
        else:
            output_format = "WEBP"  # Default to WEBP for best compression/performance

        # Save optimized image
        output_buffer, new_content_type = _save_optimized_image(img, output_format, quality)

        optimized_content = output_buffer.getvalue()
        optimized_size = len(optimized_content)

        # Log optimization results
        reduction = ((original_size - optimized_size) / original_size) * 100
        logger.info(
            f"Image optimized: {original_size / 1024:.1f}KB -> {optimized_size / 1024:.1f}KB "
            f"({reduction:.1f}% reduction), format: {output_format}"
        )

        return optimized_content, new_content_type

    except Exception as e:
        logger.warning(f"Image optimization skipped/failed: {e!s}")
        raise ValueError("Image optimization failed") from e


def get_image_dimensions(image_content: bytes) -> tuple[int, int]:
    """
    Get image dimensions without full decode.

    Returns:
        Tuple of (width, height)
    """
    try:
        img = _open_image_safely(image_content)
        return img.size
    except Exception as e:
        logger.warning(f"Failed to get image dimensions: {e!s}")
        return (0, 0)


def is_valid_image(image_content: bytes | Any) -> bool:
    """
    Verify that the content is a valid image.

    Returns:
        True if valid image, False otherwise
    """

    from app.logger import logger

    position = None
    try:
        if not isinstance(image_content, bytes) and hasattr(image_content, "tell"):
            position = image_content.tell()
        img = _open_image_safely(image_content)
        img.verify()  # Verify image integrity
        return True
    except Exception as e:
        logger.debug(f"Image validation failed: {e}")
        return False
    finally:
        if position is not None and hasattr(image_content, "seek"):
            image_content.seek(position)
