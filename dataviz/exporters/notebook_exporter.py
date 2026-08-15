from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .base import BaseExporter

# Tools whose LLM-supplied "input" args we don't bother formatting (either
# they are trivial or their real output is rendered as a dedicated cell
# elsewhere, e.g. render_charts -> per-chart Vega-Lite output cells).
_RESULT_FROM_SECTION = {
    "write_summary": "summary",
    "write_insights": "insights",
    "write_recommendations": "recommendations",
}


def _format_call(tool: str, args: dict[str, Any]) -> str:
    """Render a tool call as a Python-looking source line, e.g.

        write_recommendations(insights=[...], lang='en')

    Kept short: large/nested values are summarised instead of dumped in full,
    since this is meant to be read, not executed.
    """
    parts = []
    for key, value in args.items():
        parts.append(f"{key}={_format_value(value)}")
    return f"{tool}({', '.join(parts)})"


def _format_value(value: Any, max_len: int = 90) -> str:
    if isinstance(value, str):
        rendered = repr(value)
    elif isinstance(value, (list, tuple)):
        rendered = f"[<{len(value)} item(s)>]" if value and isinstance(value[0], (dict, list)) else repr(value)
    elif isinstance(value, dict):
        rendered = f"{{<{len(value)} key(s)>}}"
    else:
        rendered = repr(value)
    return rendered if len(rendered) <= max_len else rendered[:max_len] + "…"


def _html_table(columns: list[dict[str, Any]]) -> str:
    """Render a list of column-detail dicts as a real HTML table."""
    if not columns:
        return "_No columns._"
    keys: list[str] = []
    for col in columns:
        for key in col.keys():
            if key not in keys:
                keys.append(key)
    if "name" in keys:
        keys.remove("name")
        keys.insert(0, "name")
    header = "".join(f"<th>{key}</th>" for key in keys)
    rows = "".join(
        "<tr>" + "".join(f"<td>{col.get(key, '')}</td>" for key in keys) + "</tr>"
        for col in columns
    )
    return f"<table>\n<thead><tr>{header}</tr></thead>\n<tbody>\n{rows}\n</tbody>\n</table>"


def _text_output_cell(source: str, result_text: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "id": uuid.uuid4().hex[:8],
        "execution_count": None,
        "metadata": {},
        "source": source,
        "outputs": [
            {
                "output_type": "execute_result",
                "execution_count": None,
                "data": {"text/plain": result_text},
                "metadata": {},
            }
        ],
    }


def _chart_output_cell(source: str, chart: dict[str, Any], out_path: Path) -> dict[str, Any]:
    """Build a code cell whose output is a real chart.

    Primary mimetype is ``application/vnd.vegalite.v6+json`` -- rendered
    natively by JupyterLab (with the Vega extension), nbviewer, and GitHub's
    own .ipynb preview, no server-side conversion required. When
    ``render_charts`` also saved a real SVG file (``chart["image_path"]``),
    its actual bytes are attached too as ``image/svg+xml``, so viewers
    without Vega-Lite support still show the real generated picture rather
    than nothing.
    """
    vega_spec = chart.get("vega_spec")
    title = chart.get("title", chart.get("chart_id", "chart"))
    outputs: list[dict[str, Any]]
    if chart.get("error") or not vega_spec:
        outputs = [
            {
                "output_type": "error",
                "ename": "ChartRenderError",
                "evalue": chart.get("error", "no vega_spec returned"),
                "traceback": [],
            }
        ]
    else:
        data: dict[str, Any] = {
            "application/vnd.vegalite.v6+json": vega_spec,
            "text/plain": f"<Vega-Lite chart: {title}>",
        }
        image_path = chart.get("image_path")
        if image_path:
            svg_file = out_path / image_path
            if svg_file.exists():
                data["image/svg+xml"] = svg_file.read_text(encoding="utf-8")
        outputs = [{"output_type": "display_data", "data": data, "metadata": {}}]
    return {
        "cell_type": "code",
        "id": uuid.uuid4().hex[:8],
        "execution_count": None,
        "metadata": {},
        "source": source,
        "outputs": outputs,
    }


