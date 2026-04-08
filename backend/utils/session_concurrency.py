"""
Session Concurrency Limiter for Purrfect Spots

Provides session management to limit concurrent active sessions per user.
Helps prevent account sharing and detect compromised credentials.
"""

import time
from datetime import UTC, datetime

from logger import logger

# In-memory session tracking (use Redis in production for distributed systems)
_user_sessions: dict[str, list[dict]] = {}

# Configuration
MAX_CONCURRENT_SESSIONS = 3  # Maximum sessions per user
SESSION_TIMEOUT_SECONDS = 86400  # 24 hours


def register_session(user_id: str, session_id: str, ip_address: str, user_agent: str) -> dict:
    """
    Register a new session for a user.

    Args:
        user_id: User ID
        session_id: Unique session identifier (JWT JTI or custom ID)
        ip_address: Source IP address
        user_agent: User agent string

    Returns:
        Dictionary with session status and any kicked sessions
    """
    now = time.time()

    if user_id not in _user_sessions:
        _user_sessions[user_id] = []

    # Clean expired sessions
    _user_sessions[user_id] = [s for s in _user_sessions[user_id] if now - s["created_at"] < SESSION_TIMEOUT_SECONDS]

    # Check if session already exists (refresh)
    for session in _user_sessions[user_id]:
        if session["session_id"] == session_id:
            session["last_active"] = now
            session["ip_address"] = ip_address
            return {"status": "refreshed", "active_sessions": len(_user_sessions[user_id])}

    # Check concurrent session limit
    if len(_user_sessions[user_id]) >= MAX_CONCURRENT_SESSIONS:
        # Kick oldest session
        kicked = _user_sessions[user_id].pop(0)
        logger.warning(
            f"Session concurrency limit exceeded | "
            f"user_id={user_id} | kicked_session={kicked['session_id'][:8]}... | "
            f"active_sessions={len(_user_sessions[user_id])}"
        )
        return {
            "status": "limit_exceeded",
            "kicked_session": kicked["session_id"],
            "kicked_ip": kicked["ip_address"],
            "active_sessions": len(_user_sessions[user_id]),
        }

    # Register new session
    _user_sessions[user_id].append(
        {
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent[:200],
            "created_at": now,
            "last_active": now,
        }
    )

    return {"status": "registered", "active_sessions": len(_user_sessions[user_id])}


def remove_session(user_id: str, session_id: str) -> bool:
    """
    Remove a session for a user (logout).

    Args:
        user_id: User ID
        session_id: Session identifier to remove

    Returns:
        True if session was removed, False if not found
    """
    if user_id not in _user_sessions:
        return False

    initial_count = len(_user_sessions[user_id])
    _user_sessions[user_id] = [s for s in _user_sessions[user_id] if s["session_id"] != session_id]

    removed = len(_user_sessions[user_id]) < initial_count
    if removed:
        logger.info(f"Session removed | user_id={user_id} | session_id={session_id[:8]}...")

    return removed


def invalidate_all_sessions(user_id: str, reason: str = "security") -> int:
    """
    Invalidate all sessions for a user (force logout everywhere).

    Args:
        user_id: User ID
        reason: Reason for invalidation

    Returns:
        Number of sessions invalidated
    """
    if user_id not in _user_sessions:
        return 0

    count = len(_user_sessions[user_id])
    _user_sessions[user_id] = []

    logger.warning(f"All sessions invalidated | user_id={user_id} | count={count} | reason={reason}")

    return count


def get_active_sessions(user_id: str) -> list[dict]:
    """
    Get active sessions for a user.

    Args:
        user_id: User ID

    Returns:
        List of active session information
    """
    if user_id not in _user_sessions:
        return []

    now = time.time()
    return [
        {
            "session_id": s["session_id"][:8] + "...",
            "ip_address": s["ip_address"],
            "user_agent": s["user_agent"],
            "created_at": datetime.fromtimestamp(s["created_at"], UTC).isoformat(),
            "last_active": datetime.fromtimestamp(s["last_active"], UTC).isoformat(),
            "is_current": now - s["last_active"] < 60,  # Active within last minute
        }
        for s in _user_sessions[user_id]
    ]


def detect_concurrent_different_ips(user_id: str) -> list[dict] | None:
    """
    Detect if user has active sessions from different IP addresses.
    This could indicate compromised credentials.

    Args:
        user_id: User ID

    Returns:
        List of sessions from different IPs if detected, None otherwise
    """
    if user_id not in _user_sessions:
        return None

    sessions = _user_sessions[user_id]
    unique_ips = {s["ip_address"] for s in sessions}

    if len(unique_ips) > 1:
        logger.warning(f"Concurrent sessions from different IPs detected | user_id={user_id} | ips={unique_ips}")
        return get_active_sessions(user_id)

    return None


def get_session_summary() -> dict:
    """
    Get summary of session tracking.

    Returns:
        Dictionary with session statistics
    """
    total_sessions = sum(len(sessions) for sessions in _user_sessions.values())
    users_with_multiple = sum(1 for sessions in _user_sessions.values() if len(sessions) > 1)

    return {
        "total_active_sessions": total_sessions,
        "users_with_active_sessions": len(_user_sessions),
        "users_with_multiple_sessions": users_with_multiple,
        "max_concurrent_sessions": MAX_CONCURRENT_SESSIONS,
        "session_timeout_seconds": SESSION_TIMEOUT_SECONDS,
    }


def reset_sessions() -> None:
    """Reset all session tracking (for testing or manual reset)."""
    _user_sessions.clear()
    logger.info("Session tracking reset")
