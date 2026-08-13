from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .base import BaseReader
from .exceptions import UnsupportedFormatError


class XlsxReader(BaseReader):
    """Read Excel workbooks with optional sheet selection."""

    def __init__(self, sheet_name: str | None = None) -> None:
        """Initialize the reader.

        Args:
            sheet_name: Optional sheet name to read.
        """

        self.sheet_name = sheet_name

    def read_sample(self, file_path: str | Path, n_rows: int = 20) -> pd.DataFrame:
        """Read a sample from the selected worksheet.

        Args:
            file_path: Path to the Excel workbook.
            n_rows: Number of rows to read.

        Returns:
            A pandas DataFrame containing the sample.
        """

        with pd.ExcelFile(file_path) as workbook:
            sheet_name = self.sheet_name or workbook.sheet_names[0]
            return workbook.parse(sheet_name=sheet_name, nrows=n_rows)

    def read_full_stats(self, file_path: str | Path) -> dict[str, Any]:
        """Compute dataset statistics for the selected worksheet.

        Args:
            file_path: Path to the Excel workbook.

        Returns:
            A dictionary with row count, column metadata, and numeric stats.
        """

        with pd.ExcelFile(file_path) as workbook:
            sheet_name = self.sheet_name or workbook.sheet_names[0]
            frame = workbook.parse(sheet_name=sheet_name)
        return {
            "file_format": "xlsx",
            "sheet_name": sheet_name,
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "columns": _summarize_frame(frame),
        }


def _summarize_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Summarize columns in a DataFrame.

    Args:
        frame: DataFrame to summarize.

    Returns:
        Column summary dictionaries.
    """

    results: list[dict[str, Any]] = []
    for column_name in frame.columns:
        series = frame[column_name]
        result: dict[str, Any] = {
            "name": column_name,
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "unique_count": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            result.update(
                {
                    "min": _coerce_value(series.min()),
                    "max": _coerce_value(series.max()),
                    "mean": _coerce_value(series.mean()),
                    "std": _coerce_value(series.std()),
                }
            )
        results.append(result)
    return results


def _coerce_value(value: Any) -> Any:
    """Convert pandas scalar values into JSON-friendly values."""

    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value
