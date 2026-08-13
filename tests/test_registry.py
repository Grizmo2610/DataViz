from __future__ import annotations

import unittest

from dataviz.tools.loader import ToolNotFoundError, ToolRegistry


class RegistryTests(unittest.TestCase):
    """Verify tool registry loading and lookup."""

    def test_registry_loads_tools(self) -> None:
        """The registry should load registered tools from disk."""

        registry = ToolRegistry()
        self.assertGreater(len(registry.list_for_agent("reader")), 0)
        self.assertGreater(len(registry.list_for_agent("viz")), 0)

    def test_registry_returns_callable(self) -> None:
        """The registry should return callable tool functions."""

        registry = ToolRegistry()
        tool = registry.get("read_sample")
        self.assertTrue(callable(tool))

    def test_registry_raises_for_missing_tool(self) -> None:
        """Missing tools should raise ToolNotFoundError."""

        registry = ToolRegistry()
        with self.assertRaises(ToolNotFoundError):
            registry.get("not_a_real_tool")


if __name__ == "__main__":
    unittest.main()
