from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dataviz.readers import get_reader


def read_sample(file_path: str | Path, n_rows: int = 20) -> pd.DataFrame:
    """Read a small sample from a file.

    Args:
        file_path: Input file path.
        n_rows: Number of rows to read.

    Returns:
        A pandas DataFrame sample.
    """

    return get_reader(file_path).read_sample(file_path, n_rows=n_rows)


def detect_schema(df: pd.DataFrame) -> dict[str, Any]:
    """Detect basic dataframe schema metadata.

    Args:
        df: Input dataframe.

    Returns:
        Column metadata and counts.
    """

    columns = []
    for name in df.columns:
        series = df[name]
        columns.append(
            {
                "name": name,
                "dtype": str(series.dtype),
                "null_count": int(series.isna().sum()),
                "unique_count": int(series.nunique(dropna=True)),
            }
        )
    return {"columns": columns, "row_count": int(len(df)), "column_count": int(len(df.columns))}


def read_full_stats(file_path: str | Path) -> dict[str, Any]:
    """Read full statistics from a file.

    Args:
        file_path: Input file path.

    Returns:
        A statistics dictionary.
    """

    return get_reader(file_path).read_full_stats(file_path)
