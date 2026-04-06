"""Install/uninstall helper: context menu and TortoiseSVN hooks."""

import sys
import os
import winreg


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVNTS_CMD = "python -m svnts"
PRE_COMMIT_BAT = os.path.join(ROOT_DIR, "scripts", "hooks", "pre-commit-save.bat")
POST_UPDATE_BAT = os.path.join(ROOT_DIR, "scripts", "hooks", "post-update-restore.bat")

REG_TORTOISE = r"Software\TortoiseSVN"
HKCU_CLASSES = r"SOFTWARE\Classes"

# Context menu entries: (key_path, display_name, command)
MENU_ENTRIES = [
    (r"*\shell\SvnTimestampSave", "Save Timestamps to SVN", f'{SVNTS_CMD} save "%1"'),
    (r"*\shell\SvnTimestampRestore", "Restore Timestamps from SVN", f'{SVNTS_CMD} restore "%1"'),
    (r"Directory\shell\SvnTimestampSave", "Save Timestamps to SVN", f'{SVNTS_CMD} save "%1"'),
    (r"Directory\shell\SvnTimestampRestore", "Restore Timestamps from SVN", f'{SVNTS_CMD} restore "%1"'),
]

# TortoiseSVN hook format: each hook block is 6 lines:
#   line 1: hook_type (e.g. "pre_commit_hook", "post_update_hook")
#   line 2: working copy path filter (e.g. "C:\")
#   line 3: command line to execute
#   line 4: "true" = wait for script to finish
#   line 5: "hide" or "show" console
#   line 6: "enforce" or empty
# Blocks are separated by blank lines.
HOOK_TYPE_PRE_COMMIT = "pre_commit_hook"
HOOK_TYPE_POST_UPDATE = "post_update_hook"


def _reg_delete(key_path: str) -> None:
    """Delete a registry key under HKCU\\SOFTWARE\\Classes, ignoring errors."""
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, HKCU_CLASSES + "\\" + key_path)
    except FileNotFoundError:
        pass
    except OSError:
        pass


def _reg_add_sz(key_path: str, value_name: str, value: str) -> None:
    """Add a REG_SZ value under HKCU\\SOFTWARE\\Classes, creating keys as needed."""
    full_path = HKCU_CLASSES + "\\" + key_path
    parts = full_path.split("\\")
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, parts[0])
    for part in parts[1:-1]:
        key = winreg.CreateKey(key, part)
    sub = winreg.CreateKey(key, parts[-1])
    winreg.SetValueEx(sub, value_name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(sub)
    winreg.CloseKey(key)


def install_menu():
    """Install right-click context menu entries."""
    for key_path, display_name, command in MENU_ENTRIES:
        _reg_add_sz(key_path, None, display_name)
        _reg_add_sz(key_path, "command", command)
        _reg_add_sz(key_path, "Icon", "shell32.dll,43")


def uninstall_menu():
    """Remove right-click context menu entries."""
    for key_path, _, _ in MENU_ENTRIES:
        _reg_delete(key_path)


def _read_hooks() -> list[list[str]]:
    """Read TortoiseSVN hooks from registry.

    Returns list of hook blocks, each block is a list of 6 lines.
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_TORTOISE)
        value, _ = winreg.QueryValueEx(key, "hooks")
        winreg.CloseKey(key)
    except FileNotFoundError:
        return []

    if not value or not value.strip():
        return []

    blocks = []
    current_block = []
    for line in value.split("\n"):
        if line.strip() == "":
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)
    return blocks


def _write_hooks(blocks: list[list[str]]) -> None:
    """Write TortoiseSVN hooks to registry."""
    lines = []
    for i, block in enumerate(blocks):
        if i > 0:
            lines.append("")  # blank line between blocks
        lines.extend(block)
    value = "\n".join(lines)

    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_TORTOISE, 0, winreg.KEY_SET_VALUE)
    if value:
        winreg.SetValueEx(key, "hooks", 0, winreg.REG_SZ, value)
    else:
        winreg.DeleteValue(key, "hooks")
    winreg.CloseKey(key)


def _make_hook_block(hook_type: str, command: str) -> list[str]:
    """Create a hook block."""
    return [
        hook_type,
        "C:\\",
        command,
        "true",
        "hide",
        "enforce",
    ]


def _is_our_hook(block: list[str]) -> bool:
    """Check if a hook block belongs to SvnTimestamp."""
    for line in block:
        lower = line.lower()
        if "pre-commit-save.bat" in lower or "post-update-restore.bat" in lower:
            return True
    return False


def install_hooks():
    """Add SvnTimestamp hooks to TortoiseSVN, preserving existing hooks."""
    blocks = _read_hooks()

    # Remove our hooks if already present (idempotent)
    blocks = [b for b in blocks if not _is_our_hook(b)]

    # Add our hooks
    blocks.append(_make_hook_block(HOOK_TYPE_PRE_COMMIT, PRE_COMMIT_BAT))
    blocks.append(_make_hook_block(HOOK_TYPE_POST_UPDATE, POST_UPDATE_BAT))

    _write_hooks(blocks)


def uninstall_hooks():
    """Remove SvnTimestamp hooks from TortoiseSVN, preserving other hooks."""
    blocks = _read_hooks()
    cleaned = [b for b in blocks if not _is_our_hook(b)]
    _write_hooks(cleaned)


def main():
    if len(sys.argv) < 2:
        print("Usage: _install.py <command>")
        print("Commands: install-menu, uninstall-menu, install-hooks, uninstall-hooks")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "install-menu":
        install_menu()
    elif cmd == "uninstall-menu":
        uninstall_menu()
    elif cmd == "install-hooks":
        install_hooks()
    elif cmd == "uninstall-hooks":
        uninstall_hooks()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