def _markdown_cell(source: str) -> dict[str, Any]:
    return {"cell_type": "markdown", "id": uuid.uuid4().hex[:8], "metadata": {}, "source": source}


class NotebookExporter(BaseExporter):
    """Write a report as a Jupyter notebook.

    Rather than dumping narrative text, this reconstructs the pipeline as a
    real sequence of cells: one markdown header + code cell per tool call the
    agents actually made (``tool_trace``), with tool results (including
    rendered charts, as real Vega-Lite + saved-SVG outputs) attached as
    genuine cell outputs, and schema/stats rendered as real HTML tables.
    """

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a plain-fact section (schema/stats) as markdown.

        Sections produced by an actual agent tool call (charts, summary,
        insights, recommendations) are instead reconstructed from
        ``tool_trace`` in :meth:`write` and are not rendered here.
        """
        title = section.get("title", section.get("id", "Section"))
        section_id = section.get("id", "")
        if section_id in ("schema", "stats") and isinstance(content, dict) and isinstance(content.get("columns"), list):
            body = _html_table(content["columns"])
        elif isinstance(content, dict):
            body = "\n".join(f"- **{key}**: {value}" for key, value in content.items())
        elif isinstance(content, list):
            body = "\n".join(f"- {item}" for item in content)
        else:
            body = str(content)
        return f"## {title}\n\n{body}"

    def write(self, rendered_sections: list[str], out_dir: str | Path, **kwargs: Any) -> Path:
        """Write the notebook report to disk."""

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "report.ipynb"

        tool_trace: list[dict[str, Any]] = kwargs.get("tool_trace") or []
        charts: list[dict[str, Any]] = kwargs.get("charts") or []
        sections_raw: dict[str, Any] = kwargs.get("sections_raw") or {}
        title = kwargs.get("title", "DataViz Report")

        cells: list[dict[str, Any]] = [_markdown_cell(f"# {title}")]

        # Plain-fact sections (schema/stats) have no associated tool call --
        # ReaderAgent computes them deterministically, not via an LLM loop.
        for section_str in rendered_sections:
            heading = section_str.split("\n", 1)[0].lstrip("# ").strip()
            if heading in ("Schema", "Descriptive statistics", "Overview"):
                cells.append(_markdown_cell(section_str))

        if not tool_trace:
            # No trace available (e.g. older callers) -- fall back to the
            # plain narrative rendering instead of silently omitting sections.
            for section_str in rendered_sections:
                heading = section_str.split("\n", 1)[0].lstrip("# ").strip()
                if heading not in ("Schema", "Descriptive statistics", "Overview"):
                    cells.append(_markdown_cell(section_str))
        else:
            chart_idx = 0
            for call in tool_trace:
                tool = call.get("tool", "")
                args = call.get("input", {})
                source = _format_call(tool, args)
                cells.append(_markdown_cell(f"### Tool call: `{tool}`"))

                if tool == "render_charts":
                    cells.append({
                        "cell_type": "code", "id": uuid.uuid4().hex[:8], "execution_count": None,
                        "metadata": {}, "source": source, "outputs": [],
                    })
                    n = len(args.get("chart_specs", [])) or len(charts) - chart_idx
                    for chart in charts[chart_idx:chart_idx + n] or charts:
                        chart_title = chart.get("title", chart.get("chart_id", "chart"))
                        cells.append(_chart_output_cell(f"# output of render_charts: {chart_title}", chart, out_path))
                    chart_idx += n
                elif tool in _RESULT_FROM_SECTION:
                    result = sections_raw.get(_RESULT_FROM_SECTION[tool], "")
                    result_text = "\n".join(f"- {r}" for r in result) if isinstance(result, list) else str(result)
                    cells.append(_text_output_cell(source, result_text))
                else:
                    cells.append({
                        "cell_type": "code", "id": uuid.uuid4().hex[:8], "execution_count": None,
                        "metadata": {}, "source": source, "outputs": [],
                    })

        notebook = {
            "cells": cells,
            "metadata": {"language_info": {"name": "python"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        file_path.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
        return file_path
