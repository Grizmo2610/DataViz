from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dataviz.agents.base import PipelineContext

from .components.log_panel import LogEntry, LogPanel
from .components.progress import AgentProgress, ProgressBoard
from .screens.chart_preview import ChartPreviewScreen
from .screens.chart_selector import ChartSelectorScreen
from .screens.dashboard import DashboardScreen
from .screens.export import ExportScreen
from .screens.insight import InsightScreen


@dataclass
class DatavizApp:
    """Hold TUI state and screen routing data."""

    context: PipelineContext
    state: dict[str, Any] = field(default_factory=dict)
    progress_board: ProgressBoard = field(default_factory=ProgressBoard)
    log_panel: LogPanel = field(default_factory=LogPanel)

    def __post_init__(self) -> None:
        """Seed default progress and log state."""

        self.progress_board.ensure_default_agents()

    def log(self, agent: str, message: str) -> None:
        """Append an event to the log panel.

        Args:
            agent: Name of the agent or component.
            message: Event message.
        """

        self.log_panel.append(LogEntry(agent=agent, message=message))

    def dashboard(self) -> DashboardScreen:
        """Return the dashboard screen model."""

        return DashboardScreen(context=self.context, progress_board=self.progress_board, log_panel=self.log_panel)

    def chart_selector(self) -> ChartSelectorScreen:
        """Return the chart selector screen model."""

        charts = list(self.context.extra.get("charts", []))
        return ChartSelectorScreen(charts=charts)

    def chart_preview(self, index: int = 0) -> ChartPreviewScreen:
        """Return the chart preview screen model."""

        charts = list(self.context.extra.get("charts", []))
        chart = charts[index] if 0 <= index < len(charts) else None
        return ChartPreviewScreen(chart=chart)

    def insight(self) -> InsightScreen:
        """Return the insight screen model."""

        return InsightScreen(insights=self.state.get("insights", ""))

    def export(self) -> ExportScreen:
        """Return the export screen model."""

        return ExportScreen(output_dir=self.context.extra.get("out_dir", "./dataviz_output"))
