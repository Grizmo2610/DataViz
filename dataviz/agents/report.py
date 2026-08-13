from __future__ import annotations

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext
from dataviz.tools.loader import ToolRegistry


class ReportAgent(BaseAgent):
    """Generate narrative sections and assemble a report."""

    def __init__(self, tool_registry: ToolRegistry | None = None) -> None:
        """Initialize the report agent."""

        super().__init__(tool_registry=tool_registry)

    def run(self, context: PipelineContext) -> AgentResult:
        """Create the final report sections."""

        schema = context.extra.get("schema", {})
        stats = context.extra.get("stats", {})
        charts = context.extra.get("charts", [])
        summary = self.call_tool("write_summary", schema=schema, stats=stats, lang=context.lang)
        insights = self.call_tool("write_insights", stats=stats, charts=charts, lang=context.lang)
        recommendations = self.call_tool("write_recommendations", insights=insights, lang=context.lang)
        dashboard = self.call_tool(
            "assemble_dashboard",
            sections={
                "summary": summary,
                "insights": insights,
                "recommendations": recommendations,
                "schema": schema,
                "stats": stats,
                "charts": charts,
            },
            template_name="default",
            output_format=context.output_format,
            out_dir=context.extra.get("out_dir", "./dataviz_output"),
            lang=context.lang,
        )
        return AgentResult(output={"report": dashboard}, context_updates={"final_output_path": dashboard["output_path"]})
