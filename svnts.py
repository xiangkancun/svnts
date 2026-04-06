"""SvnTimestamp - Save/Restore file ctime/mtime via SVN properties."""

import ctypes
import ctypes.wintypes
import os
import re
import subprocess
import sys
import winreg
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CTIME_PROP = "svnts:ctime"
MTIME_PROP = "svnts:mtime"
ISO8601_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
SVN_EXE = "svn"
HOOKS_REG = r"Software\TortoiseSVN"
HKCU_CLASSES = r"SOFTWARE\Classes"

# ---------------------------------------------------------------------------
# File time operations (Win32 API)
# ---------------------------------------------------------------------------
kernel32 = ctypes.windll.kernel32


def get_file_times(path):
    """Return (ctime, mtime) as UTC datetime via Win32 GetFileTime."""
    handle = kernel32.CreateFileW(
        path, 0x80000000, 0x00000003, None, 3, 0, None)
    if handle == -1 or handle == ctypes.wintypes.HANDLE(-1).value:
        raise OSError(f"Cannot open: {path}")
    creation = ctypes.wintypes.FILETIME()
    access = ctypes.wintypes.FILETIME()
    write = ctypes.wintypes.FILETIME()
    kernel32.GetFileTime(handle, ctypes.byref(creation),
                         ctypes.byref(access), ctypes.byref(write))
    kernel32.CloseHandle(handle)
    return _ft_to_dt(creation), _ft_to_dt(write)


def set_file_times(path, ctime, mtime):
    """Set file ctime and mtime via Win32 SetFileTime."""
    handle = kernel32.CreateFileW(
        path, 0x40000000, 0x00000003, None, 3, 0, None)
    if handle == -1 or handle == ctypes.wintypes.HANDLE(-1).value:
        raise OSError(f"Cannot open: {path}")
    c = _dt_to_ft(ctime)
    a = _dt_to_ft(datetime.now(timezone.utc))
    m = _dt_to_ft(mtime)
    kernel32.SetFileTime(handle, ctypes.byref(c), ctypes.byref(a), ctypes.byref(m))
    kernel32.CloseHandle(handle)


def _ft_to_dt(ft):
    """FILETIME -> UTC datetime."""
    v = ft.dwLowDateTime | (ft.dwHighDateTime << 32)
    us = (v - 116444736000000000) // 10
    return datetime(1970, 1, 1, tzinfo=timezone.utc) + __import__(
        "datetime").timedelta(microseconds=us)


def _dt_to_ft(dt):
    """UTC datetime -> FILETIME."""
    dt = dt.astimezone(timezone.utc)
    delta = dt - datetime(1970, 1, 1, tzinfo=timezone.utc)
    v = int(delta.total_seconds() * 10000000) + 116444736000000000
    ft = ctypes.wintypes.FILETIME()
    ft.dwLowDateTime = v & 0xFFFFFFFF
    ft.dwHighDateTime = v >> 32
    return ft


def to_iso8601(dt):
    return dt.astimezone(timezone.utc).strftime(ISO8601_FMT)


def from_iso8601(s):
    return datetime.strptime(s, ISO8601_FMT).replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# SVN property operations
