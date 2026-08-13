from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dataviz.exporters import get_exporter


def write_summary(schema: dict[str, Any], stats: dict[str, Any], lang: str = "en") -> str:
    """Write a dataset summary narrative."""

    row_count = stats.get("row_count", schema.get("row_count", 0))
    column_count = schema.get("column_count", len(schema.get("columns", [])))
    return f"Dataset has {row_count} rows and {column_count} columns."


def write_insights(stats: dict[str, Any], charts: list[dict[str, Any]], lang: str = "en") -> str:
    """Write key insights from the analysis."""

    return f"Generated {len(charts)} chart ideas from the current dataset."


def write_recommendations(insights: str, lang: str = "en") -> str:
    """Write follow-up recommendations."""

    return "Review the strongest signals first and validate outliers before acting."


def assemble_dashboard(
    sections: dict[str, Any],
    template_name: str,
    output_format: str,
    out_dir: str | Path,
    lang: str = "en",
) -> dict[str, Any]:
    """Assemble a simple report payload into a file."""

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    exporter = get_exporter(output_format)
    rendered_sections = []
    for section_name, content in sections.items():
        rendered_sections.append(exporter.render_section({"id": section_name, "title": section_name.title()}, content))
    report_path = exporter.write(rendered_sections, out_path, template_name=template_name, lang=lang)
    return {"output_path": str(report_path), "sections_rendered": len(rendered_sections)}
