from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InsightScreen:
    """Render the insight narrative."""

    insights: str

    def render(self) -> str:
        """Render insight text."""

        return self.insights or "No insights available."
