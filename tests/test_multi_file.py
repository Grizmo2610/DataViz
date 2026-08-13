from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dataviz.tools.join_tools import infer_join_key, join_files


class MultiFileTests(unittest.TestCase):
    """Verify multi-file join support."""

    def test_join_files_inner(self) -> None:
        """Files should join on a shared key."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = root / "left.csv"
            right = root / "right.csv"
            left.write_text("id,name\n1,A\n2,B\n", encoding="utf-8")
            right.write_text("id,value\n1,10\n2,20\n", encoding="utf-8")

            merged = join_files([left, right], join_on="id", join_type="inner")

        self.assertEqual(len(merged), 2)
        self.assertIn("name", merged.columns)
        self.assertIn("value", merged.columns)

    def test_infer_join_key_finds_id(self) -> None:
        """Join key inference should prefer id-like columns."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            left = root / "left.csv"
            right = root / "right.csv"
            left.write_text("customer_id,name\n1,A\n", encoding="utf-8")
            right.write_text("customer_id,value\n1,10\n", encoding="utf-8")

            import pandas as pd

            frames = [pd.read_csv(left), pd.read_csv(right)]
            join_key = infer_join_key(frames)

        self.assertEqual(join_key, "customer_id")


if __name__ == "__main__":
    unittest.main()
