from __future__ import annotations

import json

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext, log
from dataviz.tools.loader import ToolRegistry


class EDAAgent(BaseAgent):
    def __init__(self, tool_registry: ToolRegistry | None = None, provider: object | None = None) -> None:
        super().__init__(tool_registry=tool_registry, provider=provider)

    def run(self, context: PipelineContext) -> AgentResult:
        if self.provider is None:
            raise RuntimeError(
                "[EDAAgent] No LLM provider configured. "
                "Run: dataviz config set --provider <name> --key <key>"
            )

        sample_df = context.extra.get("sample_df")
        if sample_df is None:
            raise RuntimeError(
                "[EDAAgent] No sample_df in context -- cannot run EDA. "
                "ReaderAgent must run before EDAAgent."
            )

        log.debug("[EDAAgent] run  sample_df=%s", f"DataFrame{sample_df.shape}")

        schema_summary = {
            "columns": list(sample_df.columns),
            "dtypes": {col: str(dtype) for col, dtype in sample_df.dtypes.items()},
            "shape": list(sample_df.shape),
        }

        # NOTE: Tools that require a DataFrame receive it via context_data injection
        # in run_agentic. The LLM calls tools by name only -- it never needs to pass df.
        initial_prompt = (
            f"You are analyzing a dataset for exploratory data analysis.\n\n"
            f"Dataset overview: {json.dumps(schema_summary, default=str)}\n\n"
            f"Call the available EDA tools to fully analyze this dataset.\n"
            f"Available tools: compute_descriptive_stats, detect_nulls, "
            f"compute_correlation, detect_time_series, detect_categorical_distributions, "
            f"detect_outliers.\n\n"
            f"IMPORTANT: Do NOT pass any 'df' argument -- the dataset is injected "
            f"automatically. Just call each tool with no arguments (or only optional "
            f"arguments like 'method' for compute_correlation).\n\n"
            f"After all tool calls are complete, respond with a single JSON object "
            f"(no markdown, no extra text) with exactly these keys:\n"
            f'  {{"descriptive_stats": {{...}}, "nulls": {{...}}, "correlation": {{...}}, '
            f'"time_series": {{...}}, "categorical": {{...}}, "outliers": {{...}}}}'
        )
        system = (
            "You are a data analysis agent. Call the EDA tools to gather facts, "
            "then return a JSON summary. Never pass 'df' -- it is injected automatically. "
            "Never fabricate statistics."
        )

        log.debug("[EDAAgent] starting agent loop")
        raw = self.run_agentic(
            initial_prompt=initial_prompt,
            system=system,
            agent_name="eda",
            max_turns=12,
            context_data={"df": sample_df},
        )

        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            results: dict = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(
                f"[EDAAgent] Agent returned non-JSON output: {exc}\nRaw: {raw[:400]}"
            ) from exc

        outliers = results.get("outliers", {})
        log.debug("[EDAAgent] run complete  output_keys=%s", list(results.keys()))

        return AgentResult(
            output=results,
            context_updates={"eda": True, "eda_outliers": outliers},
        )