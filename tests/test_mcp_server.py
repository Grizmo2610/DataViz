from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from dataviz import mcp_server
from dataviz.mcp_server import ToolError


def _make_csv(directory: Path) -> str:
    """Write a small mixed-type CSV and return its path.

    Args:
        directory: Directory to write into.

    Returns:
        Path to the CSV file as a string.
    """

    frame = pd.DataFrame(
        {
            "age": [21, 35, 42, 29, 51, 38, 27, 60],
            "income": [30.5, 52.0, 61.2, 40.1, 75.9, 58.4, 35.0, 80.2],
            "city": ["A", "B", "A", "C", "B", "A", "C", "B"],
            "signup": pd.date_range("2024-01-01", periods=8, freq="D"),
        }
    )
    path = directory / "sample.csv"
    frame.to_csv(path, index=False)
    return str(path)


class McpServerTests(unittest.TestCase):
    """Verify the MCP server tool functions."""

    def setUp(self) -> None:
        """Create a temp directory with a sample CSV."""

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.csv = _make_csv(self.tmp)

    def test_all_tools_are_registered(self) -> None:
        """The server should expose the five documented tools."""

        import asyncio

        tools = asyncio.run(mcp_server.mcp.list_tools())
        names = {t.name for t in tools}
        self.assertEqual(
            names,
            {"inspect_dataset", "analyze_dataset", "suggest_charts", "render_chart", "export_report"},
        )

    def test_inspect_dataset_returns_schema_and_sample(self) -> None:
        """inspect_dataset should return JSON-safe schema and sample rows."""

        result = mcp_server.inspect_dataset(self.csv, n_rows=3)
        self.assertEqual(result["schema"]["row_count"], 8)
        self.assertEqual(len(result["sample"]), 3)
        json.dumps(result)

    def test_inspect_dataset_missing_file(self) -> None:
        """A missing file should raise a ToolError naming the file."""

        with self.assertRaisesRegex(ToolError, "File not found"):
            mcp_server.inspect_dataset(str(self.tmp / "nope.csv"))

    def test_analyze_dataset_sections(self) -> None:
        """analyze_dataset should honour the requested sections."""

        result = mcp_server.analyze_dataset(self.csv, sections=["stats", "nulls"])
        self.assertEqual(set(result), {"stats", "nulls"})
        self.assertIn("age", result["stats"])
        json.dumps(result)

    def test_analyze_dataset_unknown_section(self) -> None:
        """An unknown section should raise ToolError."""

        with self.assertRaises(ToolError):
            mcp_server.analyze_dataset(self.csv, sections=["bogus"])

    def test_suggest_charts_includes_histogram_and_boxplot(self) -> None:
        """suggest_charts should propose histograms and a boxplot for this data."""

        specs = mcp_server.suggest_charts(self.csv)
        kinds = {s["chart_type"] for s in specs}
        self.assertIn("histogram", kinds)
        self.assertIn("boxplot", kinds)

    def test_render_chart_writes_svg(self) -> None:
        """render_chart should save an SVG file when a backend is available."""

        out = str(self.tmp / "out")
        result = mcp_server.render_chart(self.csv, "histogram", column="age", out_dir=out)
        self.assertEqual(result["chart_type"], "histogram")
        self.assertIn("age", result["columns_used"])
        if result["svg_path"] is not None:
            self.assertTrue(Path(result["svg_path"]).is_file())

    def test_render_chart_rejects_unknown_type(self) -> None:
        """An unknown chart type should raise ToolError."""

        with self.assertRaises(ToolError):
            mcp_server.render_chart(self.csv, "sunburst", column="age")

    def test_render_chart_reports_bad_column(self) -> None:
        """A missing column should surface as ToolError, not a silent success."""

        with self.assertRaises(ToolError):
            mcp_server.render_chart(self.csv, "histogram", column="does_not_exist", out_dir=str(self.tmp))

    def test_export_report_html_and_md(self) -> None:
        """export_report should write HTML and Markdown reports."""

        for fmt, name in (("html", "report.html"), ("md", "report.md")):
            out = self.tmp / f"report_{fmt}"
            result = mcp_server.export_report(self.csv, output_format=fmt, out_dir=str(out))
            self.assertTrue(Path(result["output_path"]).is_file(), fmt)
            self.assertEqual(Path(result["output_path"]).name, name)
            self.assertGreater(result["charts_rendered"], 0)

    def test_export_report_rejects_bad_format(self) -> None:
        """An unsupported output format should raise ToolError."""

        with self.assertRaises(ToolError):
            mcp_server.export_report(self.csv, output_format="docx")


if __name__ == "__main__":
    unittest.main()
