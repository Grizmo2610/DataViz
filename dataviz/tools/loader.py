from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Callable


REGISTRY_PATH = Path(__file__).with_name("registry.json")


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not present in the registry."""


class ToolRegistry:
    """Load tools from the registry JSON file.

    The registry is intentionally simple in phase 0. Later phases can
    populate the JSON file with built-in and generated tools without
    changing the interface.
    """

    def __init__(self, registry_path: Path | None = None) -> None:
        """Initialize the registry and load tool metadata.

        Args:
            registry_path: Optional override path for the registry JSON file.
        """

        self._registry_path = registry_path or REGISTRY_PATH
        self._tools: dict[str, Callable[..., Any]] = {}
        self._registry: list[dict[str, Any]] = []
        self._load_all()

    def _load_all(self) -> None:
        """Load all registered tools from disk."""

        if not self._registry_path.exists():
            return

        data = json.loads(self._registry_path.read_text(encoding="utf-8"))
        for entry in data.get("tools", []):
            self._registry.append(entry)
            module = importlib.import_module(entry["module"])
            self._tools[entry["name"]] = getattr(module, entry["name"])

    def get(self, name: str) -> Callable[..., Any]:
        """Return a tool callable by name.

        Args:
            name: Registered tool name.

        Returns:
            The callable associated with the tool.

        Raises:
            ToolNotFoundError: If the tool is not registered.
        """

        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

    def list_for_agent(self, agent: str) -> list[dict[str, Any]]:
        """List all tools owned by an agent.

        Args:
            agent: Agent name such as `reader`, `eda`, `viz`, or `report`.

        Returns:
            A list of tool registry entries.
        """

        return [entry for entry in self._registry if entry.get("agent") == agent]

    def register_generated(self, entry: dict[str, Any], fn: Callable[..., Any]) -> None:
        """Register a generated tool in memory.

        Args:
            entry: Tool registry entry.
            fn: Generated callable.
        """

        self._registry.append(entry)
        self._tools[entry["name"]] = fn
