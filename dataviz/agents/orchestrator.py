from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext
from dataviz.providers import BaseProvider
from dataviz.tools.loader import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class PipelineState:
    """Hold the output of the pipeline stages."""

    context: PipelineContext
    results: dict[str, Any]


def run_agent_with_retry(
    agent: BaseAgent,
    context: PipelineContext,
    max_retries: int = 3,
) -> AgentResult:
    """Run an agent with a simple retry loop.

    Args:
        agent: Agent instance to execute.
        context: Shared pipeline context.
        max_retries: Maximum number of attempts before re-raising.

    Returns:
        The agent result.

    Raises:
        Exception: The last exception raised after all retries are exhausted.
    """

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return agent.run(context)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning(
                "%s attempt %d/%d failed: %s",
                type(agent).__name__,
                attempt,
                max_retries,
                exc,
            )
    if last_error is not None:
        raise last_error
    return AgentResult()


class Orchestrator:
    """Coordinate the agents for the pipeline."""

    def __init__(
        self,
        provider: BaseProvider | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            provider: LLM provider shared across all agents. When provided,
                agents can use it for narrative generation via ``ask_llm``.
            tool_registry: Shared tool registry. A default registry is created
                when omitted.
        """

        self.provider = provider
        self.tool_registry = tool_registry or ToolRegistry()

    def _make_agent(self, agent_cls: type) -> BaseAgent:
        """Instantiate an agent with the shared registry and provider.

        Args:
            agent_cls: Agent class to instantiate.

        Returns:
            Configured agent instance.
        """

        return agent_cls(
            tool_registry=self.tool_registry,
            provider=self.provider,
        )

    def run(self, context: PipelineContext) -> PipelineState:
        """Run the full pipeline and collect results.

        Stages run in order: Reader → EDA → Viz → Report.
        Each stage's ``context_updates`` are merged into the shared context
        before the next stage begins.

        Args:
            context: Initial pipeline context.

        Returns:
            A :class:`PipelineState` with the final context and all stage outputs.
        """

        from .eda import EDAAgent
        from .reader import ReaderAgent
        from .report import ReportAgent
        from .viz import VizAgent

        stages: list[tuple[str, type]] = [
            ("reader", ReaderAgent),
            ("eda", EDAAgent),
            ("viz", VizAgent),
            ("report", ReportAgent),
        ]

        results: dict[str, Any] = {}
        for stage_name, agent_cls in stages:
            agent = self._make_agent(agent_cls)
            logger.debug("Orchestrator: running stage '%s' with provider=%r", stage_name, self.provider)
            result = run_agent_with_retry(agent, context)
            results[stage_name] = result.output
            context.extra.update(result.context_updates)

        return PipelineState(context=context, results=results)