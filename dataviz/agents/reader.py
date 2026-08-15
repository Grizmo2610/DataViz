from __future__ import annotations

import logging
import time

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext, log
from dataviz.readers import get_reader
from dataviz.tools.loader import ToolRegistry


class ReaderAgent(BaseAgent):
    def __init__(self, tool_registry: ToolRegistry | None = None, provider: object | None = None) -> None:
        super().__init__(tool_registry=tool_registry, provider=provider)

    def run(self, context: PipelineContext) -> AgentResult:
        file_path = context.file_paths[0]
        sheet     = context.extra.get("sheet")

        log.debug("[ReaderAgent] run  file=%r  sheet=%r  mode=%s", file_path, sheet, context.mode)

        # ── Get reader ────────────────────────────────────────────────────────
        log.debug("[ReaderAgent] get_reader(%r, sheet=%r)", file_path, sheet)
        t0 = time.monotonic()
        reader = get_reader(file_path, sheet_name=sheet)
        log.debug("[ReaderAgent] reader=%s  %.3fs", type(reader).__name__, time.monotonic() - t0)

        # ── Read sample ───────────────────────────────────────────────────────
        n_sample = 20
        log.debug("[ReaderAgent] read_sample  n_rows=%d", n_sample)
        t0 = time.monotonic()
        sample = reader.read_sample(file_path, n_rows=n_sample)
        log.debug("[ReaderAgent] sample  shape=%s  dtypes=%s  %.3fs",
                  sample.shape,
                  {c: str(t) for c, t in sample.dtypes.items()},
                  time.monotonic() - t0)

        # ── Detect schema ─────────────────────────────────────────────────────
        log.debug("[ReaderAgent] detect_schema  cols=%d", len(sample.columns))
        schema = self.call_tool("detect_schema", sample)
        log.debug("[ReaderAgent] schema  row_count=%s  col_count=%s  cols=%s",
                  schema.get("row_count"), schema.get("column_count"),
                  [c["name"] for c in schema.get("columns", [])])

        # ── Full stats ────────────────────────────────────────────────────────
        log.debug("[ReaderAgent] read_full_stats  file=%r", file_path)
        t0 = time.monotonic()
        stats = reader.read_full_stats(file_path)
        log.debug("[ReaderAgent] stats  row_count=%s  col_count=%s  strategy=%s  %.3fs",
                  stats.get("row_count"), stats.get("column_count"),
                  stats.get("read_strategy"), time.monotonic() - t0)
        log.debug("[ReaderAgent] stats  column_detail=%s",
                  [{c["name"]: {k: v for k, v in c.items() if k != "name"}}
                   for c in stats.get("columns", [])])

        return AgentResult(
            output={"sample_rows": len(sample)},
            context_updates={"schema": schema, "stats": stats, "sample_df": sample},
        )