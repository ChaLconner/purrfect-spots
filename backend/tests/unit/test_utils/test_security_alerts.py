"""
Tests for security alert system.
"""

import pytest

from utils.security_alerts import (
    BRUTE_FORCE_THRESHOLD,
    BULK_OPERATION_THRESHOLD,
    FAILED_PERMISSION_THRESHOLD,
    get_alert_summary,
    reset_alerts,
    track_bulk_operation,
    track_failed_login,
    track_failed_permission_check,
    track_geo_anomaly,
    track_suspicious_user_agent,
)


@pytest.fixture(autouse=True)
def run_reset_alerts():
    """Reset alerts before and after each test"""
    reset_alerts()
    yield
    reset_alerts()


def test_track_failed_login() -> None:
    """Test brute force detection for failed logins"""
    user = "user@example.com"
    ip = "127.0.0.1"

    # Below threshold
    for _ in range(BRUTE_FORCE_THRESHOLD - 1):
        assert track_failed_login(user, ip) is False

    # Reach threshold
    assert track_failed_login(user, ip) is True

    # Summary should show the source
    summary = get_alert_summary()
    assert summary["active_failed_login_sources"] == 1


def test_track_failed_permission_check() -> None:
    """Test detection of repeated permission violations"""
    user_id = "user123"
    permission = "admin_write"
    ip = "1.2.3.4"
    endpoint = "/admin/delete"

    # Below threshold
    for _ in range(FAILED_PERMISSION_THRESHOLD - 1):
        assert track_failed_permission_check(user_id, permission, ip, endpoint) is False

    # Reach threshold
    assert track_failed_permission_check(user_id, permission, ip, endpoint) is True

    summary = get_alert_summary()
    assert summary["active_permission_violation_sources"] == 1


def test_track_bulk_operation() -> None:
    """Test detection of large bulk operations"""
    user_id = "admin1"
    ip = "1.1.1.1"

    # Small operation
    assert track_bulk_operation(user_id, "delete_photos", 5, ip) is False

    # Large operation
    assert track_bulk_operation(user_id, "delete_photos", BULK_OPERATION_THRESHOLD, ip) is True

    summary = get_alert_summary()
    assert summary["bulk_operations_tracked"] == 1


def test_track_suspicious_user_agent() -> None:
    """Test detection of suspicious user agents"""
    assert track_suspicious_user_agent("Mozilla/5.0", "1.1.1.1") is False
    assert track_suspicious_user_agent("sqlmap/1.4.11#stable", "1.1.1.1") is True
    assert track_suspicious_user_agent("nikto-2.1.6", "2.2.2.2") is True


def test_track_geo_anomaly() -> None:
    """Test detection of geographic anomalies"""
    user_id = "user1"
    ip = "1.1.1.1"

    # Normal access
    assert track_geo_anomaly(user_id, "TH", ip) is False

    # Blocked country
    assert track_geo_anomaly(user_id, "KP", ip) is True

    # Location change (impossible travel)
    assert track_geo_anomaly(user_id, "US", ip, last_country="TH") is True


def test_alert_summary_cleanup() -> None:
    """Test that expired alerts are cleaned from summary"""
    from unittest.mock import patch

    with patch("time.time") as mock_time:
        mock_time.return_value = 1000.0
        track_failed_login("u1", "ip1")

        summary = get_alert_summary()
        assert summary["active_failed_login_sources"] == 1

        # Advance time beyond window
        mock_time.return_value = 1000.0 + 1000.0
        summary = get_alert_summary()
        assert summary["active_failed_login_sources"] == 0
