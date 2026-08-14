from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Any

import pandas as pd

from dataviz.readers import get_reader
from dataviz.readers.csv_reader import CsvReader

logger = logging.getLogger(__name__)

# Warn when any single input file exceeds this many rows
_LARGE_FILE_ROW_WARNING = 500_000


def read_input_frame(file_path: str | Path, sheet_name: str | None = None) -> pd.DataFrame:
    """Read a single input file fully into a DataFrame.

    For CSV files this uses the reader's ``read_full_stats`` path internally
    but returns a complete DataFrame rather than a statistics dict, so that all
    rows participate in the join.

    Args:
        file_path: Input file path.
        sheet_name: Optional worksheet name for Excel inputs.

    Returns:
        A pandas DataFrame containing all rows.
    """

    reader = get_reader(file_path, sheet_name=sheet_name)

    # CsvReader exposes read_sample; for joins we need the full frame.
    # Use pandas directly here so we get every row regardless of file size.
    if isinstance(reader, CsvReader):
        from dataviz.readers.csv_reader import detect_csv_delimiter
        delimiter = detect_csv_delimiter(file_path)
        frame = pd.read_csv(file_path, sep=delimiter)
    else:
        # xlsx / parquet readers already load fully in _read_frame
        frame = reader.read_sample(file_path, n_rows=2 ** 31)  # effectively unlimited

    row_count = len(frame)
    if row_count > _LARGE_FILE_ROW_WARNING:
        warnings.warn(
            f"join_files: '{Path(file_path).name}' has {row_count:,} rows. "
            "Joining large files loads everything into RAM — ensure sufficient memory.",
            ResourceWarning,
            stacklevel=3,
        )
        logger.warning(
            "Large file detected for join: %s (%d rows)", file_path, row_count
        )

    return frame


def join_files(
    file_paths: list[str | Path],
    join_on: str | list[str],
    join_type: str = "inner",
    sheet_name: str | None = None,
) -> pd.DataFrame:
    """Join multiple input files on a shared key.

    All rows from every file are loaded before joining.  A :class:`ResourceWarning`
    is emitted for any individual file that exceeds ``_LARGE_FILE_ROW_WARNING`` rows.

    Args:
        file_paths: Input file paths (at least two).
        join_on: Column name or list of column names to join on.
        join_type: pandas merge ``how`` argument — ``"inner"``, ``"left"``,
            ``"right"``, or ``"outer"``.
        sheet_name: Optional worksheet name for Excel inputs.

    Returns:
        The merged DataFrame.

    Raises:
        ValueError: If fewer than two file paths are supplied.
    """

    if len(file_paths) < 2:
        raise ValueError("join_files requires at least two file paths.")

    frames = [read_input_frame(path, sheet_name=sheet_name) for path in file_paths]

    # Validate that join key(s) exist in every frame before attempting the merge
    keys = [join_on] if isinstance(join_on, str) else list(join_on)
    for path, frame in zip(file_paths, frames):
        missing = [k for k in keys if k not in frame.columns]
        if missing:
            raise KeyError(
                f"Join key(s) {missing} not found in '{Path(path).name}'. "
                f"Available columns: {list(frame.columns)}"
            )

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on=join_on, how=join_type)

    logger.debug(
        "join_files: merged %d files on %r (%s) → %d rows, %d columns",
        len(file_paths),
        join_on,
        join_type,
        len(merged),
        len(merged.columns),
    )
    return merged


def infer_join_key(frames: list[pd.DataFrame]) -> str | None:
    """Infer a likely join key from a list of DataFrames.

    Args:
        frames: Input DataFrames.

    Returns:
        A likely join key, or ``None`` when no obvious key exists.
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