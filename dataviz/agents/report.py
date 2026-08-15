from __future__ import annotations

import json
import time

from dataviz.agents.base import (
    AgentResult, BaseAgent, LLMMaxTurnsError, PipelineContext, log,
)
from dataviz.tools.loader import ToolRegistry


class ReportAgent(BaseAgent):

    def __init__(self, tool_registry: ToolRegistry | None = None, provider: object | None = None) -> None:
        super().__init__(tool_registry=tool_registry, provider=provider)

    def run(self, context: PipelineContext) -> AgentResult:
        if self.provider is None:
            raise RuntimeError(
                "[ReportAgent] No LLM provider configured. "
                "Run: dataviz config set --provider <name> --key <key>"
            )

        schema    = context.extra.get("schema", {})
        stats     = context.extra.get("stats", {})
        charts    = context.extra.get("charts", [])
        viz_trace = context.extra.get("viz_trace", [])
        out_dir   = context.extra.get("out_dir", "./dataviz_output")

        log.debug(
            "[ReportAgent] run  schema_cols=%d  stats_rows=%s  charts=%d  "
            "out_dir=%r  lang=%s  format=%s",
            len(schema.get("columns", [])), stats.get("row_count"),
            len(charts), out_dir, context.lang, context.output_format,
        )

        # ── Agent loop ────────────────────────────────────────────────────────
        initial_prompt = (
            f"You are analyzing a dataset and must produce a complete report.\n\n"
            f"Dataset schema: {json.dumps(schema, default=str)}\n\n"
            f"EDA statistics: {json.dumps(stats, default=str)}\n\n"
            f"Charts rendered: {json.dumps(charts, default=str)}\n\n"
            f"Language for narrative text: {context.lang}\n\n"
            f"Use the available tools to:\n"
            f"1. Call write_summary to produce a dataset summary.\n"
            f"2. Call write_insights to derive key insights from the stats and charts.\n"
            f"3. Call write_recommendations to produce actionable recommendations.\n\n"
            f"After all three tools have returned results, respond with a single JSON "
            f"object (no markdown, no extra text) with exactly these keys:\n"
            f'  {{"summary": "<string>", "insights": ["<string>", ...], '
            f'"recommendations": ["<string>", ...]}}'
        )
        system = (
            "You are a data analyst agent. Use the tools provided to gather facts, "
            "then produce the final JSON report. Never fabricate numbers — always "
            "call the tools first."
        )

        log.debug("[ReportAgent] starting agent loop")
        report_trace: list[dict] = []
        raw = self.run_agentic(
            initial_prompt=initial_prompt,
            system=system,
            agent_name="report",
            max_turns=10,
            trace_sink=report_trace,
        )
        # Full pipeline trace shown to the notebook exporter: chart-selection/
        # rendering calls from VizAgent, followed by the narrative-writing
        # calls this agent just made.
        tool_trace = list(viz_trace) + report_trace

        # ── Parse agent output ────────────────────────────────────────────────
        try:
            # Strip accidental markdown fences the model may add
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            sections_llm: dict = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(
                f"[ReportAgent] Agent returned non-JSON output: {exc}\nRaw output: {raw[:400]}"
            ) from exc

        summary         = str(sections_llm.get("summary", ""))
        insights        = list(sections_llm.get("insights", []))
        recs            = list(sections_llm.get("recommendations", []))

        if not summary:
            raise RuntimeError("[ReportAgent] Agent output missing 'summary' field.")

        log.debug(
            "[ReportAgent] agent output parsed  summary_len=%d  insights=%d  recs=%d",
            len(summary), len(insights), len(recs),
        )

        # ── Meta ──────────────────────────────────────────────────────────────
        file_names = [p.split("/")[-1].split("\\")[-1] for p in context.file_paths]
        meta = {
            "File":    ", ".join(file_names) or "–",
            "Rows":    f"{stats.get('row_count', 0):,}",
            "Columns": str(stats.get("column_count", 0)),
            "Charts":  str(len(charts)),
        }

        # ── Assemble dashboard ────────────────────────────────────────────────
        sections = {
            "summary":         summary,
            "schema":          schema,
            "stats":           stats,
            "charts":          charts,
            "insights":        insights,
            "recommendations": recs,
        }
        log.debug(
            "[ReportAgent] assemble_dashboard  format=%s  out_dir=%r",
            context.output_format, out_dir,
        )

        t0 = time.monotonic()
        dashboard = self.call_tool(
            "assemble_dashboard",
            sections=sections,
            template_name=context.extra.get("template", "default"),
            output_format=context.output_format,
            out_dir=out_dir,
            lang=context.lang,
            meta=meta,
            charts=charts,
            tool_trace=tool_trace,
        )
        log.debug(
            "[ReportAgent] assemble_dashboard complete  %.3fs  output=%r  sections=%d",
            time.monotonic() - t0,
            dashboard.get("output_path"),
            dashboard.get("sections_rendered", 0),
        )

        return AgentResult(
            output={"report": dashboard},
            context_updates={"final_output_path": dashboard["output_path"]},
        )