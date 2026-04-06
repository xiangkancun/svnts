"""SvnTimestamp - Save/Restore file ctime/mtime via SVN properties."""

import ctypes
import ctypes.wintypes
import os
import shutil
import sqlite3
import sys
import winreg
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CTIME_PROP = "svnts:ctime"
MTIME_PROP = "svnts:mtime"
TIMESTAMP_FMT = "%Y-%m-%d %H:%M:%S %z"
HOOKS_REG = r"Software\TortoiseSVN"

# Install dir: %USERPROFILE%\svnts\
INSTALL_DIR = os.path.join(os.path.expanduser("~"), "svnts")

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


def to_timestamp_str(dt):
    return dt.astimezone().strftime(TIMESTAMP_FMT)


def from_timestamp_str(s):
    return datetime.strptime(s, TIMESTAMP_FMT).astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# SVN property serialization format (SVN hash)
# Format: "K <len>\n<key>\nV <len>\n<val>\n" ... "END\n"
# ---------------------------------------------------------------------------
def _parse_svn_hash(data):
    """Parse SVN property hash bytes -> dict."""
    if not data:
        return {}
    props = {}
    blob = data if isinstance(data, bytes) else data.encode("utf-8")
    pos = 0
    while pos < len(blob):
        if blob[pos:pos + 2] == b"K ":
            pos += 2
            nl = blob.index(b"\n", pos)
            klen = int(blob[pos:nl])
            pos = nl + 1
            key = blob[pos:pos + klen].decode("utf-8")
            pos += klen + 1
            if blob[pos:pos + 2] != b"V ":
                break
            pos += 2
            nl = blob.index(b"\n", pos)
            vlen = int(blob[pos:nl])
            pos = nl + 1
            val = blob[pos:pos + vlen].decode("utf-8")
            pos += vlen + 1
            props[key] = val
        elif blob[pos:pos + 3] == b"END":
            break
        else:
            pos += 1
    return props


def _serialize_svn_hash(props):
    """Serialize dict -> SVN property hash bytes."""
    buf = bytearray()
    for k, v in props.items():
        kb = k.encode("utf-8")
        vb = v.encode("utf-8")
        buf.extend(f"K {len(kb)}\n".encode())
        buf.extend(kb)
        buf.extend(b"\n")
        buf.extend(f"V {len(vb)}\n".encode())
        buf.extend(vb)
        buf.extend(b"\n")
    buf.extend(b"END\n")
    return bytes(buf)


# ---------------------------------------------------------------------------
# SVN working copy detection + wc.db access
# ---------------------------------------------------------------------------
_wc_root_cache = {}


def find_wc_root(path):
    """Find SVN working copy root for path, with caching."""
    d = os.path.realpath(path)
    if os.path.isfile(d):
        d = os.path.dirname(d)
    best = None
    for cached_dir, cached_root in _wc_root_cache.items():
        if d.lower().startswith(cached_dir.lower()):
            if best is None or len(cached_dir) > len(best[0]):
                best = (cached_dir, cached_root)
    if best:
        return best[1]
    original = d
    while d:
        if os.path.isdir(os.path.join(d, ".svn")):
            _wc_root_cache[original] = d
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def is_in_wc(path):
    return find_wc_root(path) is not None


def _wc_db_path(file_path):
    """Return (db_path, wc_root) for a file, or (None, None)."""
    wc_root = find_wc_root(file_path)
    if not wc_root:
        return None, None
    db = os.path.join(wc_root, ".svn", "wc.db")
    if os.path.isfile(db):
        return db, wc_root
    return None, None


def _relpath(file_path, wc_root):
    """Relative path from WC root, using forward slashes (SVN convention)."""
    return os.path.relpath(file_path, wc_root).replace("\\", "/")


# ---------------------------------------------------------------------------
# SVN property read/write via wc.db (zero subprocess, zero Defender impact)
# ---------------------------------------------------------------------------
def _db_propget(file_path, prop_name):
    """Read a single property from wc.db. Returns value or None."""
    db_path, wc_root = _wc_db_path(file_path)
    if not db_path:
        return None
    rp = _relpath(file_path, wc_root)
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        cur = conn.execute(
            "SELECT properties FROM nodes "
            "WHERE local_relpath = ? ORDER BY op_depth DESC LIMIT 1",
            (rp,))
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return _parse_svn_hash(row[0]).get(prop_name)
    except Exception:
        pass
    return None


