from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd

from .base import BaseReader


def detect_csv_delimiter(file_path: str | Path) -> str:
    """Detect the delimiter used by a CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        The detected delimiter, defaulting to a comma.
    """

    sample = Path(file_path).read_text(encoding="utf-8", errors="ignore")[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return dialect.delimiter
    except csv.Error:
        return ","


def get_read_strategy(file_path: str | Path) -> str:
    """Select a read strategy based on file size.

    Args:
        file_path: Path to the CSV file.

    Returns:
        One of `full`, `chunked`, or `lazy`.
    """

    size_mb = Path(file_path).stat().st_size / (1024 * 1024)
    if size_mb < 50:
        return "full"
    if size_mb < 500:
        return "chunked"
    return "lazy"


class CsvReader(BaseReader):
    """Read CSV inputs with delimiter detection and basic scale handling."""

    def read_sample(self, file_path: str | Path, n_rows: int = 20) -> pd.DataFrame:
        """Read the first rows from a CSV file.

        Args:
            file_path: Path to the CSV file.
            n_rows: Number of rows to read.

        Returns:
            A pandas DataFrame containing the sample.
        """

        delimiter = detect_csv_delimiter(file_path)
        return pd.read_csv(file_path, sep=delimiter, nrows=n_rows)

    def read_full_stats(self, file_path: str | Path) -> dict[str, Any]:
        """Compute dataset statistics for a CSV file.

        Args:
            file_path: Path to the CSV file.

        Returns:
            A dictionary with row count, column metadata, and numeric stats.
        """

        delimiter = detect_csv_delimiter(file_path)
        strategy = get_read_strategy(file_path)
        if strategy == "lazy":
            chunks = pd.read_csv(file_path, sep=delimiter, chunksize=100_000)
            frame = pd.concat(list(chunks), ignore_index=True)
        elif strategy == "chunked":
            chunks = pd.read_csv(file_path, sep=delimiter, chunksize=10_000)
            frame = pd.concat(list(chunks), ignore_index=True)
        else:
            frame = pd.read_csv(file_path, sep=delimiter)

        return _summarize_frame(frame, delimiter=delimiter, strategy=strategy)


def _summarize_frame(frame: pd.DataFrame, delimiter: str, strategy: str) -> dict[str, Any]:
    """Summarize a pandas DataFrame.

    Args:
        frame: DataFrame to summarize.

    Returns:
        A serializable summary dictionary.
    """

    columns: list[dict[str, Any]] = []
    for column_name in frame.columns:
        series = frame[column_name]
        column_summary: dict[str, Any] = {
            "name": column_name,
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "unique_count": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            column_summary.update(
                {
                    "min": _coerce_value(series.min()),
                    "max": _coerce_value(series.max()),
                    "mean": _coerce_value(series.mean()),
                    "std": _coerce_value(series.std()),
                }
            )
        columns.append(column_summary)

    return {
        "row_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "delimiter": delimiter,
        "read_strategy": strategy,
        "columns": columns,
    }


def _coerce_value(value: Any) -> Any:
    """Convert pandas scalar values into JSON-friendly values.

    Args:
        value: Value returned by pandas aggregation.

    Returns:
        A JSON-serializable scalar.
    """

    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value
