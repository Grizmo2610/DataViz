from __future__ import annotations

import functools
import math
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from dataviz.readers import get_reader
from dataviz.tools import ToolRegistry
from dataviz.tools.join_tools import read_input_frame

try:
    # mcp>=2 renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer as _ServerClass
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _ServerClass
    from mcp.server.fastmcp.exceptions import ToolError

mcp = _ServerClass("dataviz")

DEFAULT_OUT_DIR = "dataviz_output"
OUTPUT_FORMATS = ("html", "md", "pdf", "notebook")
CHART_TYPES = ("histogram", "scatter", "boxplot", "line", "heatmap", "bar", "violin", "pie")
ANALYSIS_SECTIONS = (
    "stats",
    "nulls",
    "correlation",
    "time_series",
    "categorical",
    "outliers",
)


@lru_cache(maxsize=1)
def _registry() -> ToolRegistry:
    """Return the shared tool registry, loading it on first use.

    Returns:
        A ``ToolRegistry`` populated from ``registry.json``.
    """

    return ToolRegistry()


def _tool(name: str) -> Any:
    """Look up a registered DataViz tool by name.

    Args:
        name: Tool name as listed in ``registry.json``.

    Returns:
        The tool callable.
    """

    return _registry().get(name)


def _load_frame(file_path: str, sheet_name: str | None = None) -> pd.DataFrame:
    """Read a full input file into a DataFrame.

    Args:
        file_path: Path to a CSV, Excel, or Parquet file.
        sheet_name: Optional worksheet name for Excel inputs.

    Returns:
        The full DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist (surfaced as ToolError by tools).
    """

    path = Path(file_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    return read_input_frame(path, sheet_name=sheet_name)


def _jsonable(value: Any) -> Any:
    """Convert pandas/numpy values into plain JSON-safe Python values.

    NaN and infinity become ``None`` so the payload is valid JSON.

    Args:
        value: Any value returned by a DataViz tool.

    Returns:
        A structure made only of dict, list, str, int, float, bool, and None.
    """

    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, pd.DataFrame):
        return _jsonable(value.to_dict(orient="records"))
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if hasattr(value, "item") and callable(value.item):
        try:
            value = value.item()
        except (ValueError, TypeError):
            return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _report_errors(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Turn any exception into a ``ToolError`` so the client sees the reason.

    Without this, mcp 2.x hides the message of unexpected exceptions and the
    client only sees a generic "Error executing tool".

    Args:
        fn: The tool function to wrap.

    Returns:
        A wrapped function with the same signature that raises ``ToolError``.
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except ToolError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"{type(exc).__name__}: {exc}") from exc

    return wrapper


@mcp.tool()
@_report_errors
def inspect_dataset(file_path: str, sheet_name: str | None = None, n_rows: int = 5) -> dict[str, Any]:
    """Inspect a tabular file: schema, a few sample rows, and null counts.

    Use this first to learn what columns exist before choosing charts.

    Args:
        file_path: Path to a CSV, Excel (.xlsx), or Parquet file.
        sheet_name: Worksheet name for Excel files. Defaults to the first sheet.
        n_rows: Number of sample rows to return.

    Returns:
        Dict with ``schema`` (columns, dtypes, null and unique counts, row and
        column counts) and ``sample`` (list of row dicts).
    """

    frame = _load_frame(file_path, sheet_name)
    schema = _tool("detect_schema")(frame)
    return _jsonable({"schema": schema, "sample": frame.head(max(n_rows, 0))})


