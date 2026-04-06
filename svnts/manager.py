"""Timestamp save/restore orchestration."""

import os
from dataclasses import dataclass

from svnts.file_time import get_file_times, set_file_times, to_iso8601, from_iso8601
from svnts.svn_helper import get_timestamp_properties, set_timestamp_properties
from svnts.working_copy import is_in_working_copy


@dataclass
class TimestampResult:
    path: str
    success: bool
    error: str | None = None

    @staticmethod
    def ok(path: str) -> "TimestampResult":
        return TimestampResult(path=path, success=True)

    @staticmethod
    def fail(path: str, error: str) -> "TimestampResult":
        return TimestampResult(path=path, success=False, error=error)


class TimestampManager:
    """Orchestrates timestamp save/restore operations."""

    def __init__(self, log_fn=None):
        self._log = log_fn or (lambda msg: None)

    def save(self, path: str) -> TimestampResult:
        """Save file ctime/mtime as SVN properties."""
        if not os.path.isfile(path):
            return TimestampResult.fail(path, "File does not exist")

        if not is_in_working_copy(path):
            return TimestampResult.fail(path, "Not in SVN working copy")

        try:
            ctime, mtime = get_file_times(path)
            ctime_str = to_iso8601(ctime)
            mtime_str = to_iso8601(mtime)
            set_timestamp_properties(path, ctime_str, mtime_str)
            self._log(f"Saved: {path} (ctime={ctime_str}, mtime={mtime_str})")
            return TimestampResult.ok(path)
        except PermissionError as e:
            return TimestampResult.fail(path, f"Permission denied: {e}")
        except Exception as e:
            return TimestampResult.fail(path, f"Error: {e}")

    def restore(self, path: str) -> TimestampResult:
        """Restore file ctime/mtime from SVN properties."""
        if not os.path.isfile(path):
            return TimestampResult.fail(path, "File does not exist")

        ctime_str, mtime_str = get_timestamp_properties(path)
        if ctime_str is None and mtime_str is None:
            return TimestampResult.fail(path, "No timestamp properties found")

        try:
            from datetime import datetime, timezone
            ctime = from_iso8601(ctime_str) if ctime_str else datetime.now(timezone.utc)
            mtime = from_iso8601(mtime_str) if mtime_str else datetime.now(timezone.utc)
            set_file_times(path, ctime, mtime)
            self._log(f"Restored: {path} (ctime={ctime_str}, mtime={mtime_str})")
            return TimestampResult.ok(path)
        except PermissionError as e:
            return TimestampResult.fail(path, f"Permission denied: {e}")
        except Exception as e:
            return TimestampResult.fail(path, f"Error: {e}")

    def process_files(self, paths: list[str], save: bool) -> tuple[int, int]:
        """Process a list of file/directory paths.

        Returns (success_count, fail_count).
        """
        success = 0
        fail = 0
        for path in paths:
            path = path.strip()
            if not path:
                continue

            if os.path.isfile(path):
                result = self.save(path) if save else self.restore(path)
                if result.success:
                    success += 1
                else:
                    fail += 1
            elif os.path.isdir(path):
                s, f = self._process_directory(path, save)
                success += s
                fail += f
            else:
                self._log(f"Skipped (not found): {path}")
                fail += 1
        return success, fail

    def _process_directory(self, dir_path: str, save: bool) -> tuple[int, int]:
        """Recursively process all files in a directory, skipping .svn dirs."""
        success = 0
        fail = 0
        for root, dirs, files in os.walk(dir_path):
            # Skip .svn directories
            dirs[:] = [d for d in dirs if d != ".svn"]
            for fname in files:
                fpath = os.path.join(root, fname)
                result = self.save(fpath) if save else self.restore(fpath)
                if result.success:
                    success += 1
                else:
                    fail += 1
        return success, fail
