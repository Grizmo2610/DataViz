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
        One of ``full``, ``chunked``, or ``lazy``.
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
        """Compute dataset statistics for a CSV file without loading it fully into RAM.

        For files under 50 MB the file is read in one shot.  For larger files an
        incremental pass accumulates per-column statistics (count, null count,
        min/max/sum/sum-of-squares for numerics, unique-value sketch for
        categoricals) chunk-by-chunk so peak memory stays proportional to chunk
        size, not file size.

        Args:
            file_path: Path to the CSV file.

        Returns:
            A dictionary with row count, column metadata, and numeric stats.
        """

        delimiter = detect_csv_delimiter(file_path)
        strategy = get_read_strategy(file_path)

        if strategy == "full":
            frame = pd.read_csv(file_path, sep=delimiter)
            return _summarize_frame(frame, delimiter=delimiter, strategy=strategy)

        # chunked / lazy — stream the file; never concat everything into memory
        chunk_size = 10_000 if strategy == "chunked" else 100_000
        accumulator: dict[str, _ColumnAccumulator] = {}
        total_rows = 0
        dtypes: dict[str, str] = {}

        for chunk in pd.read_csv(file_path, sep=delimiter, chunksize=chunk_size):
            total_rows += len(chunk)
            for col in chunk.columns:
                if col not in accumulator:
                    accumulator[col] = _ColumnAccumulator()
                    dtypes[col] = str(chunk[col].dtype)
                accumulator[col].update(chunk[col])

        columns: list[dict[str, Any]] = []
        for col, acc in accumulator.items():
            columns.append(acc.to_summary(col, dtypes[col]))

        return {
            "row_count": total_rows,
            "column_count": len(accumulator),
            "delimiter": delimiter,
            "read_strategy": strategy,
            "columns": columns,
        }


class _ColumnAccumulator:
    """Accumulate per-column statistics incrementally across chunks."""

    __slots__ = (
        "_count",
        "_null_count",
        "_is_numeric",
        "_min",
        "_max",
        "_sum",
        "_sum_sq",
        "_unique_sketch",
    )

    # Limit unique-value tracking to avoid unbounded RAM on high-cardinality cols
    _UNIQUE_CAP = 50_000

    def __init__(self) -> None:
        self._count = 0
        self._null_count = 0
        self._is_numeric: bool | None = None
        self._min: float | None = None
        self._max: float | None = None
        self._sum: float = 0.0
        self._sum_sq: float = 0.0
        self._unique_sketch: set[Any] | None = set()

    def update(self, series: pd.Series) -> None:
        """Incorporate one chunk's worth of data."""

        self._count += len(series)
        self._null_count += int(series.isna().sum())

        if self._is_numeric is None:
            self._is_numeric = pd.api.types.is_numeric_dtype(series)

        if self._is_numeric:
            valid = series.dropna()
            if not valid.empty:
                chunk_min = float(valid.min())
                chunk_max = float(valid.max())
                self._min = chunk_min if self._min is None else min(self._min, chunk_min)
                self._max = chunk_max if self._max is None else max(self._max, chunk_max)
                self._sum += float(valid.sum())
                self._sum_sq += float((valid ** 2).sum())

        # Track unique values up to the cap; beyond that stop counting
        if self._unique_sketch is not None:
            self._unique_sketch.update(series.dropna().tolist())
            if len(self._unique_sketch) > self._UNIQUE_CAP:
                self._unique_sketch = None  # too many — mark as unknown

    def to_summary(self, name: str, dtype: str) -> dict[str, Any]:
        """Return a serializable column summary."""

        non_null = self._count - self._null_count
        summary: dict[str, Any] = {
            "name": name,
            "dtype": dtype,
            "null_count": self._null_count,
            "unique_count": len(self._unique_sketch) if self._unique_sketch is not None else None,
        }
        if self._is_numeric and non_null > 0:
            mean = self._sum / non_null
            # population variance from sum-of-squares; convert to sample std
            variance = (self._sum_sq / non_null) - mean ** 2
            std = (max(variance, 0.0) ** 0.5) * ((non_null / (non_null - 1)) ** 0.5) if non_null > 1 else 0.0
            summary.update(
                {
                    "min": self._min,
                    "max": self._max,
                    "mean": round(mean, 6),
                    "std": round(std, 6),
                }
            )
        return summary


def _summarize_frame(frame: pd.DataFrame, delimiter: str, strategy: str) -> dict[str, Any]:
    """Summarize a pandas DataFrame (used for small files read in one shot).

    Args:
        frame: DataFrame to summarize.
        delimiter: Detected CSV delimiter.
        strategy: Read strategy label.

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