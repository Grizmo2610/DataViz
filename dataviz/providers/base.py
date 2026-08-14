from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize the provider.

        Args:
            api_key: Provider API key.
            model: Model identifier.
        """

        self.api_key = api_key
        self.model = model

    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, tool_choice: str = "auto") -> dict[str, Any]:
        """Send a chat request to the provider.

        Args:
            messages: Conversation history.
            tools: Optional tool definitions.
            tool_choice: Tool selection mode.

        Returns:
            Provider response payload.
        """

    @abstractmethod
    def format_tools(self, registry_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert registry entries to provider-specific tool definitions.

        Args:
            registry_entries: Tool registry entries.

        Returns:
            Provider-specific tool payload.
        """

    def __repr__(self) -> str:
        """Return a debug representation of the provider."""

        return f"{self.__class__.__name__}(model={self.model!r})"