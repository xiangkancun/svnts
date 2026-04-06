"""SVN property operations via svn command line."""

import subprocess
import os
import shutil

from svnts import CTIME_PROP, MTIME_PROP

# Find svn executable
SVN_EXE = shutil.which("svn") or "svn"


def get_timestamp_properties(path: str) -> tuple[str | None, str | None]:
    """Get svnts:ctime and svnts:mtime properties from a file.

    Returns (ctime_str, mtime_str). Either may be None if not set.
    """
    ctime = _get_property(path, CTIME_PROP)
    mtime = _get_property(path, MTIME_PROP)
    return ctime, mtime


def set_timestamp_properties(path: str, ctime: str, mtime: str) -> None:
    """Set svnts:ctime and svnts:mtime properties on a file."""
    _set_property(path, CTIME_PROP, ctime)
    _set_property(path, MTIME_PROP, mtime)


def has_timestamp_properties(path: str) -> bool:
    """Check if file has at least one timestamp property."""
    return _get_property(path, CTIME_PROP) is not None or _get_property(path, MTIME_PROP) is not None


def _get_property(path: str, prop_name: str) -> str | None:
    """Get a single SVN property value. Returns None if not set."""
    try:
        result = subprocess.run(
            [SVN_EXE, "propget", prop_name, path],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8"
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _set_property(path: str, prop_name: str, value: str) -> None:
    """Set a single SVN property on a file."""
    result = subprocess.run(
        [SVN_EXE, "propset", prop_name, value, path],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8"
    )
    if result.returncode != 0:
        raise OSError(f"svn propset failed: {result.stderr.strip()}")