# ---------------------------------------------------------------------------
def _svn_propget(path, prop):
    try:
        r = subprocess.run(
            [SVN_EXE, "propget", prop, path],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None


def _svn_propset(path, prop, value):
    r = subprocess.run(
        [SVN_EXE, "propset", prop, value, path],
        capture_output=True, text=True, timeout=30,
        encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise OSError(f"svn propset failed: {r.stderr.strip()}")


# ---------------------------------------------------------------------------
# Working copy detection
# ---------------------------------------------------------------------------
def is_in_wc(path):
    d = os.path.realpath(path)
    if os.path.isfile(d):
        d = os.path.dirname(d)
    while d:
        if os.path.isdir(os.path.join(d, ".svn")):
            return True
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return False


# ---------------------------------------------------------------------------
# Save / Restore
# ---------------------------------------------------------------------------
def save_timestamps(path, log=None):
    """Save file ctime/mtime as SVN properties."""
    if not os.path.isfile(path):
        return False, "File does not exist"
    if not is_in_wc(path):
        return False, "Not in SVN working copy"
    try:
        ct, mt = get_file_times(path)
        _svn_propset(path, CTIME_PROP, to_iso8601(ct))
        _svn_propset(path, MTIME_PROP, to_iso8601(mt))
        if log:
            log(f"Saved: {path}")
        return True, None
    except Exception as e:
        return False, str(e)


def restore_timestamps(path, log=None):
    """Restore file ctime/mtime from SVN properties."""
    if not os.path.isfile(path):
        return False, "File does not exist"
    ct_s = _svn_propget(path, CTIME_PROP)
    mt_s = _svn_propget(path, MTIME_PROP)
    if not ct_s and not mt_s:
        return False, "No timestamp properties found"
    try:
        ct = from_iso8601(ct_s) if ct_s else datetime.now(timezone.utc)
        mt = from_iso8601(mt_s) if mt_s else datetime.now(timezone.utc)
        set_file_times(path, ct, mt)
        if log:
            log(f"Restored: {path}")
        return True, None
    except Exception as e:
        return False, str(e)


def process_paths(paths, save, log=None):
    """Process files/directories. Returns (ok, fail)."""
    ok = fail = 0
    for p in paths:
        p = p.strip()
        if not p:
            continue
        if os.path.isfile(p):
            s, _ = (save_timestamps if save else restore_timestamps)(p, log)
            ok += s
            fail += not s
        elif os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d != ".svn"]
                for f in files:
                    fp = os.path.join(root, f)
                    s, _ = (save_timestamps if save else restore_timestamps)(fp, log)
                    ok += s
                    fail += not s
        else:
            fail += 1
    return ok, fail


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------
def _read_path_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [l for l in f.read().splitlines() if l.strip()]
    except Exception:
        return []


def cmd_save(args):
    if not args:
        print("Usage: svnts.py save <path> [path2 ...]"); return 1
    ok, fail = process_paths(args, True, log=print)
    print(f"Done: {ok} saved, {fail} failed.")
    return 1 if fail else 0


def cmd_restore(args):
    if not args:
        print("Usage: svnts.py restore <path> [path2 ...]"); return 1
    ok, fail = process_paths(args, False, log=print)
    print(f"Done: {ok} restored, {fail} failed.")
    return 1 if fail else 0


def cmd_hook_save(args):
    if not args or not os.path.isfile(args[0]):
        return 0
    paths = _read_path_file(args[0])
    if not paths:
        return 0
    ok, _ = process_paths(paths, True, log=print)
    print(f"Pre-commit: saved {ok} files")
    return 0  # never block commit


def cmd_hook_restore(args):
    result_file = args[5] if len(args) >= 6 else (args[0] if args else None)
    if not result_file or not os.path.isfile(result_file):
        return 0
    paths = _read_path_file(result_file)
    if not paths:
        return 0
    ok, _ = process_paths(paths, False, log=print)
    print(f"Post-update: restored {ok} files")
    return 0


# ---------------------------------------------------------------------------
# Registry: context menu + TortoiseSVN hooks
# ---------------------------------------------------------------------------
def _reg_add(key_path, value_name, value):
    full = HKCU_CLASSES + "\\" + key_path
    parts = full.split("\\")
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, parts[0])
    for p in parts[1:-1]:
        key = winreg.CreateKey(key, p)
    sub = winreg.CreateKey(key, parts[-1])
    winreg.SetValueEx(sub, value_name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(sub)
    winreg.CloseKey(key)


def _reg_del(key_path):
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,
                         HKCU_CLASSES + "\\" + key_path)
    except (FileNotFoundError, OSError):
        pass


