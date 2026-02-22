"""
Security utilities for Purrfect Spots
Provides input sanitization, XSS prevention, and file validation
"""

import html
import re

import bleach
import magic

from logger import logger

# ========== File Security Constants ==========
ALLOWED_IMAGE_MIMES: set[str] = {"image/jpeg", "image/png", "image/webp", "image/gif"}

MAX_FILENAME_LENGTH = 255
MAX_LOCATION_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 1000
MAX_TAG_LENGTH = 50
MAX_TAGS_COUNT = 20

# Dangerous patterns to remove from user input
DANGEROUS_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # Script tags
    r"javascript:",  # JavaScript protocol
    r"on\w+\s*=",  # Event handlers
    r"data:text/html",  # Data URLs with HTML
]

from datetime import UTC
from typing import Any


# ========== Text Sanitization ==========
def sanitize_text(text: str, max_length: int | None = None) -> str:
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

    # Remove any dangerous patterns BEFORE escaping
    # If we escape first, patterns like <script> will become &lt;script&gt; and won't be caught
    for pattern in DANGEROUS_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # HTML escape special characters
    text = html.escape(text, quote=True)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Enforce max length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def sanitize_html(text: str, allowed_tags: list[str] | None = None) -> str:
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

    return bleach.clean(text, tags=allowed_tags, attributes={}, strip=True)


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
    tag = tag.lstrip("#")

    # Keep only alphanumeric, Thai characters, and underscores
    # Allow: a-z, A-Z, 0-9, Thai (0E00-0E7F), underscore, space
    tag = re.sub(r"[^a-zA-Z0-9\u0E00-\u0E7F_\s-]", "", tag)

    # Normalize whitespace and convert to lowercase
    tag = re.sub(r"\s+", " ", tag).strip().lower()

    # Enforce max length
    return tag[:MAX_TAG_LENGTH]


def sanitize_tags(tags: list[str]) -> list[str]:
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
def validate_image_magic_bytes(file_content: bytes) -> tuple[bool, str, str]:
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
            return (
                False,
                detected_mime,
                f"File type '{detected_mime}' is not allowed. Allowed types: {', '.join(ALLOWED_IMAGE_MIMES)}",
            )

        return True, detected_mime, ""

    except Exception as e:
        logger.error(f"Magic bytes validation failed: {e!s}")
        return False, "", f"Failed to validate file type: {e!s}"


def validate_content_type_matches(claimed_content_type: str, file_content: bytes) -> tuple[bool, str]:
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
    claimed = claimed_content_type.lower().split(";")[0].strip()

    # Allow some variations (image/jpg vs image/jpeg)
    mime_aliases = {
        "image/jpg": "image/jpeg",
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
    user_id: str | None = None,
    details: dict | None = None,
    severity: str = "INFO",
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """
    Log security-related events for audit trail.

    Args:
        event_type: Type of security event (e.g., "upload_attempt", "validation_failed")
        user_id: Optional user ID associated with the event
        details: Optional dictionary with additional details
        severity: Log severity level ("INFO", "WARNING", "ERROR")
        ip_address: Optional IP address of the request
        user_agent: Optional User-Agent string of the request
    """
    log_message = f"SECURITY_EVENT: {event_type}"

    if user_id:
        log_message += f" | user_id={user_id}"

    # SECURITY: Log IP address and user agent for security audit
    # This helps identify and track potential attackers
    if ip_address:
        log_message += f" | ip={ip_address}"

    if user_agent:
        # Sanitize user agent to prevent log injection and limit length
        safe_user_agent = str(user_agent)[:200].replace("\n", " ").replace("\r", " ")
        log_message += f" | user_agent={safe_user_agent}"

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


# ========== Audit Logging ==========
# SECURITY: Audit logging for sensitive operations
# This provides a comprehensive audit trail for compliance and security monitoring
# Sensitive operations that require audit logging:
# - User authentication (login, logout, token refresh)
# - User registration and account changes
# - Password changes and resets
# - Profile updates
# - File uploads and deletions
# - Data access (especially sensitive data)
# - Permission changes
# - Admin operations


def log_audit_event(
    action: str,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    success: bool = True,
) -> None:
    """
    Log audit events for sensitive operations.

    Args:
        action: Action performed (e.g., "user_login", "password_change", "photo_upload")
        user_id: Optional user ID who performed the action
        resource_type: Type of resource affected (e.g., "user", "photo", "profile")
        resource_id: Optional ID of the affected resource
        details: Optional dictionary with additional details
        ip_address: Optional IP address of the request
        user_agent: Optional User-Agent string of the request
        success: Whether the action was successful
    """
    import json
    from datetime import datetime

    # Build audit log entry
    audit_entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "action": action,
        "success": success,
    }

    if user_id:
        audit_entry["user_id"] = user_id

    if resource_type:
        audit_entry["resource_type"] = resource_type

    if resource_id:
        audit_entry["resource_id"] = resource_id

    if ip_address:
        audit_entry["ip_address"] = ip_address

    if user_agent:
        # Sanitize user agent to prevent log injection and limit length
        safe_user_agent = str(user_agent)[:200].replace("\n", " ").replace("\r", " ")
        audit_entry["user_agent"] = safe_user_agent

    if details:
        # Sanitize details to prevent log injection
        safe_details = {k: str(v)[:200] for k, v in details.items()}
        audit_entry["details"] = safe_details

    # Log as structured JSON for easy parsing
    log_message = f"AUDIT_EVENT: {json.dumps(audit_entry, separators=(',', ':'))}"

    if success:
        logger.info(log_message)
    else:
        logger.warning(log_message)


