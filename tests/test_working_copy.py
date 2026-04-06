"""Tests for working_copy module."""

import os
import tempfile

from svnts.working_copy import is_in_working_copy, get_working_copy_root


class TestIsInWorkingCopy:
    def test_with_svn_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".svn"))
            assert is_in_working_copy(tmpdir) is True

    def test_without_svn_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_in_working_copy(tmpdir) is False

    def test_nested_in_svn_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".svn"))
            subdir = os.path.join(tmpdir, "src", "project")
            os.makedirs(subdir)
            assert is_in_working_copy(subdir) is True

    def test_file_in_working_copy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".svn"))
            fpath = os.path.join(tmpdir, "test.txt")
            with open(fpath, "w") as f:
                f.write("test")
            assert is_in_working_copy(fpath) is True

    def test_nonexistent_path(self):
        assert is_in_working_copy("C:\\__nonexistent_svnts_test_12345__") is False


class TestGetWorkingCopyRoot:
    def test_returns_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".svn"))
            root = get_working_copy_root(tmpdir)
            assert root == os.path.realpath(tmpdir)

    def test_nested_returns_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".svn"))
            subdir = os.path.join(tmpdir, "a", "b")
            os.makedirs(subdir)
            root = get_working_copy_root(subdir)
            assert root == os.path.realpath(tmpdir)

    def test_not_in_wc_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert get_working_copy_root(tmpdir) is None