@mcp.tool()
@_report_errors
def analyze_dataset(
    file_path: str,
    sheet_name: str | None = None,
    sections: list[str] | None = None,
) -> dict[str, Any]:
    """Run exploratory data analysis on a tabular file.

    Args:
        file_path: Path to a CSV, Excel (.xlsx), or Parquet file.
        sheet_name: Worksheet name for Excel files. Defaults to the first sheet.
        sections: Subset of ``stats``, ``nulls``, ``correlation``,
            ``time_series``, ``categorical``, ``outliers``. Defaults to all.

    Returns:
        Dict keyed by the requested section names.

    Raises:
        ToolError: If an unknown section name is requested.
    """

    requested = list(sections) if sections else list(ANALYSIS_SECTIONS)
    unknown = [s for s in requested if s not in ANALYSIS_SECTIONS]
    if unknown:
        raise ValueError(f"Unknown sections {unknown}; choose from {list(ANALYSIS_SECTIONS)}")

    frame = _load_frame(file_path, sheet_name)
    tool_for_section = {
        "stats": "compute_descriptive_stats",
        "nulls": "detect_nulls",
        "correlation": "compute_correlation",
        "time_series": "detect_time_series",
        "categorical": "detect_categorical_distributions",
        "outliers": "detect_outliers",
    }
    result = {name: _tool(tool_for_section[name])(frame) for name in requested}
    return _jsonable(result)


@mcp.tool()
@_report_errors
def suggest_charts(file_path: str, sheet_name: str | None = None) -> list[dict[str, Any]]:
    """Suggest suitable charts for a dataset based on its column types.

    The returned specs can be passed one by one to ``render_chart``.

    Args:
        file_path: Path to a CSV, Excel (.xlsx), or Parquet file.
        sheet_name: Worksheet name for Excel files. Defaults to the first sheet.

    Returns:
        List of chart spec dicts such as ``{"chart_type": "histogram", "column": "age"}``.
    """

    frame = _load_frame(file_path, sheet_name)
    schema = _tool("detect_schema")(frame)
    return _jsonable(_tool("auto_select_charts")(schema, {}))


@mcp.tool()
@_report_errors
def render_chart(
    file_path: str,
    chart_type: str,
    column: str | None = None,
    x: str | None = None,
    y: str | None = None,
    group_by: str | None = None,
    hue: str | None = None,
    sheet_name: str | None = None,
    out_dir: str | None = None,
    include_vega_spec: bool = False,
) -> dict[str, Any]:
    """Render one chart and save it as an SVG file.

    Required arguments per chart type: ``histogram``, ``violin`` and ``pie``
    need ``column`` (violin also accepts ``group_by``); ``boxplot`` needs
    ``column`` and optionally ``group_by``; ``scatter`` needs ``x`` and ``y``
    (optional ``hue``); ``line`` and ``bar`` need ``x`` and ``y``; ``heatmap``
    needs nothing and plots the numeric correlation matrix.

    Args:
        file_path: Path to a CSV, Excel (.xlsx), or Parquet file.
        chart_type: One of histogram, scatter, boxplot, line, heatmap, bar,
            violin, pie.
        column: Column for single-variable charts.
        x: X-axis column.
        y: Y-axis column.
        group_by: Grouping column for boxplot and violin.
        hue: Colour-by column for scatter.
        sheet_name: Worksheet name for Excel files. Defaults to the first sheet.
        out_dir: Directory for the SVG. Defaults to ``dataviz_output``.
        include_vega_spec: Also return the full Vega-Lite spec (can be large).

    Returns:
        Dict with ``chart_id``, ``title``, ``columns_used``, ``svg_path`` (absolute
        path or None when no SVG backend is installed), and optionally ``vega_spec``.

    Raises:
        ToolError: If ``chart_type`` is unknown or required columns are missing.
    """

    if chart_type not in CHART_TYPES:
        raise ValueError(f"Unknown chart_type '{chart_type}'; choose from {list(CHART_TYPES)}")

    spec: dict[str, Any] = {"chart_type": chart_type}
    for key, val in (("column", column), ("x", x), ("y", y), ("group_by", group_by), ("hue", hue)):
        if val is not None:
            spec[key] = val

    frame = _load_frame(file_path, sheet_name)
    target_dir = str(Path(out_dir or DEFAULT_OUT_DIR).expanduser().resolve())
    rendered = _tool("render_charts")([spec], frame, target_dir)
    if not rendered:
        raise ValueError(f"Could not render '{chart_type}' with arguments {spec}")

    chart = rendered[0]
    if chart.get("error"):
        raise ValueError(f"Chart render failed: {chart['error']}")

    image_path = chart.get("image_path")
    result: dict[str, Any] = {
        "chart_id": chart.get("chart_id"),
        "chart_type": chart.get("chart_type"),
        "title": chart.get("title"),
        "columns_used": chart.get("columns_used", []),
        "svg_path": str(Path(target_dir) / image_path) if image_path else None,
    }
    if include_vega_spec:
        result["vega_spec"] = chart.get("vega_spec")
    return _jsonable(result)


