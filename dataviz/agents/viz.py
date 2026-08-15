from __future__ import annotations

import json

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext, log
from dataviz.tools.loader import ToolRegistry


class VizAgent(BaseAgent):
    def __init__(self, tool_registry: ToolRegistry | None = None, provider: object | None = None) -> None:
        super().__init__(tool_registry=tool_registry, provider=provider)

    def run(self, context: PipelineContext) -> AgentResult:
        if self.provider is None:
            raise RuntimeError(
                "[VizAgent] No LLM provider configured. "
                "Run: dataviz config set --provider <name> --key <key>"
            )

        schema = context.extra.get("schema", {})
        stats  = context.extra.get("stats", {})
        df     = context.extra.get("sample_df")
        mode   = getattr(context, "mode", "default")

        if df is None:
            raise RuntimeError(
                "[VizAgent] No sample_df in context -- cannot render charts. "
                "ReaderAgent must run before VizAgent."
            )

        log.debug("[VizAgent] run  schema_cols=%d  stats_rows=%s  df=%s",
                  len(schema.get("columns", [])), stats.get("row_count"),
                  f"DataFrame{df.shape}")

        # NOTE: Tools that require a DataFrame or schema/stats receive them via
        # context_data injection in run_agentic. The LLM never passes these directly.
        initial_prompt = (
            f"You are selecting and rendering charts for a dataset.\n\n"
            f"Dataset schema: {json.dumps(schema, default=str)}\n\n"
            f"EDA statistics: {json.dumps(stats, default=str)}\n\n"
            f"Visualization mode: {mode}\n\n"
            f"Steps:\n"
            f"1. Call auto_select_charts with no arguments -- schema and stats are "
            f"injected automatically.\n"
            f"2. Call render_charts passing the chart specs returned by auto_select_charts.\n\n"
            f"IMPORTANT: Do NOT pass 'df', 'schema', or 'stats' arguments -- they are "
            f"injected automatically.\n\n"
            f"After both tool calls are complete, respond with a single JSON object "
            f"(no markdown, no extra text) with exactly this key:\n"
            f'  {{"charts": [<rendered chart objects>]}}'
        )
        system = (
            "You are a data visualization agent. Call auto_select_charts first, then "
            "render_charts with the returned specs. Never pass 'df', 'schema', or "
            "'stats' -- they are injected automatically."
        )

        log.debug("[VizAgent] starting agent loop")
        raw = self.run_agentic(
            initial_prompt=initial_prompt,
            system=system,
            agent_name="viz",
            max_turns=8,
            context_data={"df": df, "schema": schema, "stats": stats, "mode": mode},
        )

        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            results: dict = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(
                f"[VizAgent] Agent returned non-JSON output: {exc}\nRaw: {raw[:400]}"
            ) from exc

        charts = results.get("charts", [])
        if not isinstance(charts, list):
            raise RuntimeError(
                f"[VizAgent] Agent output 'charts' must be a list, got {type(charts).__name__}."
            )

        ok  = sum(1 for c in charts if c.get("vega_spec") and not c.get("error"))
        err = len(charts) - ok
        log.debug("[VizAgent] run complete  charts=%d  ok=%d  error=%d", len(charts), ok, err)

        return AgentResult(
            output={"charts": charts},
            context_updates={"charts": charts},
        )