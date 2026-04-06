"""SvnTimestamp CLI entry point."""

import sys
import os

from svnts import EXIT_SUCCESS, EXIT_ERROR, EXIT_PARTIAL
from svnts.manager import TimestampManager


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print_usage()
        return EXIT_ERROR

    cmd = argv[0].lower()
    args = argv[1:]

    try:
        if cmd == "save":
            return handle_save(args)
        elif cmd == "restore":
            return handle_restore(args)
        elif cmd == "hook-save":
            return handle_hook_save(args)
        elif cmd == "hook-restore":
            return handle_hook_restore(args)
        elif cmd in ("--help", "-h", "help"):
            print_usage()
            return EXIT_SUCCESS
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print_usage()
            return EXIT_ERROR
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_save(args):
    """Context menu: save timestamps for given paths."""
    if not args:
        print_usage()
        return EXIT_ERROR

    mgr = TimestampManager(log_fn=lambda m: print(m))
    success, fail = mgr.process_files(args, save=True)
    print(f"Done: {success} saved, {fail} failed.")
    return EXIT_PARTIAL if fail > 0 else EXIT_SUCCESS


def handle_restore(args):
    """Context menu: restore timestamps for given paths."""
    if not args:
        print_usage()
        return EXIT_ERROR

    mgr = TimestampManager(log_fn=lambda m: print(m))
    success, fail = mgr.process_files(args, save=False)
    print(f"Done: {success} restored, {fail} failed.")
    return EXIT_PARTIAL if fail > 0 else EXIT_SUCCESS


def handle_hook_save(args):
    """Pre-commit hook: save timestamps for files being committed.

    TortoiseSVN passes: PATH DEPTH MESSAGEFILE CWD
    PATH = temp file with newline-delimited file list.
    Always returns 0 (never block a commit).
    """
    if not args or not os.path.isfile(args[0]):
        return EXIT_SUCCESS

    paths = [p for p in _read_path_file(args[0]) if p.strip()]
    if not paths:
        return EXIT_SUCCESS

    mgr = TimestampManager(log_fn=lambda m: print(m))
    success, fail = mgr.process_files(paths, save=True)
    print(f"Pre-commit: saved {success} files ({fail} skipped)")
    return EXIT_SUCCESS


def handle_hook_restore(args):
    """Post-update hook: restore timestamps for updated files.

    TortoiseSVN passes: PATH DEPTH REVISION ERROR CWD RESULTPATH
    RESULTPATH (index 5) = temp file with actually updated file list.
    """
    result_file = None
    if len(args) >= 6:
        result_file = args[5]
    elif len(args) >= 1:
        result_file = args[0]

    if not result_file or not os.path.isfile(result_file):
        return EXIT_SUCCESS

    paths = [p for p in _read_path_file(result_file) if p.strip()]
    if not paths:
        return EXIT_SUCCESS

    mgr = TimestampManager(log_fn=lambda m: print(m))
    success, fail = mgr.process_files(paths, save=False)
    print(f"Post-update: restored {success} files ({fail} skipped)")
    return EXIT_SUCCESS


def _read_path_file(path: str) -> list[str]:
    """Read a newline-delimited path file from TortoiseSVN."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except Exception:
        return []


USAGE = """\
SvnTimestamp - Save/Restore file timestamps via SVN properties

Usage:
  svnts save <path> [path2 ...]             Save ctime/mtime as SVN properties
  svnts restore <path> [path2 ...]          Restore ctime/mtime from SVN properties
  svnts hook-save <PATH> <DEPTH> <MSG> <CWD>            Pre-commit hook
  svnts hook-restore <PATH> <DEPTH> <REV> <ERR> <CWD> <RESULT>  Post-update hook
  svnts --help                               Show this help

Hook configuration (TortoiseSVN Settings > Hook Scripts):
  Pre-commit:  svnts hook-save %1 %2 %3 %4
  Post-update: svnts hook-restore %1 %2 %3 %4 %5 %6"""


def print_usage():
    print(USAGE)


if __name__ == "__main__":
    sys.exit(main())
