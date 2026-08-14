from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from dataviz.tools.loader import ToolRegistry


@dataclass
class PipelineContext:
    """Shared state passed between pipeline stages.

    Attributes:
        file_paths: Input file paths.
        output_format: Requested output format.
        mode: Analysis mode.
        focus: Optional user focus hint.
        lang: Output language.
        extra: Free-form shared data for future phases.
    """

    file_paths: list[str]
    output_format: str
    mode: str = "default"
    focus: str | None = None
    lang: str = "auto"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Container for agent output and updated context data.

    Attributes:
        output: Agent output payload.
        context_updates: Values to merge into the shared context.
    """

    output: dict[str, Any] = field(default_factory=dict)
    context_updates: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base class for pipeline agents."""

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        provider: Any | None = None,
    ) -> None:
        """Initialize the agent.

        Args:
            tool_registry: Optional tool registry used by the agent.
            provider: Optional LLM provider for narrative generation.
        """

        self.tool_registry = tool_registry or ToolRegistry()
        self.provider = provider

    @abstractmethod
    def run(self, context: PipelineContext) -> AgentResult:
        """Execute the agent against the provided context.

        Args:
            context: Shared pipeline context.

        Returns:
            The agent result.
        """

    def call_tool(self, tool_name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a registered tool.

        Args:
            tool_name: Name of the tool to execute.
            *args: Positional tool arguments.
            **kwargs: Tool keyword arguments.

        Returns:
            The tool return value.
        """

        return self.tool_registry.get(tool_name)(*args, **kwargs)

    def ask_llm(self, prompt: str, system: str | None = None) -> str:
        """Send a prompt to the configured LLM provider and return the text reply.

        Falls back to an empty string when no provider is configured.

        Args:
            prompt: User-turn content.
            system: Optional system message.

        Returns:
            The model's text response, or ``""`` if no provider is available.
        """

        if self.provider is None:
            return ""

        messages: list[dict[str, Any]] = []
        if system:
            # Anthropic puts system at the top-level; other providers may differ.
            # Keep it simple: prepend as a user/assistant round.
            messages.append({"role": "user", "content": f"[System] {system}"})
            messages.append({"role": "assistant", "content": "Understood."})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.provider.chat(messages)
            return response.get("content", "")
        except Exception:  # noqa: BLE001
            return ""