from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import BaseExporter


class MdExporter(BaseExporter):
    """Write a Markdown report."""

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a section as Markdown."""

        title = section.get("title", section.get("id", "Section"))
        if isinstance(content, dict):
            body = "\n".join(f"- **{key}**: {value}" for key, value in content.items())
        elif isinstance(content, list):
            body = "\n".join(f"- {item}" for item in content)
        else:
            body = str(content)
        return f"## {title}\n\n{body}\n"

    def write(self, rendered_sections: list[str], out_dir: str | Path, **kwargs: Any) -> Path:
        """Write the Markdown report to disk."""

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "report.md"
        file_path.write_text("\n".join(rendered_sections), encoding="utf-8")
        return file_path
