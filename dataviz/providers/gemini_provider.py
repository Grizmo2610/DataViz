from __future__ import annotations

from typing import Any

from .base import BaseProvider


class GeminiProvider(BaseProvider):
    """Stub provider for Gemini chat workflows."""

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, tool_choice: str = "auto") -> dict[str, Any]:
        """Return a deterministic placeholder response."""

        return {"content": "", "tool_calls": [], "finish_reason": "stop"}

    def format_tools(self, registry_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Format registry entries for Gemini-style function calls."""

        return [
            {
                "name": entry["name"],
                "description": entry["description"],
                "parameters": {
                    "type": "object",
                    "properties": {arg: {"type": "string"} for arg in entry["args"]},
                    "required": entry["args"],
                },
            }
            for entry in registry_entries
        ]