@mcp.tool()
@_report_errors
def export_report(
    file_path: str,
    output_format: str = "html",
    out_dir: str | None = None,
    sheet_name: str | None = None,
    lang: str = "en",
) -> dict[str, Any]:
    """Run the full analysis and export a report.

    Reads the file, picks charts automatically, writes rule-based summary,
    insights, and recommendations (no LLM call), and exports the result.

    Args:
        file_path: Path to a CSV, Excel (.xlsx), or Parquet file.
        output_format: ``html``, ``md``, ``pdf`` (needs Playwright Chromium), or
            ``notebook``.
        out_dir: Output directory. Defaults to ``dataviz_output``.
        sheet_name: Worksheet name for Excel files. Defaults to the first sheet.
        lang: Reserved for report language.

    Returns:
        Dict with ``output_path``, ``sections_rendered``, ``charts_rendered``,
        and ``charts_failed``.

    Raises:
        ToolError: If ``output_format`` is not supported.
    """

    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"Unknown output_format '{output_format}'; choose from {list(OUTPUT_FORMATS)}")

    path = Path(file_path).expanduser()
    frame = _load_frame(file_path, sheet_name)
    target_dir = str(Path(out_dir or DEFAULT_OUT_DIR).expanduser().resolve())

    schema = _tool("detect_schema")(frame)
    stats = get_reader(path, sheet_name=sheet_name).read_full_stats(path)
    chart_specs = _tool("auto_select_charts")(schema, stats)
    charts = _tool("render_charts")(chart_specs, frame, target_dir)
    good_charts = [c for c in charts if not c.get("error")]

    summary = _tool("write_summary")(schema, stats, lang)
    insights = _tool("write_insights")(stats, good_charts, lang)
    recommendations = _tool("write_recommendations")(insights, lang)

    sections = {
        "summary": summary,
        "schema": schema,
        "stats": stats,
        "charts": good_charts,
        "insights": insights,
        "recommendations": recommendations,
    }
    meta = {
        "File": path.name,
        "Rows": f"{stats.get('row_count', len(frame)):,}",
        "Columns": str(stats.get("column_count", len(frame.columns))),
        "Charts": str(len(good_charts)),
    }
    tool_trace = [
        {"tool": "render_charts", "input": {"chart_specs": chart_specs}},
        {"tool": "write_summary", "input": {}},
        {"tool": "write_insights", "input": {}},
        {"tool": "write_recommendations", "input": {}},
    ]
    dashboard = _tool("assemble_dashboard")(
        sections=sections,
        template_name="default",
        output_format=output_format,
        out_dir=target_dir,
        lang=lang,
        meta=meta,
        charts=good_charts,
        tool_trace=tool_trace,
    )
    return _jsonable(
        {
            "output_path": str(Path(dashboard["output_path"]).resolve()),
            "sections_rendered": dashboard.get("sections_rendered"),
            "charts_rendered": len(good_charts),
            "charts_failed": len(charts) - len(good_charts),
        }
    )


def main() -> None:
    """Run the DataViz MCP server over stdio."""

    mcp.run()


if __name__ == "__main__":
    main()
