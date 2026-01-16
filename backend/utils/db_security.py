"""
Database Security Utilities

Provides SQL injection prevention and input validation
to protect against database attacks.

Features:
- Parameterized query helpers
- SQL injection pattern detection
- Safe identifier validation
- ORDER BY whitelist validation
- LIKE pattern escaping
"""

import re

from logger import logger

# ==============================================================================
# SQL Injection Detection Patterns
# ==============================================================================

# Common SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r"--",  # SQL comment
    r";.*(?:drop|delete|truncate|alter|update|insert)",  # Multi-statement attacks
    r"'.*or.*'.*=",  # OR injection
    r"union.*select",  # UNION injection
    r"exec(?:ute)?",  # EXEC commands
    r"xp_",  # Extended stored procedures (SQL Server)
    r"0x[0-9a-fA-F]+",  # Hex-encoded strings
    r"char\s*\(",  # CHAR() function abuse
    r"concat\s*\(",  # CONCAT() for string building
    r"/\*.*\*/",  # Block comments
    r"@@",  # System variables
    r"information_schema",  # Schema enumeration
    r"pg_",  # PostgreSQL system tables
    r"sys\.",  # System tables
]

SQL_INJECTION_REGEX = re.compile("|".join(SQL_INJECTION_PATTERNS), re.IGNORECASE)


# ==============================================================================
# Identifier Validation
# ==============================================================================


def is_safe_identifier(identifier: str) -> bool:
    """
    Check if string is a safe SQL identifier (table/column name).

    Only allows:
    - Alphanumeric characters
    - Underscores
    - Must start with letter or underscore

    Args:
        identifier: String to validate

    Returns:
        True if safe, False otherwise
    """
    if not identifier:
        return False
    if len(identifier) > 128:  # Reasonable max length
        return False
    return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", identifier))


def sanitize_order_by(
    column: str, allowed_columns: list[str], default: str | None = None
) -> str | None:
    """
    Safely validate and return column for ORDER BY clause.

    Uses whitelist approach - only allowed columns can be used.

    Args:
        column: Requested column name (may include - prefix for DESC)
        allowed_columns: Whitelist of allowed column names
        default: Default column if validation fails

    Returns:
        Safe column reference with optional DESC, or default
    """
    if not column:
        return default

    # Handle descending prefix
    descending = column.startswith("-")
    clean_column = column.lstrip("-")

    # Validate against whitelist
    if clean_column not in allowed_columns:
        logger.warning(f"Invalid ORDER BY column rejected: {column}")
        return default

    return f"{clean_column} DESC" if descending else clean_column


# ==============================================================================
# SQL Injection Detection
# ==============================================================================


def detect_sql_injection(value: str) -> bool:
    """
    Check if value contains potential SQL injection patterns.

    Args:
        value: String to check

    Returns:
        True if suspicious patterns detected
    """
    if not value:
        return False

    if SQL_INJECTION_REGEX.search(value):
        logger.warning(
            f"Potential SQL injection detected: {value[:50]}..."
            if len(value) > 50
            else f"Potential SQL injection detected: {value}"
        )
        return True

    return False


def sanitize_search_input(value: str, max_length: int = 100) -> str:
    """
    Sanitize user search input.

    Args:
        value: Raw search input
        max_length: Maximum allowed length

    Returns:
        Sanitized search string
    """
    if not value:
        return ""

    # Truncate to max length
    sanitized = value[:max_length]

    # Remove potentially dangerous characters
    sanitized = re.sub(r"[;\-\-\'\"\\]", "", sanitized)

    # Remove multiple spaces
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    return sanitized


# ==============================================================================
# LIKE Pattern Safety
# ==============================================================================


def escape_like_pattern(pattern: str) -> str:
    """
    Escape special characters for LIKE queries.

    Prevents wildcard injection in search patterns
    that could cause performance issues or data exposure.

    Args:
        pattern: Raw search pattern

    Returns:
        Escaped pattern safe for LIKE queries
    """
    # Escape SQL LIKE special characters
    pattern = pattern.replace("\\", "\\\\")
    pattern = pattern.replace("%", "\\%")
    pattern = pattern.replace("_", "\\_")
    return pattern


def build_safe_like_pattern(search_term: str, match_type: str = "contains") -> str:
    """
    Build a safe LIKE pattern from user input.

    Args:
        search_term: User's search term
        match_type: One of 'contains', 'starts', 'ends', 'exact'

    Returns:
        Safe LIKE pattern
    """
    escaped = escape_like_pattern(search_term)

    if match_type == "contains":
        return f"%{escaped}%"
    elif match_type == "starts":
        return f"{escaped}%"
    elif match_type == "ends":
        return f"%{escaped}"
    else:  # exact
        return escaped


# ==============================================================================
# UUID Validation
# ==============================================================================


UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def validate_uuid(value: str) -> bool:
    """
    Validate UUID format to prevent injection via ID fields.

    Args:
        value: String to validate

    Returns:
        True if valid UUID format
    """
    if not value:
        return False
    return bool(UUID_PATTERN.match(value))


def sanitize_uuid(value: str) -> str | None:
    """
    Validate and return UUID, or None if invalid.

    Args:
        value: Potential UUID string

    Returns:
        Lowercase UUID string or None
    """
    if validate_uuid(value):
        return value.lower()
    logger.warning(f"Invalid UUID rejected: {value[:50] if value else 'None'}...")
    return None


# ==============================================================================
# Numeric Validation
# ==============================================================================


def validate_positive_int(value: str, max_value: int = 1000000) -> int | None:
    """
    Safely parse and validate positive integer.

    Args:
        value: String to parse
        max_value: Maximum allowed value

    Returns:
        Valid integer or None
    """
    try:
        num = int(value)
        if 0 < num <= max_value:
            return num
    except (ValueError, TypeError):
        pass
    return None


def validate_pagination(
    page: str | None, limit: str | None, max_limit: int = 100
) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        page: Page number string
        limit: Items per page string
        max_limit: Maximum allowed limit

    Returns:
        Tuple of (validated_page, validated_limit)
    """
    validated_page = 1
    validated_limit = 20  # Default

    if page:
        try:
            p = int(page)
            if p > 0:
                validated_page = p
        except ValueError:
            pass

    if limit:
        try:
            lim = int(limit)
            if 0 < lim <= max_limit:
                validated_limit = lim
        except ValueError:
            pass

    return validated_page, validated_limit
