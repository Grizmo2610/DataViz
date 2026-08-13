from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ChartPreviewScreen:
    """Render a single chart preview summary."""

    chart: dict[str, Any] | None = None

    def render(self) -> str:
        """Render chart preview text."""

        if not self.chart:
            return "No chart selected."
        return "\n".join(
            [
                f"Chart Preview - {self.chart.get('chart_id', 'unknown')}",
                f"Type: {self.chart.get('chart_type', 'unknown')}",
                f"Engine: {self.chart.get('engine', 'plotly')}",
            ]
        )
