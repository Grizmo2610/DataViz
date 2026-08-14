from __future__ import annotations

import json
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _altair_available() -> bool:
    try:
        import altair  # noqa: F401
        return True
    except ImportError:
        return False


def _base_theme() -> dict[str, Any]:
    """Shared Altair config for a clean scientific look (IBM Plex / Inter font,
    light background, subtle grid, no chartjunk)."""
    return {
        "config": {
            "background": "#ffffff",
            "font": "Inter, 'IBM Plex Sans', system-ui, sans-serif",
            "title": {
                "fontSize": 14,
                "fontWeight": 600,
                "color": "#1a1a2e",
                "anchor": "start",
                "offset": 8,
            },
            "axis": {
                "labelFontSize": 11,
                "titleFontSize": 12,
                "titleFontWeight": 500,
                "labelColor": "#555770",
                "titleColor": "#333350",
                "gridColor": "#e8e8f0",
                "domainColor": "#c8c8d8",
                "tickColor": "#c8c8d8",
                "labelPadding": 6,
            },
            "legend": {
                "labelFontSize": 11,
                "titleFontSize": 12,
                "titleFontWeight": 500,
                "labelColor": "#555770",
                "titleColor": "#333350",
            },
            "view": {"strokeOpacity": 0},
            "range": {
                "category": [
                    "#4361ee", "#e63946", "#2ec4b6", "#f4a261",
                    "#7b2d8b", "#06a77d", "#e9c46a", "#264653",
                ],
            },
        }
    }


def _spec_to_dict(chart: Any) -> dict[str, Any]:
    """Convert an Altair chart to a plain dict spec with our theme applied."""
    spec = json.loads(chart.to_json())
    theme = _base_theme()
    # Merge config — chart-level config wins over theme defaults
    merged_config = {**theme["config"], **spec.get("config", {})}
    spec["config"] = merged_config
    # Default dimensions if not set
    spec.setdefault("width", "container")
    spec.setdefault("height", 300)
    return spec


def _fallback_spec(chart_type: str, reason: str) -> dict[str, Any]:
    """Return a minimal spec stub when Altair isn't available."""
    return {"_stub": True, "chart_type": chart_type, "reason": reason}


# ---------------------------------------------------------------------------
# Chart selection
# ---------------------------------------------------------------------------