MENU_ITEMS = [
    (r"*\shell\SvnTimestampSave", "Save Timestamps to SVN",
     f'python "{__file__}" save "%1"'),
    (r"*\shell\SvnTimestampRestore", "Restore Timestamps from SVN",
     f'python "{__file__}" restore "%1"'),
    (r"Directory\shell\SvnTimestampSave", "Save Timestamps to SVN",
     f'python "{__file__}" save "%1"'),
    (r"Directory\shell\SvnTimestampRestore", "Restore Timestamps from SVN",
     f'python "{__file__}" restore "%1"'),
]


def _make_hook_block(hook_type, path, command):
    return [hook_type, path, command, "true", "hide", "enforce"]


def _read_hooks():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, HOOKS_REG)
        val, _ = winreg.QueryValueEx(key, "hooks")
        winreg.CloseKey(key)
    except FileNotFoundError:
        return []
    if not val or not val.strip():
        return []
    lines = [l for l in val.split("\n") if l.strip()]
    return [lines[i:i + 6] for i in range(0, len(lines), 6)]


def _write_hooks(blocks):
    all_lines = []
    for b in blocks:
        all_lines.extend(b)
    val = "\n".join(all_lines)
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, HOOKS_REG, 0, winreg.KEY_SET_VALUE)
    if val:
        winreg.SetValueEx(key, "hooks", 0, winreg.REG_SZ, val)
    else:
        try:
            winreg.DeleteValue(key, "hooks")
        except FileNotFoundError:
            pass
    winreg.CloseKey(key)


def _is_our_hook(block):
    marker = os.path.basename(__file__)
    return any(marker in l.lower() for l in block)


def _get_local_drives():
    """Get all local fixed drives (C:, D:, Z:, etc.)."""
    drives = set()
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        path = letter + ":\\"
        if os.path.isdir(path):
            drives.add(path)
    return sorted(drives)


def cmd_install(_args):
    """Register context menu + TortoiseSVN hooks for all drives."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pre_commit = os.path.join(script_dir, "scripts", "hooks", "pre-commit-save.bat")
    post_update = os.path.join(script_dir, "scripts", "hooks", "post-update-restore.bat")

    # Context menu
    print("[1/2] Registering context menu...")
    for key_path, name, cmd in MENU_ITEMS:
        _reg_add(key_path, None, name)
        _reg_add(key_path, "command", cmd)
        _reg_add(key_path, "Icon", "shell32.dll,43")
    print("       Done.")

    # TortoiseSVN hooks — one block per drive
    print("[2/2] Registering TortoiseSVN hooks...")
    blocks = _read_hooks()
    blocks = [b for b in blocks if not _is_our_hook(b)]

    drives = _get_local_drives()
    print(f"       Drives: {', '.join(drives)}")
    for drive in drives:
        blocks.append(_make_hook_block("pre_commit_hook", drive, pre_commit))
        blocks.append(_make_hook_block("post_update_hook", drive, post_update))

    _write_hooks(blocks)
    print("       Done.")
    print("\nInstallation complete.")
    return 0


def cmd_uninstall(_args):
    """Remove all context menu entries and TortoiseSVN hooks."""
    print("[1/2] Removing context menu...")
    for key_path, _, _ in MENU_ITEMS:
        _reg_del(key_path)
    print("       Done.")

    print("[2/2] Removing TortoiseSVN hooks...")
    blocks = _read_hooks()
    blocks = [b for b in blocks if not _is_our_hook(b)]
    _write_hooks(blocks)
    print("       Done.")
    print("\nUninstallation complete.")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: svnts.py <save|restore|hook-save|hook-restore|install|uninstall>")
        return 1
    return {
        "save": cmd_save,
        "restore": cmd_restore,
        "hook-save": cmd_hook_save,
        "hook-restore": cmd_hook_restore,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
    }.get(sys.argv[1].lower(), lambda a: (print(f"Unknown: {sys.argv[1]}"), 1)[1])(sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