def _db_propset(file_path, prop_name, prop_value):
    """Write a property to wc.db. Creates working layer if needed."""
    db_path, wc_root = _wc_db_path(file_path)
    if not db_path:
        raise OSError("Not in SVN working copy")
    rp = _relpath(file_path, wc_root)
    conn = sqlite3.connect(db_path, timeout=5)

    # Find existing working layer (op_depth > 0)
    working = conn.execute(
        "SELECT op_depth, properties FROM nodes "
        "WHERE local_relpath = ? AND op_depth > 0 "
        "ORDER BY op_depth DESC LIMIT 1",
        (rp,)).fetchone()

    if working:
        op_depth, prop_blob = working
        props = _parse_svn_hash(prop_blob) if prop_blob else {}
        props[prop_name] = prop_value
        conn.execute(
            "UPDATE nodes SET properties = ? "
            "WHERE local_relpath = ? AND op_depth = ?",
            (_serialize_svn_hash(props), rp, op_depth))
    else:
        # No working layer — copy base row to op_depth=1 with modified props
        base = conn.execute(
            "SELECT properties FROM nodes "
            "WHERE local_relpath = ? AND op_depth = 0",
            (rp,)).fetchone()
        if not base:
            conn.close()
            raise OSError(f"Not in WC DB: {rp}")
        props = _parse_svn_hash(base[0]) if base[0] else {}
        props[prop_name] = prop_value
        conn.execute(
            "INSERT INTO nodes "
            "(wc_id, local_relpath, parent_relpath, name, kind, "
            "presence, checksum, op_depth, properties) "
            "SELECT wc_id, local_relpath, parent_relpath, name, kind, "
            "presence, checksum, 1, ? "
            "FROM nodes WHERE local_relpath = ? AND op_depth = 0",
            (_serialize_svn_hash(props), rp))

    conn.commit()
    conn.close()


def _db_propget_batch(file_paths, prop_name):
    """Batch read a property for multiple files. Returns {path: value}.

    Groups files by WC root, one SQL query per WC.
    """
    result = {}
    by_wc = {}
    for fp in file_paths:
        db_path, wc_root = _wc_db_path(fp)
        if not db_path:
            continue
        rp = _relpath(fp, wc_root)
        by_wc.setdefault((db_path, wc_root), []).append((rp, fp))

    for (db_path, wc_root), entries in by_wc.items():
        relpaths = [e[0] for e in entries]
        rp_map = {e[0]: e[1] for e in entries}
        placeholders = ",".join("?" * len(relpaths))
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            cur = conn.execute(
                f"SELECT local_relpath, properties FROM nodes "
                f"WHERE local_relpath IN ({placeholders}) "
                f"ORDER BY local_relpath, op_depth DESC",
                relpaths)
            seen = set()
            for row in cur.fetchall():
                rp, prop_blob = row
                if rp in seen:
                    continue
                seen.add(rp)
                if prop_blob:
                    val = _parse_svn_hash(prop_blob).get(prop_name)
                    if val:
                        result[rp_map[rp]] = val
            conn.close()
        except Exception:
            pass
    return result


# ---------------------------------------------------------------------------
# Save / Restore
# ---------------------------------------------------------------------------
def save_timestamps(path):
    """Save file ctime/mtime as SVN properties via wc.db."""
    if not os.path.isfile(path):
        return False
    if not is_in_wc(path):
        return False
    try:
        ct, mt = get_file_times(path)
        _db_propset(path, CTIME_PROP, to_timestamp_str(ct))
        _db_propset(path, MTIME_PROP, to_timestamp_str(mt))
        return True
    except Exception:
        return False


def _restore_file(path, ct_s, mt_s):
    """Restore a single file from already-fetched property values."""
    if not ct_s and not mt_s:
        return None  # no props, skip silently
    try:
        ct = from_timestamp_str(ct_s) if ct_s else datetime.now(timezone.utc)
        mt = from_timestamp_str(mt_s) if mt_s else datetime.now(timezone.utc)
        set_file_times(path, ct, mt)
        return True
    except Exception:
        return False


def _collect_files(paths):
    """Collect all file paths from given paths/directories."""
    files = []
    for p in paths:
        p = p.strip()
        if not p:
            continue
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, dirs, filenames in os.walk(p):
                dirs[:] = [d for d in dirs if d != ".svn"]
                for f in filenames:
                    files.append(os.path.join(root, f))
    return files


def _progress_bar(current, total, width=30):
    pct = current / total if total else 0
    filled = int(width * pct)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    print(f"\r  [{bar}] {current}/{total}", end="", flush=True)


def process_paths(paths, save, log=None):
    """Process files/directories. Returns (ok, fail).

    All operations go through wc.db (SQLite) — zero subprocess, zero Defender.
    """
    files = _collect_files(paths)
    if not files:
        return 0, 0
    files = [f for f in files if is_in_wc(f)]
    if not files:
        return 0, 0
    total = len(files)

    if save:
        ok = fail = 0
        for i, f in enumerate(files):
            if save_timestamps(f):
                ok += 1
            else:
                fail += 1
            if log:
                _progress_bar(i + 1, total)
    else:
        if log:
            print("  Reading properties...", flush=True)
        ct_map = _db_propget_batch(files, CTIME_PROP)
        mt_map = _db_propget_batch(files, MTIME_PROP)
        ok = fail = skip = 0
        for i, f in enumerate(files):
            s = _restore_file(f, ct_map.get(f), mt_map.get(f))
            if s is None:
                skip += 1
            else:
                ok += s
                fail += not s
            if log:
                _progress_bar(i + 1, total)

    if log:
        print()
        action = "saved" if save else "restored"
        msg = f"Done: {ok} {action}"
        if fail:
            msg += f", {fail} failed"
        if not save and skip:
            msg += f", {skip} skipped (no props)"
        print(f"  {msg}")
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
    return 1 if fail else 0


