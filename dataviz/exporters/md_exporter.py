from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseExporter
from .chart_render import chart_to_data_uri


class MdExporter(BaseExporter):
    """Write a Markdown report.

    Charts are embedded as real ``<img>`` tags pointing at the actual SVG
    files ``render_charts`` saved to ``<out_dir>/charts/*.svg`` (via its
    ``image_path`` field) -- not re-derived from the in-memory vega_spec
    after the fact. Tabular sections (schema/stats) are rendered as real
    HTML ``<table>`` markup embedded inline, which every Markdown renderer
    (GitHub, VS Code, Jupyter, mkdocs, ...) displays as an actual table.
    """

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a section as Markdown."""

        title = section.get("title", section.get("id", "Section"))
        section_id = section.get("id", "")

        if section_id == "charts":
            body = self._render_charts(content)
        elif section_id in ("schema", "stats") and isinstance(content, dict) and isinstance(content.get("columns"), list):
            body = self._render_table(content["columns"])
        elif isinstance(content, dict):
            body = "\n".join(f"- **{key}**: {value}" for key, value in content.items())
        elif isinstance(content, list):
            body = "\n".join(f"- {item}" for item in content)
        else:
            body = str(content)
        return f"## {title}\n\n{body}\n"

    def _render_table(self, columns: list[dict[str, Any]]) -> str:
        """Render a list of column-detail dicts as a real HTML table."""
        if not columns:
            return "_No columns._"

        # Union of keys across all rows, "name" first if present.
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

    def _render_charts(self, charts: list[dict[str, Any]]) -> str:
        """Embed every rendered chart as a real image.

        Prefers the actual SVG file ``render_charts`` saved to disk
        (``chart["image_path"]``, relative to the report's out_dir --
        referenced directly so the browser/viewer loads the real file).
        Falls back to re-deriving a base64 data URI from the in-memory
        vega_spec only if no file was saved (e.g. no SVG backend was
        available at chart-creation time), and finally to a text note.
        """
        if not charts:
            return "_No charts generated._"

        blocks: list[str] = []
        for chart in charts:
            title = chart.get("title", chart.get("chart_id", "Chart"))
            if chart.get("error"):
                blocks.append(f"**{title}** \u2014 could not be rendered: {chart['error']}")
                continue

            image_path = chart.get("image_path")
            if image_path:
                blocks.append(f'**{title}**\n\n<img src="{image_path}" alt="{title}" width="600" />')
                continue

            vega_spec = chart.get("vega_spec")
            data_uri = chart_to_data_uri(vega_spec) if vega_spec else None
            if data_uri:
                blocks.append(f'**{title}**\n\n<img src="{data_uri}" alt="{title}" width="600" />')
            else:
                blocks.append(
                    f"**{title}** \u2014 could not be rendered "
                    "(no working SVG backend: altair/vl-convert-python/matplotlib)."
                )
        return "\n\n".join(blocks)

    def write(self, rendered_sections: list[str], out_dir: str | Path, **kwargs: Any) -> Path:
        """Write the Markdown report to disk."""

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "report.md"
        file_path.write_text("\n".join(rendered_sections), encoding="utf-8")
        return file_path
