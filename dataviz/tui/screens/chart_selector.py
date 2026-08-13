from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChartSelectorScreen:
    """Present generated charts for selection."""

    charts: list[dict[str, Any]] = field(default_factory=list)
    selected: set[int] = field(default_factory=set)

    def toggle(self, index: int) -> None:
        """Toggle chart selection by index."""

        if index in self.selected:
            self.selected.remove(index)
        else:
            self.selected.add(index)

    def render(self) -> str:
        """Render the chart selector as text."""

        lines = [f"Charts ({len(self.charts)} total)"]
        for index, chart in enumerate(self.charts):
            mark = "x" if index in self.selected else " "
            lines.append(f"[{mark}] {chart.get('chart_type', 'chart')} - {chart.get('chart_id', index)}")
        return "\n".join(lines)
