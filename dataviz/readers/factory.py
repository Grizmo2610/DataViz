from __future__ import annotations

from pathlib import Path

from .base import BaseReader
from .csv_reader import CsvReader
from .exceptions import UnsupportedFormatError
from .parquet_reader import ParquetReader
from .xlsx_reader import XlsxReader


def get_reader(file_path: str | Path, sheet_name: str | None = None) -> BaseReader:
    """Return the reader implementation for a file path.

    Args:
        file_path: Input file path.
        sheet_name: Optional sheet name for Excel files.

    Returns:
        A reader instance for the detected file type.

    Raises:
        UnsupportedFormatError: If the file extension is not supported.
    """

    suffix = Path(file_path).suffix.lower()
    if suffix == ".csv":
        return CsvReader()
    if suffix in {".xlsx", ".xls"}:
        return XlsxReader(sheet_name=sheet_name)
    if suffix == ".parquet":
        return ParquetReader()
    raise UnsupportedFormatError(f"Unsupported file format: {suffix or '(missing extension)'}")
