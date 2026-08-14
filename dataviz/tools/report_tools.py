from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

from dataviz.exporters import get_exporter


# ---------------------------------------------------------------------------
# Narrative writers
# ---------------------------------------------------------------------------

def write_summary(schema: dict[str, Any], stats: dict[str, Any], lang: str = "en") -> str:
    """Write a concise dataset summary derived from real stats.

    Args:
        schema: Output of ``detect_schema`` — has ``columns``, ``row_count``.
        stats:  Output of ``read_full_stats`` — has ``columns`` with numeric info.
        lang:   Reserved for future i18n.

    Returns:
        A multi-sentence summary string.
    """
    row_count = stats.get("row_count", schema.get("row_count", 0))
    col_count  = schema.get("column_count", len(schema.get("columns", [])))

    columns = schema.get("columns", [])
    dtypes = [c.get("dtype", "") for c in columns]
    n_numeric = sum(1 for d in dtypes if "int" in d or "float" in d)
    n_cat     = sum(1 for d in dtypes if d in ("object", "string", "category"))
    n_date    = sum(1 for d in dtypes if "datetime" in d)

    # Null summary from stats columns
    stat_cols = stats.get("columns", [])
    total_nulls = sum(c.get("null_count", 0) for c in stat_cols)
    null_rate   = total_nulls / max(row_count * col_count, 1)

    parts: list[str] = []
    parts.append(
        f"The dataset contains {row_count:,} rows and {col_count} columns "
        f"({n_numeric} numeric, {n_cat} categorical"
        + (f", {n_date} datetime" if n_date else "")
        + ")."
    )

    if null_rate > 0.3:
        parts.append(f"Data quality is a concern — {null_rate*100:.1f}% of values are missing across all columns.")
    elif null_rate > 0.05:
        parts.append(f"{null_rate*100:.1f}% of values are missing; review the most affected columns before modelling.")
    else:
        parts.append("Data completeness looks good — missing values are minimal.")

    # Highlight any column with > 40 % nulls
    problematic = [c["name"] for c in stat_cols if c.get("null_count", 0) / max(row_count, 1) > 0.4]
    if problematic:
        listed = ", ".join(f"'{n}'" for n in problematic[:5])
        parts.append(f"Columns with heavy missingness: {listed}.")

    return " ".join(parts)


def write_insights(stats: dict[str, Any], charts: list[dict[str, Any]], lang: str = "en") -> list[str]:
    """Derive key insights from EDA stats and rendered charts.

    Args:
        stats:  Output of ``read_full_stats``.
        charts: Rendered chart dicts from ``render_charts``.
        lang:   Reserved for future i18n.

    Returns:
        A list of insight strings (one per bullet).
    """
    insights: list[str] = []
    stat_cols = stats.get("columns", [])
    row_count = stats.get("row_count", 1) or 1

    numeric_cols = [c for c in stat_cols if "mean" in c]

    # --- Numeric distribution insights ---
    for col in numeric_cols:
        mean  = col.get("mean")
        std   = col.get("std")
        vmin  = col.get("min")
        vmax  = col.get("max")
        if None in (mean, std, vmin, vmax):
            continue
        name = col["name"]
        cv = std / abs(mean) if mean else None
        skew_hint = ""
        if vmax - mean > 3 * std:
            skew_hint = " with a long right tail"
        elif mean - vmin > 3 * std:
            skew_hint = " with a long left tail"
        if cv is not None and cv > 1.0:
            insights.append(
                f"'{name}' shows high variability (CV ≈ {cv:.2f}){skew_hint}; "
                "consider log-transforming before modelling."
            )
        elif skew_hint:
            insights.append(f"'{name}' appears skewed{skew_hint} — check for outliers.")

    # --- Missing data insights ---
    high_null = [c for c in stat_cols if c.get("null_count", 0) / row_count > 0.2]
    if high_null:
        listed = ", ".join(f"'{c['name']}' ({c['null_count']/row_count*100:.0f}%)" for c in high_null[:4])
        insights.append(f"High null rates found in {listed}.")

    # --- Chart-level insights ---
    heatmap = next((c for c in charts if c.get("chart_type") == "heatmap"), None)
    if heatmap and not heatmap.get("error"):
        insights.append(
            "A correlation heatmap was generated — look for strongly correlated pairs "
            "(|r| > 0.7) that may indicate redundant features or multicollinearity."
        )

    if not insights:
        insights.append(
            f"Analysis produced {len(charts)} visualisations. "
            "Review each chart to identify patterns, outliers, and distributional properties."
        )

    return insights


