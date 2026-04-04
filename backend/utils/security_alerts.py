"""
Security Alert System for Purrfect Spots

Provides suspicious activity detection and alerting for:
- Brute force login attempts
- Unusual admin access patterns
- Bulk data operations
- Failed permission checks
- Geographic anomalies
"""

import time
from datetime import UTC, datetime

from logger import logger

# Thresholds for suspicious activity detection
BRUTE_FORCE_THRESHOLD = 5  # Failed attempts before alerting
BRUTE_FORCE_WINDOW = 300  # 5 minutes in seconds
BULK_OPERATION_THRESHOLD = 50  # Records before alerting
FAILED_PERMISSION_THRESHOLD = 10  # Failed checks before alerting
FAILED_PERMISSION_WINDOW = 60  # 1 minute in seconds

# In-memory tracking (use Redis in production for distributed systems)
_failed_logins: dict[str, list[float]] = {}
_failed_permissions: dict[str, list[float]] = {}
_bulk_operations: dict[str, list[float]] = {}


def track_failed_login(user_identifier: str, ip_address: str, reason: str = "invalid_credentials") -> bool:
    """
    Track failed login attempts and alert if threshold exceeded.

    Args:
        user_identifier: Email or user ID that failed to authenticate
        ip_address: Source IP address
        reason: Reason for failure

    Returns:
        True if alert should be triggered, False otherwise
    """
    now = time.time()
    key = f"{ip_address}:{user_identifier}"

    if key not in _failed_logins:
        _failed_logins[key] = []

    # Clean old entries outside the window
    _failed_logins[key] = [t for t in _failed_logins[key] if now - t < BRUTE_FORCE_WINDOW]
    _failed_logins[key].append(now)

    attempt_count = len(_failed_logins[key])

    if attempt_count >= BRUTE_FORCE_THRESHOLD:
        logger.warning(
            f"SECURITY_ALERT: Possible brute force attack detected | "
            f"ip={ip_address} | user={user_identifier} | "
            f"attempts={attempt_count} | window={BRUTE_FORCE_WINDOW}s | "
            f"reason={reason}"
        )
        return True

    return False


def track_failed_permission_check(
    user_id: str,
    required_permission: str,
    ip_address: str,
    endpoint: str,
) -> bool:
    """
    Track failed permission checks and alert if threshold exceeded.

    Args:
        user_id: User ID that failed permission check
        required_permission: Permission that was required
        ip_address: Source IP address
        endpoint: Endpoint that was accessed

    Returns:
        True if alert should be triggered, False otherwise
    """
    now = time.time()
    key = f"{user_id}:{endpoint}"

    if key not in _failed_permissions:
        _failed_permissions[key] = []

    # Clean old entries outside the window
    _failed_permissions[key] = [t for t in _failed_permissions[key] if now - t < FAILED_PERMISSION_WINDOW]
    _failed_permissions[key].append(now)

    fail_count = len(_failed_permissions[key])

    if fail_count >= FAILED_PERMISSION_THRESHOLD:
        logger.warning(
            f"SECURITY_ALERT: Repeated permission violations detected | "
            f"user_id={user_id} | ip={ip_address} | "
            f"permission={required_permission} | endpoint={endpoint} | "
            f"violations={fail_count} | window={FAILED_PERMISSION_WINDOW}s"
        )
        return True

    return False


def track_bulk_operation(
    user_id: str,
    operation: str,
    record_count: int,
    ip_address: str,
) -> bool:
    """
    Track bulk operations and alert if threshold exceeded.

    Args:
        user_id: User ID performing the operation
        operation: Type of bulk operation (ban, delete, export, etc.)
        record_count: Number of records affected
        ip_address: Source IP address

    Returns:
        True if alert should be triggered, False otherwise
    """
    now = time.time()
    key = f"{user_id}:{operation}"

    if key not in _bulk_operations:
        _bulk_operations[key] = []

    _bulk_operations[key].append(now)

    if record_count >= BULK_OPERATION_THRESHOLD:
        logger.warning(
            f"SECURITY_ALERT: Large bulk operation detected | "
            f"user_id={user_id} | operation={operation} | "
            f"record_count={record_count} | ip={ip_address}"
        )
        return True

    return False


def track_suspicious_user_agent(user_agent: str, ip_address: str) -> bool:
    """
    Detect suspicious user agents (bots, scanners, etc.).

    Args:
        user_agent: User agent string
        ip_address: Source IP address

    Returns:
        True if suspicious, False otherwise
    """
    suspicious_patterns = [
        "sqlmap",
        "nikto",
        "nmap",
        "masscan",
        "dirbuster",
        "gobuster",
        "wfuzz",
        "burpsuite",
        "zap",
        "hydra",
        "metasploit",
    ]

    ua_lower = user_agent.lower()
    for pattern in suspicious_patterns:
        if pattern in ua_lower:
            logger.warning(
                f"SECURITY_ALERT: Suspicious user agent detected | "
                f"ip={ip_address} | pattern={pattern} | "
                f"user_agent={user_agent[:100]}"
            )
            return True

    return False


def track_geo_anomaly(user_id: str, country: str, ip_address: str, last_country: str | None = None) -> bool:
    """
    Detect geographic anomalies (impossible travel, blocked countries).

    Args:
        user_id: User ID
        country: Current country code
        ip_address: Source IP address
        last_country: Previous country code

    Returns:
        True if anomaly detected, False otherwise
    """
    # List of blocked/sanctioned countries (example)
    blocked_countries = {"KP", "IR", "SY", "CU"}

    if country in blocked_countries:
        logger.warning(
            f"SECURITY_ALERT: Access from blocked country | user_id={user_id} | country={country} | ip={ip_address}"
        )
        return True

    # Impossible travel detection (different countries in short time)
    if last_country and country != last_country:
        logger.warning(
            f"SECURITY_ALERT: Geographic location change detected | "
            f"user_id={user_id} | from={last_country} | to={country} | ip={ip_address}"
        )
        return True

    return False


def get_alert_summary() -> dict:
    """
    Get summary of current security alerts.

    Returns:
        Dictionary with alert counts and details
    """
    now = time.time()

    # Clean expired entries
    for key in list(_failed_logins.keys()):
        _failed_logins[key] = [t for t in _failed_logins[key] if now - t < BRUTE_FORCE_WINDOW]
        if not _failed_logins[key]:
            del _failed_logins[key]

    for key in list(_failed_permissions.keys()):
        _failed_permissions[key] = [t for t in _failed_permissions[key] if now - t < FAILED_PERMISSION_WINDOW]
        if not _failed_permissions[key]:
            del _failed_permissions[key]

    return {
        "active_failed_login_sources": len(_failed_logins),
        "active_permission_violation_sources": len(_failed_permissions),
        "bulk_operations_tracked": len(_bulk_operations),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def reset_alerts() -> None:
    """Reset all alert tracking (for testing or manual reset)."""
    _failed_logins.clear()
    _failed_permissions.clear()
    _bulk_operations.clear()
    logger.info("Security alerts reset")