def log_authentication_event(
    action: str,
    user_id: str | None = None,
    email: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    success: bool = True,
    failure_reason: str | None = None,
) -> None:
    """
    Log authentication events for security monitoring.

    Args:
        action: Authentication action (e.g., "login", "logout", "token_refresh", "password_reset")
        user_id: Optional user ID (available after successful login)
        email: Optional email address (sanitized)
        ip_address: Optional IP address of the request
        user_agent: Optional User-Agent string of the request
        success: Whether the authentication was successful
        failure_reason: Optional reason for failure (e.g., "invalid_credentials", "account_locked")
    """
    details = {}
    if email:
        # Sanitize email - only show first 3 characters for privacy
        safe_email = email[:3] + "***@" + email.split("@")[1] if "@" in email else "***"
        details["email"] = safe_email

    if failure_reason:
        details["failure_reason"] = failure_reason

    log_audit_event(
        action=f"auth_{action}",
        user_id=user_id,
        resource_type="user_session",
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
    )


def log_data_access_event(
    action: str,
    user_id: str,
    resource_type: str,
    resource_id: str | None = None,
    access_type: str = "read",
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """
    Log data access events for compliance monitoring.

    Args:
        action: Action performed (e.g., "view_profile", "download_photo")
        user_id: User ID who accessed the data
        resource_type: Type of resource accessed
        resource_id: Optional ID of the accessed resource
        access_type: Type of access (read, write, delete)
        ip_address: Optional IP address of the request
        user_agent: Optional User-Agent string of the request
    """
    log_audit_event(
        action=f"data_{action}",
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details={"access_type": access_type},
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
    )


def log_file_operation_event(
    action: str,
    user_id: str,
    filename: str | None = None,
    file_size: int | None = None,
    file_type: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    success: bool = True,
    error_message: str | None = None,
) -> None:
    """
    Log file operation events for security monitoring.

    Args:
        action: File operation (e.g., "upload", "delete", "download")
        user_id: User ID who performed the operation
        filename: Optional filename (sanitized)
        file_size: Optional file size in bytes
        file_type: Optional file type (MIME type)
        ip_address: Optional IP address of the request
        user_agent: Optional User-Agent string of the request
        success: Whether the operation was successful
        error_message: Optional error message if operation failed
    """
    details: dict[str, Any] = {}
    if filename:
        # Sanitize filename - only show first 50 characters
        details["filename"] = filename[:50]

    if file_size is not None:
        details["file_size"] = file_size

    if file_type:
        details["file_type"] = file_type

    if error_message:
        details["error"] = error_message[:200]

    log_audit_event(
        action=f"file_{action}",
        user_id=user_id,
        resource_type="file",
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
    )


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
    if ".." in filename or "/" in filename or "\\" in filename:
        return False

    # Check for null bytes
    if "\x00" in filename:
        return False

    # Check length
    return not len(filename) > MAX_FILENAME_LENGTH
