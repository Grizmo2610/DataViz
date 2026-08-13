from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseExporter


class PdfExporter(BaseExporter):
    """Write a PDF-like text artifact for environments without a PDF engine."""

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a section for PDF export."""

        title = section.get("title", section.get("id", "Section"))
        return f"{title}\n{content}\n"

    def write(self, rendered_sections: list[str], out_dir: str | Path, **kwargs: Any) -> Path:
        """Write the report payload to a PDF placeholder file.

        The actual PDF engine is introduced in a later cleanup phase.
        """

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "report.pdf"
        file_path.write_text("\n".join(rendered_sections), encoding="utf-8")
        return file_path
