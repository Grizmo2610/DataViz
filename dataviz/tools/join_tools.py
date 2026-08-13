from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from dataviz.readers import get_reader


def read_input_frame(file_path: str | Path, sheet_name: str | None = None) -> pd.DataFrame:
    """Read a single input file into a DataFrame.

    Args:
        file_path: Input file path.
        sheet_name: Optional worksheet name for Excel inputs.

    Returns:
        A pandas DataFrame.
    """

    return get_reader(file_path, sheet_name=sheet_name).read_sample(file_path, n_rows=10_000)


def join_files(
    file_paths: list[str | Path],
    join_on: str | list[str],
    join_type: str = "inner",
    sheet_name: str | None = None,
) -> pd.DataFrame:
    """Join multiple input files on a shared key.

    Args:
        file_paths: Input file paths.
        join_on: Column name or list of column names.
        join_type: Join strategy.
        sheet_name: Optional worksheet name for Excel inputs.

    Returns:
        The merged DataFrame.
    """

    frames = [read_input_frame(path, sheet_name=sheet_name) for path in file_paths]
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on=join_on, how=join_type)
    return merged


def infer_join_key(frames: list[pd.DataFrame]) -> str | None:
    """Infer a likely join key from a list of DataFrames.

    Args:
        frames: Input DataFrames.

    Returns:
        A likely join key, or None when no obvious key exists.
    """

    if not frames:
        return None
    common = set(frames[0].columns)
    for frame in frames[1:]:
        common &= set(frame.columns)
    for candidate in sorted(common):
        if candidate.lower().endswith("id") or candidate.lower() in {"id", "key", "code"}:
            return candidate
    return next(iter(sorted(common)), None)
