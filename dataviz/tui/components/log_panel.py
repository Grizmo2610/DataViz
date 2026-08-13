from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LogEntry:
    """Represent a single log event."""

    agent: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    def render(self) -> str:
        """Render the log entry as one line."""

        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.agent:<7} {self.message}"


@dataclass
class LogPanel:
    """Collect log entries for the TUI."""

    entries: list[LogEntry] = field(default_factory=list)

    def append(self, entry: LogEntry) -> None:
        """Add a log entry."""

        self.entries.append(entry)

    def render(self) -> str:
        """Render all log entries."""

        return "\n".join(entry.render() for entry in self.entries)
