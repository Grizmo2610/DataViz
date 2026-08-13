from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from dataviz.tools import reader_tools, eda_tools, report_tools, viz_tools


class ToolTests(unittest.TestCase):
    """Verify built-in tool functions."""

    def test_reader_tools_detect_schema(self) -> None:
        """Schema detection should summarize dataframe columns."""

        frame = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        schema = reader_tools.detect_schema(frame)
        self.assertEqual(schema["row_count"], 2)
        self.assertEqual(schema["column_count"], 2)

    def test_eda_tools_compute_descriptive_stats(self) -> None:
        """Descriptive stats should include numeric columns."""

        frame = pd.DataFrame({"a": [1, 2, 3]})
        stats = eda_tools.compute_descriptive_stats(frame)
        self.assertIn("a", stats)

    def test_viz_tools_auto_select_charts(self) -> None:
        """Chart selection should produce a histogram for numeric columns."""

        charts = viz_tools.auto_select_charts({"columns": [{"name": "a", "dtype": "int64"}]}, {}, "default")
        self.assertEqual(charts[0]["chart_type"], "histogram")

    def test_report_tools_assemble_dashboard(self) -> None:
        """Report assembly should write a file and return its path."""

        with tempfile.TemporaryDirectory() as tmp:
            result = report_tools.assemble_dashboard(
                {"summary": "hello", "insights": "world"},
                "default",
                "html",
                Path(tmp),
                "en",
            )
            self.assertTrue(Path(result["output_path"]).exists())


if __name__ == "__main__":
    unittest.main()
