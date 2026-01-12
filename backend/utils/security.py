"""
Security utilities for Purrfect Spots
Provides input sanitization, XSS prevention, and file validation
"""
import re
import html
import magic
import bleach
from typing import Optional, Tuple, Set
from logger import logger

# ========== File Security Constants ==========
ALLOWED_IMAGE_MIMES: Set[str] = {
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/gif'
}

MAX_FILENAME_LENGTH = 255
MAX_LOCATION_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 1000
MAX_TAG_LENGTH = 50
MAX_TAGS_COUNT = 20

# Dangerous patterns to remove from user input
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',  # Script tags
    r'javascript:',                 # JavaScript protocol
    r'on\w+\s*=',                   # Event handlers
    r'data:text/html',             # Data URLs with HTML
]


# ========== Text Sanitization ==========
def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input to prevent XSS and injection attacks.
    
    Args:
        text: Raw text input
        max_length: Optional maximum length to enforce
        
    Returns:
        Sanitized text string
    """
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # HTML escape special characters
    text = html.escape(text, quote=True)
    
    # Remove any remaining dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Enforce max length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text


def sanitize_html(text: str, allowed_tags: Optional[list] = None) -> str:
    """
    Sanitize HTML content while preserving allowed tags.
    
    Args:
        text: Raw HTML text
        allowed_tags: List of allowed HTML tags (default: none)
        
    Returns:
        Sanitized HTML string
    """
    if not text:
        return ""
    
    if allowed_tags is None:
        allowed_tags = []  # No HTML tags allowed by default
    
    return bleach.clean(
        text,
        tags=allowed_tags,
        attributes={},
        strip=True
    )


def sanitize_tag(tag: str) -> str:
    """
    Sanitize a single tag for safe storage and display.
    
    Args:
        tag: Raw tag string
        
    Returns:
        Sanitized tag string
    """
    if not tag:
        return ""
    
    # Remove # prefix if present
    tag = tag.lstrip('#')
    
    # Keep only alphanumeric, Thai characters, and underscores
    # Allow: a-z, A-Z, 0-9, Thai (0E00-0E7F), underscore, space
    tag = re.sub(r'[^a-zA-Z0-9\u0E00-\u0E7F_\s-]', '', tag)
    
    # Normalize whitespace and convert to lowercase
    tag = re.sub(r'\s+', ' ', tag).strip().lower()
    
    # Enforce max length
    return tag[:MAX_TAG_LENGTH]


def sanitize_tags(tags: list) -> list:
    """
    Sanitize a list of tags.
    
    Args:
        tags: List of raw tag strings
        
    Returns:
        List of sanitized tag strings
    """
    if not tags or not isinstance(tags, list):
        return []
    
    sanitized = []
    seen = set()
    
    for tag in tags:
        if not tag or not isinstance(tag, str):
            continue
            
        clean_tag = sanitize_tag(tag)
        
        if clean_tag and clean_tag not in seen:
            sanitized.append(clean_tag)
            seen.add(clean_tag)
        
        # Limit number of tags
        if len(sanitized) >= MAX_TAGS_COUNT:
            break
    
    return sanitized


def sanitize_location_name(name: str) -> str:
    """
    Sanitize location name with specific rules.
    
    Args:
        name: Raw location name
        
    Returns:
        Sanitized location name
    """
    return sanitize_text(name, max_length=MAX_LOCATION_NAME_LENGTH)


def sanitize_description(description: str) -> str:
    """
    Sanitize description with specific rules.
    
    Args:
        description: Raw description
        
    Returns:
        Sanitized description
    """
    return sanitize_text(description, max_length=MAX_DESCRIPTION_LENGTH)


# ========== File Validation with Magic Bytes ==========
def validate_image_magic_bytes(file_content: bytes) -> Tuple[bool, str, str]:
    """
    Validate image file using magic bytes (file signature).
    This is more secure than checking Content-Type header which can be spoofed.
    
    Args:
        file_content: Raw file bytes
        
    Returns:
        Tuple of (is_valid, detected_mime_type, error_message)
    """
    if not file_content:
        return False, "", "Empty file content"
    
    try:
        # Detect MIME type from file content (first 2KB is enough)
        detected_mime = magic.from_buffer(file_content[:2048], mime=True)
        
        logger.debug(f"Detected MIME type from magic bytes: {detected_mime}")
        
        # Check if detected MIME is in allowed list
        if detected_mime not in ALLOWED_IMAGE_MIMES:
            return False, detected_mime, f"File type '{detected_mime}' is not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_MIMES)}"
        
        return True, detected_mime, ""
        
    except Exception as e:
        logger.error(f"Magic bytes validation failed: {str(e)}")
        return False, "", f"Failed to validate file type: {str(e)}"


def validate_content_type_matches(
    claimed_content_type: str, 
    file_content: bytes
) -> Tuple[bool, str]:
    """
    Validate that the claimed Content-Type matches the actual file content.
    
    Args:
        claimed_content_type: Content-Type header from request
        file_content: Raw file bytes
        
    Returns:
        Tuple of (is_match, actual_mime_type)
    """
    is_valid, detected_mime, error = validate_image_magic_bytes(file_content)
    
    if not is_valid:
        return False, error
    
    # Normalize MIME types for comparison
    claimed = claimed_content_type.lower().split(';')[0].strip()
    
    # Allow some variations (image/jpg vs image/jpeg)
    mime_aliases = {
        'image/jpg': 'image/jpeg',
    }
    
    claimed = mime_aliases.get(claimed, claimed)
    detected = mime_aliases.get(detected_mime, detected_mime)
    
    if claimed != detected:
        logger.warning(f"Content-Type mismatch: claimed={claimed}, detected={detected}")
        # Still return true but with actual type - we'll use the detected type
        return True, detected_mime
    
    return True, detected_mime


# ========== Security Logging ==========
def log_security_event(
    event_type: str,
    user_id: Optional[str] = None,
    details: Optional[dict] = None,
    severity: str = "INFO"
):
    """
    Log security-related events for audit trail.
    
    Args:
        event_type: Type of security event (e.g., "upload_attempt", "validation_failed")
        user_id: Optional user ID associated with the event
        details: Optional dictionary with additional details
        severity: Log severity level ("INFO", "WARNING", "ERROR")
    """
    log_message = f"SECURITY_EVENT: {event_type}"
    
    if user_id:
        log_message += f" | user_id={user_id}"
    
    if details:
        # Sanitize details to prevent log injection
        safe_details = {k: str(v)[:200] for k, v in details.items()}
        log_message += f" | details={safe_details}"
    
    if severity == "ERROR":
        logger.error(log_message)
    elif severity == "WARNING":
        logger.warning(log_message)
    else:
        logger.info(log_message)


# ========== Input Validation Helpers ==========
def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no path traversal, etc.)
    
    Args:
        filename: Filename to validate
        
    Returns:
        True if filename is safe, False otherwise
    """
    if not filename:
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for null bytes
    if '\x00' in filename:
        return False
    
    # Check length
    if len(filename) > MAX_FILENAME_LENGTH:
        return False
    
    return True