def write_recommendations(insights: list[str] | str, lang: str = "en") -> list[str]:
    """Derive actionable recommendations from insight list.

    Args:
        insights: Insight strings from ``write_insights``.
        lang:     Reserved for future i18n.

    Returns:
        A list of recommendation strings.
    """
    recs: list[str] = []

    insight_text = " ".join(insights) if isinstance(insights, list) else insights

    if "log-transform" in insight_text or "high variability" in insight_text:
        recs.append("Apply log or Box-Cox transformation to high-CV numeric columns before fitting models.")

    if "null" in insight_text or "missing" in insight_text:
        recs.append(
            "Address missing data before modelling: use median/mode imputation for low cardinality columns, "
            "KNN or iterative imputation for the rest."
        )

    if "correlated" in insight_text or "multicollinearity" in insight_text:
        recs.append(
            "Review the correlation matrix and drop or combine highly correlated features "
            "(|r| > 0.85) to reduce multicollinearity."
        )

    if "outlier" in insight_text or "tail" in insight_text:
        recs.append(
            "Validate outliers manually — clip or winsorise extreme values only if they are "
            "confirmed errors, not genuine signal."
        )

    if not recs:
        recs.append("Review all generated charts before proceeding to feature engineering or modelling.")

    recs.append(
        "Always validate findings on a held-out sample before drawing conclusions "
        "or sharing results with stakeholders."
    )
    return recs


# ---------------------------------------------------------------------------
# Dashboard assembly
# ---------------------------------------------------------------------------

def assemble_dashboard(
    sections: dict[str, Any],
    template_name: str,
    output_format: str,
    out_dir: str | Path,
    lang: str = "en",
    meta: dict[str, Any] | None = None,
    charts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble all report sections into an output file.

    Section order and display labels are determined here so agents don't need
    to know about the exporter internals.

    Args:
        sections:      Mapping of section_id → content.
        template_name: Logical template name (e.g. ``"default"``).
        output_format: ``"html"``, ``"pdf"``, ``"md"``, or ``"notebook"``.
        out_dir:       Directory to write the report into.
        lang:          Reserved for i18n.
        meta:          Optional metadata dict shown in the report header.
        charts:        Rendered chart dicts (for PDF SVG injection).

    Returns:
        Dict with ``output_path`` and ``sections_rendered``.
    """
    SECTION_ORDER = [
        ("summary",         "Overview"),
        ("schema",          "Schema"),
        ("stats",           "Descriptive statistics"),
        ("charts",          "Visualisations"),
        ("insights",        "Key insights"),
        ("recommendations", "Recommendations"),
    ]
    SECTION_PILLS = {
        "schema":          "EDA",
        "stats":           "EDA",
        "charts":          "Viz",
        "insights":        "Analysis",
        "recommendations": "Action",
    }

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    exporter = get_exporter(output_format)

    rendered_sections: list[str] = []
    for section_id, title in SECTION_ORDER:
        if section_id not in sections:
            continue
        content = sections[section_id]
        section_meta = {
            "id":    section_id,
            "title": title,
            "pill":  SECTION_PILLS.get(section_id, ""),
        }
        rendered_sections.append(exporter.render_section(section_meta, content))

    # Build kwargs for write()
    report_title = meta.get("file", "DataViz Report") if meta else "DataViz Report"
    write_kwargs: dict[str, Any] = {
        "title":         report_title,
        "meta":          meta or {},
        "template_name": template_name,
        "lang":          lang,
        "charts":        charts or [],
    }

    report_path = exporter.write(rendered_sections, out_path, **write_kwargs)
    return {"output_path": str(report_path), "sections_rendered": len(rendered_sections)}