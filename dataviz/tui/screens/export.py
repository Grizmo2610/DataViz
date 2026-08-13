from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExportScreen:
    """Render export options."""

    output_dir: str
    format_name: str = "html"

    def render(self) -> str:
        """Render export details."""

        return "\n".join(
            [
                "Export",
                f"Format: {self.format_name}",
                f"Output dir: {self.output_dir}",
            ]
        )
