from __future__ import annotations

from dataclasses import dataclass

from dataviz.agents.base import PipelineContext

from ..components.log_panel import LogPanel
from ..components.progress import ProgressBoard


@dataclass
class DashboardScreen:
    """Render the main dashboard summary."""

    context: PipelineContext
    progress_board: ProgressBoard
    log_panel: LogPanel

    def render(self) -> str:
        """Render a compact dashboard view."""

        schema = self.context.extra.get("schema", {})
        stats = self.context.extra.get("stats", {})
        lines = [
            f"DataViz Dashboard - {self.context.file_paths[0] if self.context.file_paths else '(no file)'}",
            "",
            "Schema",
            f"Columns: {len(schema.get('columns', []))}",
            f"Rows: {schema.get('row_count', 0)}",
            "",
            "Stats",
            f"Keys: {len(stats)}",
            "",
            "Progress",
            self.progress_board.render(),
            "",
            "Logs",
            self.log_panel.render() or "(no events)",
        ]
        return "\n".join(lines)
