from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from dataviz.agents.base import PipelineContext
from dataviz.agents.eda import EDAAgent
from dataviz.agents.viz import VizAgent
from dataviz.agents.report import ReportAgent
from dataviz.agents.orchestrator import Orchestrator


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

EDA_RESULT = {
    "descriptive_stats": {"a": {"mean": 1.5}},
    "nulls": {},
    "correlation": {},
    "time_series": {},
    "categorical": {"b": {"x": 1, "y": 1}},
    "outliers": {},
}
CHARTS_RESULT = {
    "charts": [{"chart_id": "c1", "chart_type": "bar", "vega_spec": {"mark": "bar"}}],
}
REPORT_RESULT = {
    "summary": "Test summary.",
    "insights": ["Insight A"],
    "recommendations": ["Rec A"],
}


def _mock_provider(*turn_jsons) -> MagicMock:
    """Provider whose chat() returns each JSON payload as a single-turn final answer."""
    provider = MagicMock()
    provider.api_key = "sk-fake"
    provider.model = "fake-model"
    provider.format_tools = MagicMock(return_value=[])
    provider.chat = MagicMock(side_effect=[
        {"content": json.dumps(p), "tool_calls": [], "finish_reason": "end_turn"}
        for p in turn_jsons
    ])
    return provider


def _csv(tmp: str, content: str = "a,b\n1,x\n2,y\n") -> str:
    path = Path(tmp) / "data.csv"
    path.write_text(content, encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

class OrchestratorPipelineTests(unittest.TestCase):

    def test_full_pipeline_with_provider(self) -> None:
        """All four stages run and produce a report when a provider is configured."""
        # Each agent gets its own chat() call (single-turn, no tool calls).
        provider = _mock_provider(EDA_RESULT, CHARTS_RESULT, REPORT_RESULT)

        with tempfile.TemporaryDirectory() as tmp:
            orchestrator = Orchestrator(provider=provider)
            state = orchestrator.run(
                PipelineContext(file_paths=[_csv(tmp)], output_format="html", lang="en")
            )

        self.assertIn("report", state.results)
        self.assertTrue(state.context.extra["final_output_path"])

    def test_pipeline_raises_without_provider(self) -> None:
        """RuntimeError must be raised at construction time when no provider is set."""
        with self.assertRaises(RuntimeError) as ctx:
            Orchestrator(provider=None)
        self.assertIn("provider", str(ctx.exception).lower())


# ---------------------------------------------------------------------------
# EDAAgent
# ---------------------------------------------------------------------------

class EDAAgentTests(unittest.TestCase):

    def test_raises_without_provider(self) -> None:
        agent = EDAAgent(provider=None)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        with self.assertRaises(RuntimeError) as cm:
            agent.run(ctx)
        self.assertIn("provider", str(cm.exception).lower())

    def test_raises_without_sample_df(self) -> None:
        provider = _mock_provider()
        agent = EDAAgent(provider=provider)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        with self.assertRaises(RuntimeError) as cm:
            agent.run(ctx)
        self.assertIn("sample_df", str(cm.exception).lower())

    def test_agent_loop_called_and_parsed(self) -> None:
        import pandas as pd
        provider = _mock_provider(EDA_RESULT)
        agent = EDAAgent(provider=provider)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        ctx.extra["sample_df"] = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})

        result = agent.run(ctx)

        self.assertIn("descriptive_stats", result.output)
        self.assertIn("outliers", result.output)
        self.assertTrue(result.context_updates.get("eda"))
        # Provider must have been called (agent loop ran)
        self.assertTrue(provider.chat.called)


# ---------------------------------------------------------------------------
# VizAgent
# ---------------------------------------------------------------------------

class VizAgentTests(unittest.TestCase):

    def test_raises_without_provider(self) -> None:
        agent = VizAgent(provider=None)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        with self.assertRaises(RuntimeError) as cm:
            agent.run(ctx)
        self.assertIn("provider", str(cm.exception).lower())

    def test_raises_without_sample_df(self) -> None:
        provider = _mock_provider()
        agent = VizAgent(provider=provider)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        with self.assertRaises(RuntimeError) as cm:
            agent.run(ctx)
        self.assertIn("sample_df", str(cm.exception).lower())

    def test_agent_loop_called_and_parsed(self) -> None:
        import pandas as pd
        provider = _mock_provider(CHARTS_RESULT)
        agent = VizAgent(provider=provider)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        ctx.extra["sample_df"] = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        ctx.extra["schema"] = {}
        ctx.extra["stats"] = {}

        result = agent.run(ctx)

        self.assertIsInstance(result.output["charts"], list)
        self.assertEqual(len(result.output["charts"]), 1)
        self.assertTrue(provider.chat.called)

    def test_raises_on_non_list_charts(self) -> None:
        import pandas as pd
        bad_result = {"charts": "not-a-list"}
        provider = _mock_provider(bad_result)
        agent = VizAgent(provider=provider)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        ctx.extra["sample_df"] = pd.DataFrame({"a": [1, 2]})
        ctx.extra["schema"] = {}
        ctx.extra["stats"] = {}

        with self.assertRaises(RuntimeError) as cm:
            agent.run(ctx)
        self.assertIn("list", str(cm.exception).lower())


# ---------------------------------------------------------------------------
# ReportAgent
# ---------------------------------------------------------------------------

class ReportAgentTests(unittest.TestCase):

    def test_raises_without_provider(self) -> None:
        agent = ReportAgent(provider=None)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        with self.assertRaises(RuntimeError) as cm:
            agent.run(ctx)
        self.assertIn("provider", str(cm.exception).lower())

    def test_raises_on_missing_summary(self) -> None:
        bad = {"insights": ["x"], "recommendations": ["y"]}  # no "summary"
        provider = _mock_provider(bad)
        agent = ReportAgent(provider=provider)
        ctx = PipelineContext(file_paths=[], output_format="html", lang="en")
        ctx.extra = {"schema": {}, "stats": {}, "charts": [], "out_dir": "/tmp"}

        with self.assertRaises(RuntimeError) as cm:
            agent.run(ctx)
        self.assertIn("summary", str(cm.exception).lower())


if __name__ == "__main__":
    unittest.main()