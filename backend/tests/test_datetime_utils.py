"""
Tests for DateTime Utilities
"""

from datetime import UTC, datetime, timezone

import pytest

from utils.datetime_utils import from_iso, to_utc, utc_now, utc_now_iso


class TestDateTimeUtils:
    """Test suite for datetime utilities"""

    def test_utc_now_returns_aware_datetime(self):
        """Test that utc_now returns timezone-aware datetime"""
        now = utc_now()
        assert isinstance(now, datetime)
        assert now.tzinfo is not None
        assert now.tzinfo == UTC

    def test_utc_now_is_recent(self):
        """Test that utc_now returns current time (within 1 second)"""
        now1 = utc_now()
        now2 = datetime.now(UTC)
        delta = abs((now2 - now1).total_seconds())
        assert delta < 1.0

    def test_utc_now_iso_format(self):
        """Test that utc_now_iso returns valid ISO format"""
        iso_string = utc_now_iso()
        assert isinstance(iso_string, str)
        # Should be parseable
        parsed = datetime.fromisoformat(iso_string)
        assert parsed.tzinfo is not None

    def test_utc_now_iso_contains_timezone(self):
        """Test that ISO string contains timezone info"""
        iso_string = utc_now_iso()
        assert "+00:00" in iso_string or "Z" in iso_string

    def test_to_utc_with_naive_datetime(self):
        """Test converting naive datetime to UTC"""
        naive_dt = datetime(2024, 1, 15, 12, 30, 45)
        utc_dt = to_utc(naive_dt)

        assert utc_dt.tzinfo == UTC
        assert utc_dt.year == 2024
        assert utc_dt.month == 1
        assert utc_dt.day == 15
        assert utc_dt.hour == 12
        assert utc_dt.minute == 30
        assert utc_dt.second == 45

    def test_to_utc_with_utc_datetime(self):
        """Test converting already UTC datetime"""
        utc_dt_in = datetime(2024, 1, 15, 12, 30, 45, tzinfo=UTC)
        utc_dt_out = to_utc(utc_dt_in)

        assert utc_dt_out.tzinfo == UTC
        assert utc_dt_out == utc_dt_in

    def test_to_utc_with_other_timezone(self):
        """Test converting datetime from another timezone to UTC"""
        # Create a datetime in EST (UTC-5)
        from datetime import timedelta

        est = timezone(timedelta(hours=-5))
        est_dt = datetime(2024, 1, 15, 12, 30, 45, tzinfo=est)

        utc_dt = to_utc(est_dt)

        assert utc_dt.tzinfo == UTC
        # 12:30 EST = 17:30 UTC
        assert utc_dt.hour == 17
        assert utc_dt.minute == 30

    def test_from_iso_with_utc_string(self):
        """Test parsing ISO string with +00:00 timezone"""
        iso_string = "2024-01-15T12:30:45+00:00"
        dt = from_iso(iso_string)

        assert dt.tzinfo == UTC
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 12
        assert dt.minute == 30
        assert dt.second == 45

    def test_from_iso_with_z_timezone(self):
        """Test parsing ISO string with Z (Zulu) timezone"""
        iso_string = "2024-01-15T12:30:45Z"
        dt = from_iso(iso_string)

        assert dt.tzinfo == UTC
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 12

    def test_from_iso_with_offset_timezone(self):
        """Test parsing ISO string with timezone offset"""
        iso_string = "2024-01-15T12:30:45+05:30"
        dt = from_iso(iso_string)

        # Should be converted to UTC
        assert dt.tzinfo == UTC
        # 12:30 +05:30 = 07:00 UTC
        assert dt.hour == 7
        assert dt.minute == 0

    def test_from_iso_roundtrip(self):
        """Test that from_iso can parse utc_now_iso output"""
        iso_string = utc_now_iso()
        dt = from_iso(iso_string)

        assert dt.tzinfo == UTC
        # Should be within 1 second of now
        now = utc_now()
        delta = abs((now - dt).total_seconds())
        assert delta < 2.0

    def test_to_utc_preserves_microseconds(self):
        """Test that to_utc preserves microseconds"""
        naive_dt = datetime(2024, 1, 15, 12, 30, 45, 123456)
        utc_dt = to_utc(naive_dt)

        assert utc_dt.microsecond == 123456
