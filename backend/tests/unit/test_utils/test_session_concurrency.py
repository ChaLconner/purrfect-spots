"""
Tests for session concurrency management.
"""

import pytest

from utils.session_concurrency import (
    MAX_CONCURRENT_SESSIONS,
    SESSION_TIMEOUT_SECONDS,
    detect_concurrent_different_ips,
    get_active_sessions,
    get_session_summary,
    invalidate_all_sessions,
    register_session,
    remove_session,
    reset_sessions,
)


@pytest.fixture(autouse=True)
def run_reset_sessions():
    """Reset session state before and after each test"""
    reset_sessions()
    yield
    reset_sessions()


def test_register_new_session():
    """Test registering a new session"""
    user_id = "user1"
    session_id = "session1"
    ip = "127.0.0.1"
    ua = "Mozilla/5.0"

    result = register_session(user_id, session_id, ip, ua)

    assert result["status"] == "registered"
    assert result["active_sessions"] == 1

    sessions = get_active_sessions(user_id)
    assert len(sessions) == 1
    assert sessions[0]["ip_address"] == ip
    assert sessions[0]["user_agent"] == ua


def test_refresh_existing_session():
    """Test refreshing an existing session"""
    user_id = "user1"
    session_id = "session1"

    register_session(user_id, session_id, "1.1.1.1", "UA1")
    result = register_session(user_id, session_id, "2.2.2.2", "UA2")

    assert result["status"] == "refreshed"
    assert result["active_sessions"] == 1

    sessions = get_active_sessions(user_id)
    assert len(sessions) == 1
    assert sessions[0]["ip_address"] == "2.2.2.2"


def test_concurrency_limit_exceeded():
    """Test kicking out the oldest session when limit is exceeded"""
    user_id = "user1"

    # Fill sessions to limit
    for i in range(MAX_CONCURRENT_SESSIONS):
        register_session(user_id, f"session{i}", f"ip{i}", f"ua{i}")

    # Add one more
    result = register_session(user_id, "session_new", "ip_new", "ua_new")

    assert result["status"] == "limit_exceeded"
    assert result["kicked_session"] == "session0"  # Oldest should be kicked
    assert result["active_sessions"] == MAX_CONCURRENT_SESSIONS - 1

    sessions = get_active_sessions(user_id)
    assert len(sessions) == MAX_CONCURRENT_SESSIONS - 1
    # Check session0 is gone
    session_ids = [s["session_id"] for s in sessions]
    assert not any(s.startswith("session0") for s in session_ids)


def test_remove_session():
    """Test removing a specific session"""
    user_id = "user1"
    session_id = "session1"

    register_session(user_id, session_id, "1.1.1.1", "UA")
    assert remove_session(user_id, session_id) is True
    assert len(get_active_sessions(user_id)) == 0

    # Remove non-existent session
    assert remove_session(user_id, "non_existent") is False
    # Remove from user with no sessions
    assert remove_session("no_user", "session1") is False


def test_invalidate_all_sessions():
    """Test invalidating all sessions for a user"""
    user_id = "user1"

    register_session(user_id, "s1", "ip1", "ua1")
    register_session(user_id, "s2", "ip2", "ua2")

    count = invalidate_all_sessions(user_id, reason="password_change")
    assert count == 2
    assert len(get_active_sessions(user_id)) == 0

    # Invalidate for user with no sessions
    assert invalidate_all_sessions("no_user") == 0


def test_detect_different_ips():
    """Test detection of sessions from different IPs"""
    user_id = "user1"

    register_session(user_id, "s1", "1.1.1.1", "ua1")
    assert detect_concurrent_different_ips(user_id) is None

    # Same IP again, still None
    register_session(user_id, "s2", "1.1.1.1", "ua2")
    assert detect_concurrent_different_ips(user_id) is None

    # Different IP
    register_session(user_id, "s3", "2.2.2.2", "ua3")
    diff_sessions = detect_concurrent_different_ips(user_id)
    assert diff_sessions is not None
    assert len(diff_sessions) == 3

    # User with no sessions
    assert detect_concurrent_different_ips("no_user") is None


def test_get_session_summary():
    """Test session summary statistics"""
    register_session("u1", "s1", "ip1", "ua1")
    register_session("u1", "s2", "ip2", "ua2")
    register_session("u2", "s3", "ip3", "ua3")

    summary = get_session_summary()
    assert summary["total_active_sessions"] == 3
    assert summary["users_with_active_sessions"] == 2
    assert summary["users_with_multiple_sessions"] == 1
    assert summary["max_concurrent_sessions"] == MAX_CONCURRENT_SESSIONS


def test_session_expiry():
    """Test that expired sessions are automatically cleaned"""
    # Use monkeypatch to simulate passage of time if possible
    # But since it uses time.time() directly in the function...
    from unittest.mock import patch

    user_id = "user1"

    # Mock time.time to simulate far future
    with patch("time.time") as mock_time:
        mock_time.return_value = 1000.0
        register_session(user_id, "s1", "ip1", "ua1")

        # Advance time beyond timeout
        mock_time.return_value = 1000.0 + SESSION_TIMEOUT_SECONDS + 10
        # Registering another session should clean s1
        register_session(user_id, "s2", "ip2", "ua2")

        sessions = get_active_sessions(user_id)
        # Note: get_active_sessions doesn't clean, it just filters by list
        # Actually register_session cleaned s1 during the second call.
        assert len(sessions) == 1
        # Check that we only have s2... (wait get_active_sessions truncates)
        assert sessions[0]["session_id"].startswith("s2")
