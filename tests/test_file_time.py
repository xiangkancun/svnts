"""Tests for file_time module."""

import os
import tempfile
from datetime import datetime, timezone

from svnts.file_time import to_iso8601, from_iso8601, get_file_times, set_file_times


class TestIso8601:
    def test_round_trip(self):
        original = datetime(2024, 6, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
        iso = to_iso8601(original)
        result = from_iso8601(iso)
        # Millisecond precision (our format uses .%f which is microseconds, but we store 3 digits)
        assert result.year == original.year
        assert result.month == original.month
        assert result.day == original.day
        assert result.hour == original.hour
        assert result.minute == original.minute
        assert result.second == original.second

    def test_utc_format(self):
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        iso = to_iso8601(dt)
        assert iso.endswith("Z")

    def test_parse_valid(self):
        result = from_iso8601("2024-06-15T14:30:45.123Z")
        assert result.year == 2024
        assert result.month == 6
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo == timezone.utc

    def test_local_converts_to_utc(self):
        local = datetime(2024, 1, 1, 8, 0, 0)  # no timezone = local
        iso = to_iso8601(local)
        parsed = from_iso8601(iso)
        assert parsed.tzinfo == timezone.utc


class TestFileTimes:
    def test_get_and_set_round_trip(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        try:
            target_mtime = datetime(2023, 5, 20, 14, 25, 35, tzinfo=timezone.utc)
            set_file_times(path, datetime.now(timezone.utc), target_mtime)

            ctime, mtime = get_file_times(path)
            # mtime should match (ctime may not be settable on all filesystems)
            assert mtime.year == target_mtime.year
            assert mtime.month == target_mtime.month
            assert mtime.day == target_mtime.day
            assert mtime.hour == target_mtime.hour
            assert mtime.minute == target_mtime.minute
            assert mtime.second == target_mtime.second
        finally:
            os.unlink(path)

    def test_nonexistent_file_raises(self):
        try:
            get_file_times("C:\\__nonexistent_svnts_test_12345__")
            assert False, "Should have raised"
        except OSError:
            pass