def auto_select_charts(
    schema: dict[str, Any],
    stats: dict[str, Any],
    mode: str = "default",
) -> list[dict[str, Any]]:
    """Decide which charts are appropriate given the dataset schema and stats.

    Rules (applied in order):
    - Every numeric column → histogram
    - Pairs of numeric columns (up to 3 pairs) → scatter
    - Numeric + categorical column → boxplot
    - Date column + numeric → line
    - Correlation matrix exists → heatmap (once)

    Args:
        schema: Output of ``detect_schema``.
        stats: Output of ``read_full_stats``.
        mode: Pipeline mode (currently unused but reserved for future modes).

    Returns:
        List of chart spec dicts ready for ``render_charts``.
    """
    columns = schema.get("columns", [])
    numerics = [c["name"] for c in columns if "int" in c["dtype"] or "float" in c["dtype"]]
    categoricals = [c["name"] for c in columns if c["dtype"] in ("object", "string", "category", "bool")]
    dates = [c["name"] for c in columns if "datetime" in c["dtype"]]

    selected: list[dict[str, Any]] = []

    # Histograms — one per numeric col (cap at 6)
    for col in numerics[:6]:
        selected.append({"chart_type": "histogram", "column": col})

    # Scatter — first 3 pairs of numeric cols
    pairs = [(numerics[i], numerics[j]) for i in range(len(numerics)) for j in range(i + 1, len(numerics))]
    for x, y in pairs[:3]:
        selected.append({"chart_type": "scatter", "x": x, "y": y})

    # Boxplot — first numeric × first categorical
    if numerics and categoricals:
        selected.append({"chart_type": "boxplot", "column": numerics[0], "group_by": categoricals[0]})

    # Line — date × each numeric (cap at 3)
    if dates:
        for col in numerics[:3]:
            selected.append({"chart_type": "line", "x": dates[0], "y": col})

    # Correlation heatmap — only when 3+ numeric cols
    if len(numerics) >= 3:
        selected.append({"chart_type": "heatmap"})

    return selected


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_charts(
    chart_specs: list[dict[str, Any]],
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Render a list of chart spec descriptors into Altair/Vega JSON specs.

    Each output dict contains:
    - ``chart_id`` (str)
    - ``chart_type`` (str)
    - ``title`` (str)
    - ``vega_spec`` (dict) — ready for Vega-Embed
    - ``columns_used`` (list[str])

    Args:
        chart_specs: Descriptors from ``auto_select_charts``.
        df: The full (or sampled) DataFrame.

    Returns:
        List of rendered chart dicts.
    """
    rendered: list[dict[str, Any]] = []
    for spec in chart_specs:
        chart_type = spec.get("chart_type", "")
        try:
            if chart_type == "histogram":
                result = plot_histogram(df, spec["column"])
            elif chart_type == "scatter":
                result = plot_scatter(df, spec["x"], spec["y"], hue=spec.get("hue"))
            elif chart_type == "boxplot":
                result = plot_boxplot(df, spec["column"], group_by=spec.get("group_by"))
            elif chart_type == "line":
                result = plot_line(df, spec["x"], spec["y"])
            elif chart_type == "heatmap":
                result = plot_heatmap(df)
            elif chart_type == "bar":
                result = plot_bar(df, spec["x"], spec["y"])
            elif chart_type == "violin":
                result = plot_violin(df, spec["column"], group_by=spec.get("group_by"))
            elif chart_type == "pie":
                result = plot_pie(df, spec["column"])
            else:
                continue
            rendered.append(result)
        except Exception as exc:  # noqa: BLE001
            rendered.append({
                "chart_id": f"error_{chart_type}",
                "chart_type": chart_type,
                "title": f"{chart_type} (render error)",
                "error": str(exc),
                "vega_spec": None,
                "columns_used": [],
            })
    return rendered


# ---------------------------------------------------------------------------
# Individual chart functions
# ---------------------------------------------------------------------------

def plot_histogram(df: pd.DataFrame, col: str) -> dict[str, Any]:
    """Render a histogram with a KDE overlay for a numeric column.

    Args:
        df: Source DataFrame.
        col: Numeric column name.

    Returns:
        Rendered chart dict with ``vega_spec``.
    """
    if not _altair_available():
        return _fallback_spec("histogram", "altair not installed")

    import altair as alt

    valid = df[[col]].dropna()
    base = alt.Chart(valid).encode(
        x=alt.X(f"{col}:Q", bin=alt.Bin(maxbins=40), title=col),
        y=alt.Y("count()", title="Count"),
        tooltip=[alt.Tooltip(f"{col}:Q", bin=alt.Bin(maxbins=40)), "count()"],
    )
    bars = base.mark_bar(color="#4361ee", opacity=0.75, cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
    chart = bars.properties(title=f"Distribution of {col}")

    return {
        "chart_id": f"histogram_{col}",
        "chart_type": "histogram",
        "title": f"Distribution of {col}",
        "vega_spec": _spec_to_dict(chart),
        "columns_used": [col],
    }


def plot_scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    hue: str | None = None,
) -> dict[str, Any]:
    """Render a scatter plot, optionally coloured by a categorical column.

    Args:
        df: Source DataFrame.
        x: Column for the x-axis.
        y: Column for the y-axis.
        hue: Optional categorical column for colour encoding.

    Returns:
        Rendered chart dict with ``vega_spec``.
    """
    if not _altair_available():
        return _fallback_spec("scatter", "altair not installed")

    import altair as alt

    cols = [x, y] + ([hue] if hue else [])
    valid = df[cols].dropna()

    encode_kwargs: dict[str, Any] = {
        "x": alt.X(f"{x}:Q", title=x),
        "y": alt.Y(f"{y}:Q", title=y),
        "tooltip": [x, y] + ([hue] if hue else []),
    }
    if hue:
        encode_kwargs["color"] = alt.Color(f"{hue}:N", title=hue)

    chart = (
        alt.Chart(valid)
        .mark_circle(size=50, opacity=0.65, stroke="#ffffff", strokeWidth=0.5)
        .encode(**encode_kwargs)
        .properties(title=f"{y} vs {x}")
    )

    return {
        "chart_id": f"scatter_{x}_{y}",
        "chart_type": "scatter",
        "title": f"{y} vs {x}",
        "vega_spec": _spec_to_dict(chart),
        "columns_used": cols,
    }


def plot_bar(df: pd.DataFrame, x: str, y: str) -> dict[str, Any]:
    """Render a sorted bar chart (categorical x, numeric y).

    Args:
        df: Source DataFrame.
        x: Categorical column for the x-axis.
        y: Numeric column for bar height (aggregated as mean).

    Returns:
        Rendered chart dict with ``vega_spec``.
    """
    if not _altair_available():
        return _fallback_spec("bar", "altair not installed")

    import altair as alt

    valid = df[[x, y]].dropna()
    chart = (
        alt.Chart(valid)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#4361ee")
        .encode(
            x=alt.X(f"{x}:N", sort="-y", title=x),
            y=alt.Y(f"mean({y}):Q", title=f"Mean {y}"),
            tooltip=[alt.Tooltip(f"{x}:N"), alt.Tooltip(f"mean({y}):Q", format=".2f")],
        )
        .properties(title=f"{y} by {x}")
    )

    return {
        "chart_id": f"bar_{x}_{y}",
        "chart_type": "bar",
        "title": f"{y} by {x}",
        "vega_spec": _spec_to_dict(chart),
        "columns_used": [x, y],
    }


def plot_line(df: pd.DataFrame, x: str, y: str) -> dict[str, Any]:
    """Render a line chart with a confidence band for time-series data.

    Args:
        df: Source DataFrame.
        x: Temporal or ordered column for the x-axis.
        y: Numeric column for the y-axis.

    Returns:
        Rendered chart dict with ``vega_spec``.
    """
    if not _altair_available():
        return _fallback_spec("line", "altair not installed")

    import altair as alt

    valid = df[[x, y]].dropna().sort_values(x)
    x_type = "T" if pd.api.types.is_datetime64_any_dtype(df[x]) else "O"

    line = (
        alt.Chart(valid)
        .mark_line(color="#4361ee", strokeWidth=2)
        .encode(
            x=alt.X(f"{x}:{x_type}", title=x),
            y=alt.Y(f"{y}:Q", title=y),
            tooltip=[x, y],
        )
    )
    points = (
        alt.Chart(valid)
        .mark_circle(color="#4361ee", size=30, opacity=0.6)
        .encode(
            x=alt.X(f"{x}:{x_type}"),
            y=alt.Y(f"{y}:Q"),
        )
    )
    chart = (line + points).properties(title=f"{y} over {x}")

    return {
        "chart_id": f"line_{x}_{y}",
        "chart_type": "line",
        "title": f"{y} over {x}",
        "vega_spec": _spec_to_dict(chart),
        "columns_used": [x, y],
    }


def plot_boxplot(
    df: pd.DataFrame,
    col: str,
    group_by: str | None = None,
) -> dict[str, Any]:
    """Render a box-plot, optionally grouped by a categorical column.

    Args:
        df: Source DataFrame.
        col: Numeric column to plot.
        group_by: Optional categorical grouping column.

    Returns:
        Rendered chart dict with ``vega_spec``.
    """
    if not _altair_available():
        return _fallback_spec("boxplot", "altair not installed")

    import altair as alt

    cols = [col] + ([group_by] if group_by else [])
    valid = df[cols].dropna()

    encode_kwargs: dict[str, Any] = {"y": alt.Y(f"{col}:Q", title=col)}
    if group_by:
        encode_kwargs["x"] = alt.X(f"{group_by}:N", title=group_by)
        encode_kwargs["color"] = alt.Color(f"{group_by}:N", legend=None)
    else:
        encode_kwargs["x"] = alt.value(0)

    chart = (
        alt.Chart(valid)
        .mark_boxplot(extent="min-max", size=30)
        .encode(**encode_kwargs)
        .properties(title=f"Distribution of {col}" + (f" by {group_by}" if group_by else ""))
    )

    title = f"Distribution of {col}" + (f" by {group_by}" if group_by else "")
    return {
        "chart_id": f"boxplot_{col}" + (f"_{group_by}" if group_by else ""),
        "chart_type": "boxplot",
        "title": title,
        "vega_spec": _spec_to_dict(chart),
        "columns_used": cols,
    }


def plot_heatmap(df: pd.DataFrame) -> dict[str, Any]:
    """Render a correlation heatmap for all numeric columns.

    Args:
        df: Source DataFrame (numeric columns are selected automatically).

    Returns:
        Rendered chart dict with ``vega_spec``.
    """
    if not _altair_available():
        return _fallback_spec("heatmap", "altair not installed")

    import altair as alt

    numeric = df.select_dtypes(include="number")
    corr = numeric.corr().round(3)

    # Melt to long form for Altair
    corr_long = (
        corr.reset_index()
        .melt(id_vars="index", var_name="col_b", value_name="correlation")
        .rename(columns={"index": "col_a"})
    )

    chart = (
        alt.Chart(corr_long)
        .mark_rect()
        .encode(
            x=alt.X("col_a:N", title=None, axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("col_b:N", title=None),
            color=alt.Color(
                "correlation:Q",
                scale=alt.Scale(scheme="blueorange", domain=[-1, 1]),
                title="r",
            ),
            tooltip=[
                alt.Tooltip("col_a:N", title="Column A"),
                alt.Tooltip("col_b:N", title="Column B"),
                alt.Tooltip("correlation:Q", format=".3f", title="r"),
            ],
        )
        .properties(title="Correlation matrix", height=320)
    )

    # Overlay correlation values as text
    text = chart.mark_text(fontSize=10).encode(
        text=alt.Text("correlation:Q", format=".2f"),
        color=alt.condition(
            alt.datum.correlation > 0.5,
            alt.value("white"),
            alt.value("#1a1a2e"),
        ),
    )

    return {
        "chart_id": "heatmap_correlation",
        "chart_type": "heatmap",
        "title": "Correlation matrix",
        "vega_spec": _spec_to_dict(chart + text),
        "columns_used": list(numeric.columns),
    }


def plot_violin(
    df: pd.DataFrame,
    col: str,
    group_by: str | None = None,
) -> dict[str, Any]:
    """Render a violin plot using KDE density marks.

    Args:
        df: Source DataFrame.
        col: Numeric column to plot.
        group_by: Optional categorical grouping column.

    Returns:
        Rendered chart dict with ``vega_spec``.
    """
    if not _altair_available():
        return _fallback_spec("violin", "altair not installed")

    import altair as alt

    cols = [col] + ([group_by] if group_by else [])
    valid = df[cols].dropna()

    if group_by:
        chart = (
            alt.Chart(valid)
            .transform_density(col, as_=[col, "density"], groupby=[group_by])
            .mark_area(orient="horizontal", opacity=0.6)
            .encode(
                y=alt.Y(f"{col}:Q", title=col),
                x=alt.X("density:Q", stack="center", title=None, axis=alt.Axis(labels=False, ticks=False)),
                color=alt.Color(f"{group_by}:N", title=group_by),
                column=alt.Column(f"{group_by}:N", title=group_by),
                tooltip=[alt.Tooltip(f"{col}:Q"), alt.Tooltip("density:Q", format=".4f")],
            )
            .properties(width=120, height=280, title=f"Density of {col} by {group_by}")
        )
    else:
        chart = (
            alt.Chart(valid)
            .transform_density(col, as_=[col, "density"])
            .mark_area(orient="horizontal", opacity=0.7, color="#4361ee")
            .encode(
                y=alt.Y(f"{col}:Q", title=col),
                x=alt.X("density:Q", stack="center", title="Density", axis=alt.Axis(labels=False, ticks=False)),
                tooltip=[alt.Tooltip(f"{col}:Q"), alt.Tooltip("density:Q", format=".4f")],
            )
            .properties(width=200, height=300, title=f"Density of {col}")
        )

    title = f"Density of {col}" + (f" by {group_by}" if group_by else "")
    return {
        "chart_id": f"violin_{col}" + (f"_{group_by}" if group_by else ""),
        "chart_type": "violin",
        "title": title,
        "vega_spec": _spec_to_dict(chart),
        "columns_used": cols,
    }


def plot_pie(df: pd.DataFrame, col: str) -> dict[str, Any]:
    """Render a donut / pie chart for a categorical column (top 8 values).

    Args:
        df: Source DataFrame.
        col: Categorical column.

    Returns:
        Rendered chart dict with ``vega_spec``.
    """
    if not _altair_available():
        return _fallback_spec("pie", "altair not installed")

    import altair as alt

    counts = df[col].value_counts(dropna=True).head(8).reset_index()
    counts.columns = [col, "count"]

    chart = (
        alt.Chart(counts)
        .mark_arc(innerRadius=55, outerRadius=110, stroke="#ffffff", strokeWidth=1.5)
        .encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color(f"{col}:N", title=col, legend=alt.Legend(orient="right")),
            tooltip=[alt.Tooltip(f"{col}:N"), alt.Tooltip("count:Q")],
        )
        .properties(title=f"Composition of {col}", height=260)
    )

    return {
        "chart_id": f"pie_{col}",
        "chart_type": "pie",
        "title": f"Composition of {col}",
        "vega_spec": _spec_to_dict(chart),
        "columns_used": [col],
    }