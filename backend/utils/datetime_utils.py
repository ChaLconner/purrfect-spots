"""
DateTime Utilities

Provides timezone-aware datetime utilities to avoid deprecated utcnow().
Use these functions instead of datetime.utcnow() throughout the codebase.
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.
    
    This replaces the deprecated datetime.utcnow() which is scheduled
    for removal in Python 3.16.
    
    Returns:
        Timezone-aware datetime object in UTC
        
    Usage:
        from utils.datetime_utils import utc_now
        
        now = utc_now()
        iso_string = utc_now_iso()
    """
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """
    Get current UTC time as ISO 8601 formatted string.
    
    Returns:
        ISO 8601 formatted string (e.g., "2024-01-12T15:30:00+00:00")
    """
    return datetime.now(timezone.utc).isoformat()


def to_utc(dt: datetime) -> datetime:
    """
    Convert a datetime to UTC timezone.
    
    Args:
        dt: A datetime object (naive or aware)
        
    Returns:
        Timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        # Assume naive datetime is in UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def from_iso(iso_string: str) -> datetime:
    """
    Parse an ISO 8601 string to timezone-aware datetime.
    
    Args:
        iso_string: ISO 8601 formatted string
        
    Returns:
        Timezone-aware datetime object
    """
    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return to_utc(dt)
