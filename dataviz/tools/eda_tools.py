from __future__ import annotations

from typing import Any

import pandas as pd


def compute_descriptive_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Compute descriptive statistics for numeric columns."""

    numeric = df.select_dtypes(include="number")
    return {
        col: {
            "count": int(series.count()),
            "mean": series.mean(),
            "std": series.std(),
            "min": series.min(),
            "25%": series.quantile(0.25),
            "50%": series.quantile(0.5),
            "75%": series.quantile(0.75),
            "max": series.max(),
        }
        for col, series in numeric.items()
    }


def detect_nulls(df: pd.DataFrame) -> dict[str, Any]:
    """Compute null counts and percentages for each column."""

    row_count = max(len(df), 1)
    return {
        col: {"count": int(series.isna().sum()), "pct": float(series.isna().sum() / row_count)}
        for col, series in df.items()
    }


def compute_correlation(df: pd.DataFrame, method: str = "pearson") -> dict[str, Any]:
    """Compute a correlation matrix for numeric columns."""

    return df.select_dtypes(include="number").corr(method=method).fillna(0).to_dict()


def detect_time_series(df: pd.DataFrame) -> dict[str, Any]:
    """Detect date-like columns and return a simple summary."""

    return {"date_columns": [col for col in df.columns if "date" in col.lower() or "time" in col.lower()]}


def detect_categorical_distributions(df: pd.DataFrame) -> dict[str, Any]:
    """Return value counts for categorical columns."""

    categorical = df.select_dtypes(exclude="number")
    return {col: series.value_counts(dropna=False).to_dict() for col, series in categorical.items()}


def detect_outliers(df: pd.DataFrame) -> dict[str, Any]:
    """Return a placeholder outlier summary for numeric columns."""

    numeric = df.select_dtypes(include="number")
    return {col: {"count": 0, "method": "iqr"} for col in numeric.columns}
