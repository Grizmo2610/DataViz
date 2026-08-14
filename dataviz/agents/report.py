from __future__ import annotations

import logging

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext
from dataviz.tools.loader import ToolRegistry

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """Generate narrative sections and assemble the final HTML/PDF report."""

    def __init__(self, tool_registry: ToolRegistry | None = None, provider: object | None = None) -> None:
        super().__init__(tool_registry=tool_registry, provider=provider)

    def run(self, context: PipelineContext) -> AgentResult:
        """Build every report section then write the file via assemble_dashboard.

        If a provider is configured, key sections are enriched with LLM-generated
        narrative; otherwise the rule-based fallbacks are used.
        """
        schema  = context.extra.get("schema", {})
        stats   = context.extra.get("stats", {})
        charts  = context.extra.get("charts", [])
        out_dir = context.extra.get("out_dir", "./dataviz_output")

        # ── Narrative ────────────────────────────────────────────────────────
        summary = self.call_tool("write_summary", schema=schema, stats=stats, lang=context.lang)
        insights = self.call_tool("write_insights", stats=stats, charts=charts, lang=context.lang)
        recommendations = self.call_tool("write_recommendations", insights=insights, lang=context.lang)

        # Optional LLM enrichment
        if self.provider:
            llm_summary = self.ask_llm(
                f"Write a 2-3 sentence executive summary for a dataset with these properties: {summary}. "
                "Be concise and focus on business implications.",
                system="You are a data analyst writing for a non-technical audience.",
            )
            if llm_summary:
                summary = llm_summary

        logger.debug(
            "ReportAgent: summary=%d chars, insights=%d, recs=%d, charts=%d",
            len(summary), len(insights), len(recommendations), len(charts),
        )

        # ── Meta for header ───────────────────────────────────────────────────
        file_names = [p.split("/")[-1] for p in context.file_paths] if context.file_paths else []
        meta = {
            "File": ", ".join(file_names) or "–",
            "Rows": f"{stats.get('row_count', 0):,}",
            "Columns": str(stats.get("column_count", 0)),
            "Charts": str(len(charts)),
        }

        # ── Assemble ─────────────────────────────────────────────────────────
        dashboard = self.call_tool(
            "assemble_dashboard",
            sections={
                "summary":         summary,
                "schema":          schema,
                "stats":           stats,
                "charts":          charts,
                "insights":        insights,
                "recommendations": recommendations,
            },
            template_name="default",
            output_format=context.output_format,
            out_dir=out_dir,
            lang=context.lang,
            meta=meta,
            charts=charts,
        )

        logger.info("ReportAgent: report written to %s", dashboard["output_path"])
        return AgentResult(
            output={"report": dashboard},
            context_updates={"final_output_path": dashboard["output_path"]},
        )