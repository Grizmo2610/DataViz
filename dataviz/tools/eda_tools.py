from __future__ import annotations

from typing import Any

import pandas as pd


def compute_descriptive_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Compute descriptive statistics for numeric columns.

    Args:
        df: Input DataFrame.

    Returns:
        Dict mapping column name → statistics dict.
    """

    numeric = df.select_dtypes(include="number")
    result: dict[str, Any] = {}
    for col, series in numeric.items():
        valid = series.dropna()
        result[col] = {
            "count": int(series.count()),
            "mean": float(valid.mean()) if not valid.empty else None,
            "std": float(valid.std()) if len(valid) > 1 else None,
            "min": float(valid.min()) if not valid.empty else None,
            "25%": float(valid.quantile(0.25)) if not valid.empty else None,
            "50%": float(valid.quantile(0.50)) if not valid.empty else None,
            "75%": float(valid.quantile(0.75)) if not valid.empty else None,
            "max": float(valid.max()) if not valid.empty else None,
        }
    return result


def detect_nulls(df: pd.DataFrame) -> dict[str, Any]:
    """Compute null counts and percentages for each column.

    Args:
        df: Input DataFrame.

    Returns:
        Dict mapping column name → ``{"count": int, "pct": float}``.
    """

    row_count = max(len(df), 1)
    return {
        col: {
            "count": int(series.isna().sum()),
            "pct": float(series.isna().sum() / row_count),
        }
        for col, series in df.items()
    }


def compute_correlation(df: pd.DataFrame, method: str = "pearson") -> dict[str, Any]:
    """Compute a correlation matrix for numeric columns.

    Args:
        df: Input DataFrame.
        method: Correlation method — ``"pearson"``, ``"kendall"``, or ``"spearman"``.

    Returns:
        Nested dict ``{col: {other_col: corr_value}}``.
    """

    return df.select_dtypes(include="number").corr(method=method).fillna(0).to_dict()


def detect_time_series(df: pd.DataFrame) -> dict[str, Any]:
    """Detect datetime columns using dtype inspection and a parse attempt.

    A column is considered a time-series candidate when:
    - Its dtype is already ``datetime64``, OR
    - It is object/string dtype AND ``pd.to_datetime`` succeeds on a sample
      of up to 50 non-null values without raising.

    Args:
        df: Input DataFrame.

    Returns:
        Dict with keys:
        - ``date_columns`` (list[str]): Column names identified as datetime.
        - ``detection_method`` (dict[str, str]): How each column was detected.
    """

    date_cols: list[str] = []
    method_map: dict[str, str] = {}

    for col in df.columns:
        series = df[col]
        # Definitive: already a datetime dtype
        if pd.api.types.is_datetime64_any_dtype(series):
            date_cols.append(col)
            method_map[col] = "dtype"
            continue

        # Heuristic: try parsing a sample of string/object columns (pandas 3 uses StringDtype)
        is_string_like = series.dtype == object or pd.api.types.is_string_dtype(series)
        if is_string_like:
            sample = series.dropna().head(50)
            if sample.empty:
                continue
            try:
                import warnings as _warnings
                with _warnings.catch_warnings():
                    _warnings.simplefilter("ignore", UserWarning)
                    parsed = pd.to_datetime(sample, errors="raise")
                # Accept if ≥80 % of sampled values parsed successfully
                if parsed.notna().mean() >= 0.8:
                    date_cols.append(col)
                    method_map[col] = "parse_sample"
            except (ValueError, TypeError):
                pass

    return {"date_columns": date_cols, "detection_method": method_map}


def detect_categorical_distributions(df: pd.DataFrame) -> dict[str, Any]:
    """Return value counts for categorical / object columns.

    Args:
        df: Input DataFrame.

    Returns:
        Dict mapping column name → ``{value: count}`` (top-50 values).
    """

    categorical = df.select_dtypes(exclude="number")
    return {
        col: series.value_counts(dropna=False).head(50).to_dict()
        for col, series in categorical.items()
    }


def detect_outliers(df: pd.DataFrame, iqr_multiplier: float = 1.5) -> dict[str, Any]:
    """Detect outliers in numeric columns using the IQR fence method.

    A value is an outlier when it falls below ``Q1 - multiplier * IQR``
    or above ``Q3 + multiplier * IQR``.

    Args:
        df: Input DataFrame.
        iqr_multiplier: Fence width multiplier (default 1.5 = Tukey's rule).

    Returns:
        Dict mapping column name → outlier summary with keys:
        - ``count`` (int): Number of outlier rows.
        - ``pct`` (float): Fraction of non-null values that are outliers.
        - ``lower_fence`` (float): Lower bound.
        - ``upper_fence`` (float): Upper bound.
        - ``method`` (str): Always ``"iqr"``.
    """

    numeric = df.select_dtypes(include="number")
    result: dict[str, Any] = {}

    for col, series in numeric.items():
        valid = series.dropna()
        if valid.empty:
            result[col] = {"count": 0, "pct": 0.0, "lower_fence": None, "upper_fence": None, "method": "iqr"}
            continue

        q1 = float(valid.quantile(0.25))
        q3 = float(valid.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr

        outlier_mask = (valid < lower) | (valid > upper)
        count = int(outlier_mask.sum())

        result[col] = {
            "count": count,
            "pct": float(count / len(valid)),
            "lower_fence": round(lower, 6),
            "upper_fence": round(upper, 6),
            "method": "iqr",
        }

    return result