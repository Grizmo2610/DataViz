from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseExporter(ABC):
    """Abstract base class for report exporters."""

    @abstractmethod
    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a single template section.

        Args:
            section: Template section definition.
            content: Section content payload.

        Returns:
            Rendered section markup.
        """

    @abstractmethod
    def write(self, rendered_sections: list[str], out_dir: str | Path, **kwargs: Any) -> Path:
        """Write rendered sections to an output file.

        Args:
            rendered_sections: Rendered section fragments.
            out_dir: Output directory.
            **kwargs: Extra exporter options.

        Returns:
            Path to the final output file.
        """
