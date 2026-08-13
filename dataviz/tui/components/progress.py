from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentProgress:
    """Track a single agent's progress."""

    name: str
    percent: int = 0
    status: str = "pending"

    def advance(self, percent: int, status: str | None = None) -> None:
        """Update the progress entry."""

        self.percent = max(0, min(100, percent))
        if status is not None:
            self.status = status


@dataclass
class ProgressBoard:
    """Manage progress entries for all agents."""

    agents: dict[str, AgentProgress] = field(default_factory=dict)

    def ensure_default_agents(self) -> None:
        """Create the standard agent entries if they are missing."""

        for name in ("Reader", "EDA", "Viz", "Report"):
            self.agents.setdefault(name, AgentProgress(name=name))

    def update(self, name: str, percent: int, status: str | None = None) -> None:
        """Update or create an agent entry."""

        self.agents.setdefault(name, AgentProgress(name=name)).advance(percent, status=status)

    def render(self) -> str:
        """Render a text summary of progress."""

        lines = []
        for entry in self.agents.values():
            bars = "█" * (entry.percent // 10)
            bars = bars.ljust(10, "░")
            lines.append(f"{entry.name:<7} {bars} {entry.percent:>3}% {entry.status}")
        return "\n".join(lines)
