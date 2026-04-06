"""Tests for manager module."""

import os
import tempfile

from svnts.manager import TimestampManager, TimestampResult


class TestTimestampManager:
    def test_save_nonexistent_file(self):
        mgr = TimestampManager()
        result = mgr.save("C:\\__nonexistent_svnts_test_12345__")
        assert result.success is False
        assert "does not exist" in result.error

    def test_restore_nonexistent_file(self):
        mgr = TimestampManager()
        result = mgr.restore("C:\\__nonexistent_svnts_test_12345__")
        assert result.success is False
        assert "does not exist" in result.error

    def test_save_not_in_working_copy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = os.path.join(tmpdir, "test.txt")
            with open(fpath, "w") as f:
                f.write("test")
            mgr = TimestampManager()
            result = mgr.save(fpath)
            assert result.success is False
            assert "Not in SVN working copy" in result.error

    def test_process_files_empty(self):
        mgr = TimestampManager()
        success, fail = mgr.process_files([], save=True)
        assert success == 0
        assert fail == 0

    def test_process_files_nonexistent(self):
        mgr = TimestampManager(log_fn=lambda m: None)
        success, fail = mgr.process_files(["C:\\__nonexistent_svnts_test_12345__"], save=True)
        assert success == 0
        assert fail == 1

    def test_process_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".svn"))
            os.makedirs(os.path.join(tmpdir, "src"))
            with open(os.path.join(tmpdir, "src", "a.txt"), "w") as f:
                f.write("a")
            with open(os.path.join(tmpdir, "src", "b.txt"), "w") as f:
                f.write("b")
            # Files are in a WC but not versioned, so save will succeed
            # (svn propset will fail, caught as error)
            mgr = TimestampManager(log_fn=lambda m: None)
            success, fail = mgr.process_files([os.path.join(tmpdir, "src")], save=True)
            # Should process 2 files (both fail because not versioned)
            assert fail == 2
