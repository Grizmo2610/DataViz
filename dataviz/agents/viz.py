from __future__ import annotations

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext
from dataviz.tools.loader import ToolRegistry


class VizAgent(BaseAgent):
    """Select chart ideas from the current analysis context."""

    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        """Initialize the Viz agent."""

        super().__init__(tool_registry=tool_registry)

    def run(self, context: PipelineContext) -> AgentResult:
        """Select a simple set of chart ideas."""

        schema = context.extra.get("schema", {})
        stats = context.extra.get("stats", {})
        charts = self.call_tool("auto_select_charts", schema=schema, stats=stats, mode=context.mode)
        return AgentResult(output={"charts": charts}, context_updates={"charts": charts})
