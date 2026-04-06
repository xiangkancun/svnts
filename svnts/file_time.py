"""File time operations using Windows API via ctypes."""

import ctypes
import ctypes.wintypes
from datetime import datetime, timezone

from svnts import ISO8601_FMT

kernel32 = ctypes.windll.kernel32

FILETIME = ctypes.wintypes.FILETIME


def get_file_times(path: str) -> tuple[datetime, datetime]:
    """Read file creation time and modification time via Win32 API.

    Returns (ctime, mtime) as UTC datetime objects.
    """
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3

    handle = kernel32.CreateFileW(
        path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
        None, OPEN_EXISTING, 0, None
    )
    if handle == -1 or handle == ctypes.wintypes.HANDLE(-1).value:
        raise OSError(f"Cannot open file: {path}")

    creation = FILETIME()
    access = FILETIME()
    write = FILETIME()

    ok = kernel32.GetFileTime(handle, ctypes.byref(creation), ctypes.byref(access), ctypes.byref(write))
    kernel32.CloseHandle(handle)
    if not ok:
        raise OSError(f"GetFileTime failed for: {path}")

    return _filetime_to_dt(creation), _filetime_to_dt(write)


def set_file_times(path: str, ctime: datetime, mtime: datetime) -> None:
    """Set file creation time and modification time via Win32 API.

    Input datetime objects should be UTC.
    """
    GENERIC_WRITE = 0x40000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3

    handle = kernel32.CreateFileW(
        path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
        None, OPEN_EXISTING, 0, None
    )
    if handle == -1 or handle == ctypes.wintypes.HANDLE(-1).value:
        raise OSError(f"Cannot open file: {path}")

    c_ft = _dt_to_filetime(ctime)
    a_ft = _dt_to_filetime(datetime.now(timezone.utc))
    m_ft = _dt_to_filetime(mtime)

    ok = kernel32.SetFileTime(handle, ctypes.byref(c_ft), ctypes.byref(a_ft), ctypes.byref(m_ft))
    kernel32.CloseHandle(handle)
    if not ok:
        raise OSError(f"SetFileTime failed for: {path}")


def to_iso8601(dt: datetime) -> str:
    """Convert datetime to ISO 8601 UTC string."""
    return dt.astimezone(timezone.utc).strftime(ISO8601_FMT)


def from_iso8601(s: str) -> datetime:
    """Parse ISO 8601 UTC string to datetime."""
    return datetime.strptime(s, ISO8601_FMT).replace(tzinfo=timezone.utc)


def _filetime_to_dt(ft: FILETIME) -> datetime:
    """Convert Win32 FILETIME to UTC datetime."""
    value = ft.dwLowDateTime | (ft.dwHighDateTime << 32)
    # FILETIME: 100-nanosecond intervals since 1601-01-01
    # Python timestamp: seconds since 1970-01-01
    EPOCH_DIFF = 116444736000000000  # 100ns intervals between 1601 and 1970
    microseconds = (value - EPOCH_DIFF) // 10
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + __import__("datetime").timedelta(microseconds=microseconds)


def _dt_to_filetime(dt: datetime) -> FILETIME:
    """Convert UTC datetime to Win32 FILETIME."""
    dt = dt.astimezone(timezone.utc)
    EPOCH_DIFF = 116444736000000000
    # Total microseconds since 1970-01-01
    delta = dt - datetime(1970, 1, 1, tzinfo=timezone.utc)
    value = int(delta.total_seconds() * 10000000) + EPOCH_DIFF
    ft = FILETIME()
    ft.dwLowDateTime = value & 0xFFFFFFFF
    ft.dwHighDateTime = value >> 32
    return ft
