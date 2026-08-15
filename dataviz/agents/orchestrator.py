from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from typing import Any

from dataviz.agents.base import AgentResult, BaseAgent, LLMError, PipelineContext
from dataviz.providers import BaseProvider
from dataviz.tools.loader import ToolRegistry

logger: logging.Logger = logging.getLogger("dataviz")


@dataclass
class PipelineState:
    """Hold the output of the pipeline stages."""
    context: PipelineContext
    results: dict[str, Any]


class Orchestrator:
    """Coordinate the agents for the pipeline.

    Each stage is executed in order: Reader → EDA → Viz → Report.
    A provider is required — without one the pipeline raises immediately
    in __init__. Any agent failure propagates immediately and interrupts
    the pipeline. No silent swallowing, no retries at this level.
    """

    def __init__(
        self,
        provider: BaseProvider | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        if provider is None:
            raise RuntimeError(
                "[Orchestrator] No LLM provider configured. "
                "Run: dataviz config set --provider <name> --key <key>"
            )
        self.provider = provider
        self.tool_registry = tool_registry or ToolRegistry()

    def _make_agent(self, agent_cls: type) -> BaseAgent:
        return agent_cls(
            tool_registry=self.tool_registry,
            provider=self.provider,
        )

    def run(self, context: PipelineContext) -> PipelineState:
        """Run the full pipeline, interrupting immediately on any failure.

        Args:
            context: Initial pipeline context.

        Returns:
            PipelineState with the final context and all stage outputs.

        Raises:
            RuntimeError: Configuration error or agent failure.
            LLMError: Any LLM-layer error from any agent.
        """
        from .eda import EDAAgent
        from .reader import ReaderAgent
        from .report import ReportAgent
        from .viz import VizAgent

        stages: list[tuple[str, type]] = [
            ("reader", ReaderAgent),
            ("eda",    EDAAgent),
            ("viz",    VizAgent),
            ("report", ReportAgent),
        ]

        results: dict[str, Any] = {}
        for stage_name, agent_cls in stages:
            agent = self._make_agent(agent_cls)
            logger.debug(
                "[Orchestrator] stage=%s  provider=%s  model=%s",
                stage_name,
                type(self.provider).__name__,
                getattr(self.provider, "model", "?"),
            )
            try:
                result = agent.run(context)
            except Exception as exc:
                logger.error(
                    "[Orchestrator] stage=%s  ✗ %s: %s\n%s",
                    stage_name, type(exc).__name__, exc, traceback.format_exc(),
                )
                raise

            results[stage_name] = result.output
            context.extra.update(result.context_updates)
            logger.debug("[Orchestrator] stage=%s  ✓ complete", stage_name)

        return PipelineState(context=context, results=results)