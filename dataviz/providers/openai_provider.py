from __future__ import annotations

from typing import Any

from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """Stub provider for OpenAI-compatible chat workflows."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        """Initialize the provider.

        Args:
            api_key: Provider API key.
            model: Model identifier.
            base_url: Optional endpoint override.
        """

        super().__init__(api_key, model)
        self.base_url = base_url

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, tool_choice: str = "auto") -> dict[str, Any]:
        """Return a deterministic placeholder response.

        Args:
            messages: Conversation history.
            tools: Optional tool definitions.
            tool_choice: Tool selection mode.

        Returns:
            A simple response payload.
        """

        return {"content": "", "tool_calls": [], "finish_reason": "stop"}

    def format_tools(self, registry_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format registry entries as OpenAI tool definitions.

        Args:
            registry_entries: Tool registry entries.

        Returns:
            OpenAI tool payloads.
        """

        formatted: list[dict[str, Any]] = []
        for entry in registry_entries:
            properties = {arg: {"type": "string"} for arg in entry["args"]}
            formatted.append(
                {
                    "type": "function",
                    "function": {
                        "name": entry["name"],
                        "description": entry["description"],
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": entry["args"],
                        },
                    },
                }
            )
        return formatted
