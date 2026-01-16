import mimetypes

# Additional mime types mapping that might be missing in some environments
MIME_MAPPING = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def get_safe_file_extension(filename: str, content_type: str) -> str:
    """
    Get a safe file extension based on content type and filename.
    Prioritizes the content type mapping, then falls back to filename extension if safe.
    """
    # Try to map from content type first (more secure)
    ext = MIME_MAPPING.get(content_type.lower())
    if ext:
        return ext

    # Fallback to mimetypes library
    ext = mimetypes.guess_extension(content_type)
    if ext and ext in ALLOWED_EXTENSIONS:
        return ext

    # Last resort: check the actual filename extension against allowlist
    if "." in filename:
        raw_ext = "." + filename.rsplit(".", 1)[1].lower()
        if raw_ext in ALLOWED_EXTENSIONS:
            return raw_ext

    # Default safe fallback
    return ".jpg"


def validate_image_file(
    content_type: str, file_size: int, max_size_mb: int = 10
) -> None:
    """
    Validate image file size and type.
    Raises ValueError if invalid.
    """
    if not content_type or not content_type.startswith("image/"):
        raise ValueError("File must be an image")

    if file_size > max_size_mb * 1024 * 1024:
        raise ValueError(f"File too large (max {max_size_mb}MB)")
