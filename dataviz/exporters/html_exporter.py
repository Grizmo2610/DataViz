from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseExporter


class HtmlExporter(BaseExporter):
    """Write a simple self-contained HTML report."""

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a section as HTML."""

        title = section.get("title", section.get("id", "Section"))
        if isinstance(content, dict):
            body = f"<pre>{content}</pre>"
        elif isinstance(content, list):
            body = "<ul>" + "".join(f"<li>{item}</li>" for item in content) + "</ul>"
        else:
            body = f"<p>{content}</p>"
        return f"<section><h2>{title}</h2>{body}</section>"

    def write(self, rendered_sections: list[str], out_dir: str | Path, **kwargs: Any) -> Path:
        """Write the HTML report to disk."""

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "report.html"
        body = "\n".join(rendered_sections)
        file_path.write_text(
            f"<!doctype html><html><head><meta charset='utf-8'><title>DataViz Report</title></head><body>{body}</body></html>",
            encoding="utf-8",
        )
        return file_path
