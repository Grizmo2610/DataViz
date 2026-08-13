from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseExporter


class NotebookExporter(BaseExporter):
    """Write a minimal notebook report."""

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a section as notebook markdown."""

        title = section.get("title", section.get("id", "Section"))
        return f"## {title}\n\n{content}"

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
