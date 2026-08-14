from __future__ import annotations

import logging

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext
from dataviz.tools.loader import ToolRegistry

logger = logging.getLogger(__name__)


class VizAgent(BaseAgent):
    """Select charts, then render them to Vega specs using the real DataFrame."""

    def __init__(self, tool_registry: ToolRegistry | None = None, provider: object | None = None) -> None:
        super().__init__(tool_registry=tool_registry, provider=provider)

    def run(self, context: PipelineContext) -> AgentResult:
        """Auto-select chart types, then render each to a Vega-Lite JSON spec.

        Uses ``auto_select_charts`` to decide which chart types suit the data,
        then ``render_charts`` to produce actual Altair/Vega specs.  The rendered
        list is stored in context so ReportAgent can embed it.
        """
        schema = context.extra.get("schema", {})
        stats  = context.extra.get("stats", {})
        df     = context.extra.get("sample_df")

        # 1. Decide which charts to draw
        chart_specs = self.call_tool(
            "auto_select_charts",
            schema=schema,
            stats=stats,
            mode=context.mode,
        )
        logger.debug("VizAgent: selected %d chart specs", len(chart_specs))

        # 2. Render specs → Vega JSON (needs the DataFrame)
        rendered_charts: list[dict] = []
        if df is not None and not df.empty:
            rendered_charts = self.call_tool("render_charts", chart_specs=chart_specs, df=df)
            ok  = sum(1 for c in rendered_charts if not c.get("error"))
            err = len(rendered_charts) - ok
            logger.debug("VizAgent: rendered %d charts (%d ok, %d error)", len(rendered_charts), ok, err)
        else:
            logger.warning("VizAgent: no DataFrame in context — skipping render, returning spec metadata only")
            rendered_charts = chart_specs  # fall back to metadata stubs

        return AgentResult(
            output={"charts": rendered_charts},
            context_updates={"charts": rendered_charts},
        )