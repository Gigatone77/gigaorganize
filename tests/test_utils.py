import os
import tempfile
import unittest
from pathlib import Path

from gigaorganize.utils.file_utils import (
    bin_path,
    move_to_recoverable_bin,
)
from gigaorganize.utils.format import format_size, truncate


class TestFormatSize(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(format_size(0), "0 B")
        self.assertEqual(format_size(512), "512 B")

    def test_kib(self):
        self.assertEqual(format_size(1024), "1.0 KiB")

    def test_mib(self):
        self.assertEqual(format_size(1024 * 1024), "1.0 MiB")

    def test_gib(self):
        self.assertEqual(format_size(1536 * 1024 * 1024), "1.5 GiB")

    def test_negative(self):
        self.assertEqual(format_size(-1), "-1 B")


class TestTruncate(unittest.TestCase):
    def test_short_stays(self):
        self.assertEqual(truncate("abc", 5), "abc")
        self.assertEqual(truncate("abc", 3), "abc")

    def test_long_truncated(self):
        self.assertEqual(truncate("abcdefghij", 5), "ab...")


class TestMoveToRecoverableBin(unittest.TestCase):
    def _make_tree(self):
        d = tempfile.mkdtemp()
        root = Path(d)
        (root / "a.txt").write_text("a")
        (root / "sub").mkdir()
        (root / "sub" / "b.txt").write_text("b")
        return root

    def test_file_moved_not_deleted(self):
        root = self._make_tree()
        src = root / "a.txt"
        ok = move_to_recoverable_bin(src, "cache")
        self.assertTrue(ok)
        dest = bin_path(src, "cache") / "a.txt"
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "a")
        self.assertFalse(src.exists())

    def test_dir_contents_moved_source_recreated(self):
        root = self._make_tree()
        sub = root / "sub"
        ok = move_to_recoverable_bin(sub, "sub")
        self.assertTrue(ok)
        dest = bin_path(sub, "sub") / "b.txt"
        self.assertTrue(dest.exists())
        self.assertEqual(dest.read_text(), "b")
        # source dir recreated (empty)
        self.assertTrue(sub.is_dir())
        self.assertEqual(list(sub.iterdir()), [])

    def test_bin_is_hidden_and_restorable(self):
        root = self._make_tree()
        src = root / "a.txt"
        move_to_recoverable_bin(src, "cache")
        bin_root = root / ".gigaorganize-trash" / "cache"
        self.assertTrue(bin_root.is_dir())
        restored = bin_root / "a.txt"
        self.assertTrue(restored.exists())

    def test_duplicate_names_get_unique(self):
        root = self._make_tree()
        (root / "x.txt").write_text("one")
        move_to_recoverable_bin(root / "x.txt", "d1")
        (root / "x.txt").write_text("two")
        # creating a second source with the same target name in the SAME bin
        src2 = root / "x.txt"
        self.assertTrue(move_to_recoverable_bin(src2, "d1"))
        first = bin_path(src2, "d1") / "x.txt"
        second = bin_path(src2, "d1") / "x (1).txt"
        contents = {first.read_text(), second.read_text()}
        self.assertEqual(contents, {"one", "two"})


if __name__ == "__main__":
    unittest.main()
