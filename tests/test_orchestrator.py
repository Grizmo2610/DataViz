from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from dataviz.agents.base import PipelineContext
from dataviz.agents.orchestrator import Orchestrator


class OrchestratorTests(unittest.TestCase):
    """Verify the agent pipeline runs end to end."""

    def test_orchestrator_runs_pipeline(self) -> None:
        """The orchestrator should produce a final report path."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            path.write_text("a,b\n1,x\n2,y\n", encoding="utf-8")
            with patch("dataviz.agents.report.ToolRegistry"), patch("dataviz.agents.viz.ToolRegistry"), patch("dataviz.agents.eda.ToolRegistry"), patch("dataviz.agents.reader.ToolRegistry"):
                orchestrator = Orchestrator()
                state = orchestrator.run(PipelineContext(file_paths=[str(path)], output_format="html", lang="en"))

        self.assertIn("report", state.results)
        self.assertTrue(state.context.extra["final_output_path"])


if __name__ == "__main__":
    unittest.main()
