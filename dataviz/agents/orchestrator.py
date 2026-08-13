from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dataviz.agents.base import AgentResult, BaseAgent, PipelineContext
from dataviz.providers import BaseProvider
from dataviz.tools.loader import ToolRegistry


@dataclass
class PipelineState:
    """Hold the output of the pipeline stages."""

    context: PipelineContext
    results: dict[str, Any]


def run_agent_with_retry(agent: BaseAgent, context: PipelineContext, max_retries: int = 3) -> AgentResult:
    """Run an agent with a simple retry loop."""

    last_error: Exception | None = None
    for _ in range(max_retries):
        try:
            return agent.run(context)
        except Exception as exc:  # pragma: no cover - simple retry shell
            last_error = exc
    if last_error is not None:
        raise last_error
    return AgentResult()


class Orchestrator:
    """Coordinate the agents for the pipeline."""

    def __init__(self, provider: BaseProvider | None = None, tool_registry: ToolRegistry | None = None) -> None:
        """Initialize the orchestrator."""

        self.provider = provider
        self.tool_registry = tool_registry or ToolRegistry()

    def run(self, context: PipelineContext) -> PipelineState:
        """Run the pipeline and collect results."""

        from .eda import EDAAgent
        from .reader import ReaderAgent
        from .report import ReportAgent
        from .viz import VizAgent

        reader = ReaderAgent(tool_registry=self.tool_registry)
        eda = EDAAgent(tool_registry=self.tool_registry)
        viz = VizAgent(tool_registry=self.tool_registry)
        report = ReportAgent(tool_registry=self.tool_registry)

        results: dict[str, Any] = {}
        reader_result = run_agent_with_retry(reader, context)
        results["reader"] = reader_result.output
        context.extra.update(reader_result.context_updates)

        eda_result = run_agent_with_retry(eda, context)
        results["eda"] = eda_result.output
        context.extra.update(eda_result.context_updates)

        viz_result = run_agent_with_retry(viz, context)
        results["viz"] = viz_result.output
        context.extra.update(viz_result.context_updates)

        report_result = run_agent_with_retry(report, context)
        results["report"] = report_result.output
        context.extra.update(report_result.context_updates)
        return PipelineState(context=context, results=results)
