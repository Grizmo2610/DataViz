from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseExporter
from .chart_render import chart_to_data_uri


class NotebookExporter(BaseExporter):
    """Write a minimal notebook report."""

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a section as notebook markdown."""

        title = section.get("title", section.get("id", "Section"))

        if section.get("id") == "charts":
            body = self._render_charts(content)
        elif isinstance(content, dict):
            body = "\n".join(f"- **{key}**: {value}" for key, value in content.items())
        elif isinstance(content, list):
            body = "\n".join(f"- {item}" for item in content)
        else:
            body = str(content)

        return f"## {title}\n\n{body}"

    def _render_charts(self, charts: list[dict[str, Any]]) -> str:
        """Render rendered chart dicts as real images (SVG data URIs).

        Falls back to a plain-text note per chart when no SVG renderer
        backend (Altair/vl-convert) is available, instead of dumping the
        raw vega_spec dict as text.
        """
        if not charts:
            return "_No charts generated._"

        blocks: list[str] = []
        for chart in charts:
            title = chart.get("title", chart.get("chart_id", "Chart"))
            if chart.get("error"):
                blocks.append(f"**{title}** \u2014 could not be rendered: {chart['error']}")
                continue

            vega_spec = chart.get("vega_spec")
            data_uri = chart_to_data_uri(vega_spec) if vega_spec else None
            if data_uri:
                blocks.append(f"**{title}**\n\n![{title}]({data_uri})")
            else:
                blocks.append(f"**{title}** \u2014 no SVG renderer available (install `altair`/`vl-convert-python`).")
        return "\n\n".join(blocks)

    def write(self, rendered_sections: list[str], out_dir: str | Path, **kwargs: Any) -> Path:
        """Write the notebook report to disk."""

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "report.ipynb"
        notebook = {
            "cells": [
                {"cell_type": "markdown", "metadata": {}, "source": section, "outputs": []}
                for section in rendered_sections
            ],
            "metadata": {"language_info": {"name": "python"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        file_path.write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
        return file_path
