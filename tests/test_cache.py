from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dataviz.cache import clear_cache, compute_file_hash, read_cache, write_cache


class CacheTests(unittest.TestCase):
    """Verify cache hashing and persistence."""

    def test_compute_file_hash_changes_when_file_changes(self) -> None:
        """Hash output should change after the file content changes."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.txt"
            path.write_text("hello", encoding="utf-8")
            first = compute_file_hash(path)
            path.write_text("world", encoding="utf-8")
            second = compute_file_hash(path)

        self.assertNotEqual(first, second)

    def test_cache_write_and_read(self) -> None:
        """Cache payloads should be written and read back unchanged."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {"row_count": 2, "columns": ["a", "b"]}
            cache_path = write_cache("abc123", payload, base_dir=root)
            loaded = read_cache("abc123", base_dir=root)
            self.assertTrue(cache_path.exists())
            self.assertEqual(loaded["row_count"], 2)
            self.assertEqual(loaded["columns"], ["a", "b"])

    def test_clear_cache_removes_directory(self) -> None:
        """Clearing cache should remove the cache directory."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache_dir = root / ".dataviz" / "cache"
            cache_dir.mkdir(parents=True)
            (cache_dir / "test.json").write_text("{}", encoding="utf-8")
            cleared = clear_cache(base_dir=root)

        self.assertEqual(cleared, cache_dir)
        self.assertFalse(cache_dir.exists())


if __name__ == "__main__":
    unittest.main()
