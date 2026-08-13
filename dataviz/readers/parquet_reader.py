from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .base import BaseReader
from .exceptions import MissingDependencyError, UnsupportedFormatError


class ParquetReader(BaseReader):
    """Read Parquet inputs when a Parquet engine is available."""

    def read_sample(self, file_path: str | Path, n_rows: int = 20) -> pd.DataFrame:
        """Read a sample from a Parquet file.

        Args:
            file_path: Path to the Parquet file.
            n_rows: Number of rows to read.

        Returns:
            A pandas DataFrame containing the sample.
        """

        frame = self._read_frame(file_path)
        return frame.head(n_rows)

    def read_full_stats(self, file_path: str | Path) -> dict[str, Any]:
        """Compute dataset statistics for a Parquet file.

        Args:
            file_path: Path to the Parquet file.

        Returns:
            A dictionary with row count, column metadata, and numeric stats.
        """

        frame = self._read_frame(file_path)
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
            "file_format": "parquet",
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "columns": columns,
        }

    def _read_frame(self, file_path: str | Path) -> pd.DataFrame:
        """Read the full Parquet file with dependency checks.

        Args:
            file_path: Path to the Parquet file.

        Returns:
            The loaded DataFrame.

        Raises:
            MissingDependencyError: If no Parquet engine is available.
            UnsupportedFormatError: If pandas cannot load the file.
        """

        try:
            return pd.read_parquet(file_path)
        except ImportError as exc:
            raise MissingDependencyError(
                "Parquet support requires either 'pyarrow' or 'fastparquet'."
            ) from exc
        except Exception as exc:  # pragma: no cover - backend-specific error handling
            raise UnsupportedFormatError(f"Could not read Parquet file: {file_path}") from exc


def _coerce_value(value: Any) -> Any:
    """Convert pandas scalar values into JSON-friendly values."""

    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value
