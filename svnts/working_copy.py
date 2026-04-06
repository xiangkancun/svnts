"""SVN working copy detection."""

import os


def is_in_working_copy(path: str) -> bool:
    """Check if path is inside an SVN working copy by looking for .svn directory."""
    path = os.path.realpath(path)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    if not os.path.isdir(path):
        return False
    return _has_svn_dir(path)


def get_working_copy_root(path: str) -> str | None:
    """Get the SVN working copy root directory. Returns None if not in a WC."""
    path = os.path.realpath(path)
    if os.path.isfile(path):
        path = os.path.dirname(path)
    current = path
    while current:
        if os.path.isdir(os.path.join(current, ".svn")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def _has_svn_dir(path: str) -> bool:
    """Walk up directories to find .svn."""
    current = path
    while current:
        if os.path.isdir(os.path.join(current, ".svn")):
            return True
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return False
