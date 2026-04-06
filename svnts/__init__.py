"""SvnTimestamp - Save/Restore file ctime/mtime via SVN properties."""

__version__ = "1.0.0"

# SVN custom property names
CTIME_PROP = "svnts:ctime"
MTIME_PROP = "svnts:mtime"

# ISO 8601 UTC format
ISO8601_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_PARTIAL = 2
