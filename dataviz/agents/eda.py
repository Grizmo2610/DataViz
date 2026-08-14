from __future__ import annotations

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext
from dataviz.tools.loader import ToolRegistry


class EDAAgent(BaseAgent):
    """Compute descriptive EDA outputs."""

    def __init__(self, tool_registry: ToolRegistry | None = None, provider: object | None = None) -> None:
        """Initialize the EDA agent."""

        super().__init__(tool_registry=tool_registry, provider=provider)

    def run(self, context: PipelineContext) -> AgentResult:
        """Compute EDA summaries from the sampled data."""

        sample_df = context.extra.get("sample_df")
        if sample_df is None:
            return AgentResult(output={}, context_updates={})
        return AgentResult(
            output={
                "descriptive_stats": self.call_tool("compute_descriptive_stats", sample_df),
                "nulls": self.call_tool("detect_nulls", sample_df),
                "correlation": self.call_tool("compute_correlation", sample_df, method="pearson"),
                "time_series": self.call_tool("detect_time_series", sample_df),
                "categorical": self.call_tool("detect_categorical_distributions", sample_df),
            },
            context_updates={"eda": True},
        )