from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from dataviz.readers import CsvReader, MissingDependencyError, ParquetReader, UnsupportedFormatError, XlsxReader, get_reader
from dataviz.readers.csv_reader import detect_csv_delimiter, get_read_strategy


class ReaderTests(unittest.TestCase):
    """Verify file reader behavior."""

    def test_csv_detects_semicolon_delimiter(self) -> None:
        """CSV delimiter detection should identify semicolon-separated data."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            path.write_text("a;b\n1;2\n", encoding="utf-8")

            self.assertEqual(detect_csv_delimiter(path), ";")

    def test_csv_reader_reads_sample_and_stats(self) -> None:
        """CSV reader should return a sample and statistics payload."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")

            reader = CsvReader()
            sample = reader.read_sample(path, n_rows=1)
            stats = reader.read_full_stats(path)

        self.assertEqual(len(sample), 1)
        self.assertEqual(stats["row_count"], 2)
        self.assertEqual(stats["delimiter"], ",")
        self.assertEqual(stats["read_strategy"], "full")

    def test_csv_scale_strategy_small(self) -> None:
        """Small CSV files should use the full strategy."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            path.write_text("a,b\n1,2\n", encoding="utf-8")

            self.assertEqual(get_read_strategy(path), "full")

    def test_xlsx_reader_uses_first_sheet(self) -> None:
        """XLSX reader should read the first sheet when no sheet is provided."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "First"
            sheet.append(["a", "b"])
            sheet.append([1, 2])
            workbook.create_sheet("Second")
            workbook.save(path)

            reader = XlsxReader()
            sample = reader.read_sample(path, n_rows=1)
            stats = reader.read_full_stats(path)

        self.assertEqual(list(sample.columns), ["a", "b"])
        self.assertEqual(stats["sheet_name"], "First")
        self.assertEqual(stats["file_format"], "xlsx")
        self.assertIn("available_sheets", stats)

    def test_xlsx_reader_lists_sheets(self) -> None:
        """XLSX reader should list available sheets."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.xlsx"
            workbook = Workbook()
            workbook.active.title = "First"
            workbook.create_sheet("Second")
            workbook.save(path)

            reader = XlsxReader()
            sheets = reader.list_sheets(path)

        self.assertEqual(sheets, ["First", "Second"])

    def test_get_reader_rejects_unknown_extension(self) -> None:
        """Unsupported file extensions should raise a clear error."""

        with self.assertRaises(UnsupportedFormatError):
            get_reader("data.txt")

    def test_parquet_reader_requires_engine(self) -> None:
        """Parquet reader should raise a dependency error when no engine is installed."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.parquet"
            path.write_bytes(b"not a real parquet file")

            reader = ParquetReader()
            with self.assertRaises(MissingDependencyError):
                reader.read_sample(path)


if __name__ == "__main__":
    unittest.main()
