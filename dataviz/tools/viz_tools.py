from __future__ import annotations

from typing import Any


def auto_select_charts(schema: dict[str, Any], stats: dict[str, Any], mode: str = "default") -> list[dict[str, Any]]:
    """Choose chart ideas from schema and statistics."""

    charts: list[dict[str, Any]] = []
    for column in schema.get("columns", []):
        if "int" in column.get("dtype", "") or "float" in column.get("dtype", ""):
            charts.append({"chart_type": "histogram", "column": column["name"]})
    return charts


def plot_histogram(col: str, engine: str = "plotly") -> dict[str, Any]:
    """Describe a histogram chart."""

    return {"chart_id": f"histogram_{col}", "chart_type": "histogram", "column": col, "engine": engine}


def plot_bar(x: str, y: str, engine: str = "plotly") -> dict[str, Any]:
    """Describe a bar chart."""

    return {"chart_id": f"bar_{x}_{y}", "chart_type": "bar", "x": x, "y": y, "engine": engine}


def plot_line(x: str, y: str, engine: str = "plotly") -> dict[str, Any]:
    """Describe a line chart."""

    return {"chart_id": f"line_{x}_{y}", "chart_type": "line", "x": x, "y": y, "engine": engine}


def plot_scatter(x: str, y: str, hue: str | None = None, engine: str = "plotly") -> dict[str, Any]:
    """Describe a scatter chart."""

    return {"chart_id": f"scatter_{x}_{y}", "chart_type": "scatter", "x": x, "y": y, "hue": hue, "engine": engine}


def plot_heatmap(corr_matrix: dict[str, Any], engine: str = "plotly") -> dict[str, Any]:
    """Describe a heatmap chart."""

    return {"chart_id": "heatmap_correlation", "chart_type": "heatmap", "engine": engine, "matrix": corr_matrix}


def plot_boxplot(col: str, group_by: str | None = None, engine: str = "plotly") -> dict[str, Any]:
    """Describe a boxplot chart."""

    return {"chart_id": f"boxplot_{col}", "chart_type": "boxplot", "column": col, "group_by": group_by, "engine": engine}


def plot_pie(col: str, engine: str = "plotly") -> dict[str, Any]:
    """Describe a pie chart."""

    return {"chart_id": f"pie_{col}", "chart_type": "pie", "column": col, "engine": engine}


def plot_missing_heatmap(df: Any, engine: str = "plotly") -> dict[str, Any]:
    """Describe a missing values heatmap."""

    return {"chart_id": "missing_heatmap", "chart_type": "missing_heatmap", "engine": engine}


def plot_pairplot(cols: list[str], engine: str = "plotly") -> dict[str, Any]:
    """Describe a pairplot."""

    return {"chart_id": "pairplot", "chart_type": "pairplot", "columns": cols, "engine": engine}


def plot_violin(col: str, group_by: str | None = None, engine: str = "plotly") -> dict[str, Any]:
    """Describe a violin chart."""

    return {"chart_id": f"violin_{col}", "chart_type": "violin", "column": col, "group_by": group_by, "engine": engine}