def cmd_restore(args):
    if not args:
        print("Usage: svnts.py restore <path> [path2 ...]"); return 1
    ok, fail = process_paths(args, False, log=print)
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
# TortoiseSVN hooks (registry)
# ---------------------------------------------------------------------------
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
    return INSTALL_DIR.lower() in " ".join(block).lower()


def _get_local_drives():
    """Get all local fixed drives (C:, D:, Z:, etc.)."""
    drives = set()
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        path = letter + ":\\"
        if os.path.isdir(path):
            drives.add(path)
    return sorted(drives)


# ---------------------------------------------------------------------------
# Context menu (registry)
# ---------------------------------------------------------------------------
_CONTEXT_PREFIXES = [
    r"Software\Classes\*\shell",
    r"Software\Classes\Directory\shell",
    r"Software\Classes\Directory\Background\shell",
]


def _add_context_menu(name, display_text, command, icon_path=None,
                      bg_command=None):
    """Register context menu. bg_command is used for Directory\\Background."""
    for prefix in _CONTEXT_PREFIXES:
        is_bg = "Background" in prefix
        cmd = bg_command if is_bg and bg_command else command
        key = winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, f"{prefix}\\{name}", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, display_text)
        if icon_path and os.path.isfile(icon_path):
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{icon_path}",0')
        winreg.CloseKey(key)
        cmd_key = winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            f"{prefix}\\{name}\\command", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(cmd_key, None, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(cmd_key)


def _del_context_menu(name):
    advapi32 = ctypes.windll.advapi32
    advapi32.RegDeleteTreeW.argtypes = [ctypes.wintypes.HKEY, ctypes.c_wchar_p]
    advapi32.RegDeleteTreeW.restype = ctypes.c_long
    for prefix in _CONTEXT_PREFIXES:
        path = f"{prefix}\\{name}"
        advapi32.RegDeleteTreeW(winreg.HKEY_CURRENT_USER, path)


# ---------------------------------------------------------------------------
# Install / Uninstall
# ---------------------------------------------------------------------------
def cmd_install(_args):
    """Copy files to %USERPROFILE%\\svnts and register everything."""
    hooks_dir = os.path.join(INSTALL_DIR, "hooks")
    src_dir = os.path.dirname(os.path.abspath(__file__))
    pre_commit_src = os.path.join(src_dir, "scripts", "hooks", "pre-commit-save.bat")
    post_update_src = os.path.join(src_dir, "scripts", "hooks", "post-update-restore.bat")
    pre_commit_dst = os.path.join(hooks_dir, "pre-commit-save.bat")
    post_update_dst = os.path.join(hooks_dir, "post-update-restore.bat")

    # Copy files
    print(f"[1/3] Copying files to {INSTALL_DIR}...")
    os.makedirs(hooks_dir, exist_ok=True)
    shutil.copy2(__file__, INSTALL_DIR)
    shutil.copy2(pre_commit_src, pre_commit_dst)
    shutil.copy2(post_update_src, post_update_dst)
    print("       Done.")

    # Context menu
    print("[2/3] Registering context menu...")
    exe = sys.executable
    script = os.path.join(INSTALL_DIR, "svnts.py")
    tsvn_icon = r"C:\Program Files\TortoiseSVN\bin\TortoiseProc.exe"
    _add_context_menu(
        "SvnTimestampsSave", "SVN: 保存时间戳 (ctime/mtime)",
        f'"{exe}" "{script}" save "%1"', tsvn_icon,
        bg_command=f'"{exe}" "{script}" save "%V"')
    _add_context_menu(
        "SvnTimestampsRestore", "SVN: 恢复时间戳 (ctime/mtime)",
        f'"{exe}" "{script}" restore "%1"', tsvn_icon,
        bg_command=f'"{exe}" "{script}" restore "%V"')
    print("       Done.")

    # TortoiseSVN hooks
    print("[3/3] Registering TortoiseSVN hooks...")
    blocks = _read_hooks()
    blocks = [b for b in blocks if not _is_our_hook(b)]

    drives = _get_local_drives()
    print(f"       Drives: {', '.join(drives)}")
    for drive in drives:
        blocks.append(_make_hook_block("pre_commit_hook", drive, pre_commit_dst))
        blocks.append(_make_hook_block("post_update_hook", drive, post_update_dst))

    _write_hooks(blocks)
    print("       Done.")
    print(f"\nInstallation complete. Files in {INSTALL_DIR}")
    return 0


def cmd_uninstall(_args):
    """Remove context menu, TortoiseSVN hooks, and installed files."""
    print("[1/3] Removing context menu...")
    _del_context_menu("SvnTimestampsSave")
    _del_context_menu("SvnTimestampsRestore")
    print("       Done.")

    print("[2/3] Removing TortoiseSVN hooks...")
    blocks = _read_hooks()
    blocks = [b for b in blocks if not _is_our_hook(b)]
    _write_hooks(blocks)
    print("       Done.")

    print(f"[3/3] Removing {INSTALL_DIR}...")
    if os.path.isdir(INSTALL_DIR):
        shutil.rmtree(INSTALL_DIR)
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
