from __future__ import annotations

import unittest

from dataviz.agents.base import PipelineContext
from dataviz.cli import should_launch_tui
from dataviz.tui import DatavizApp


class TuiTests(unittest.TestCase):
    """Verify the TUI data model and launch gate."""

    def test_should_launch_tui_respects_flag(self) -> None:
        """The TUI should not launch when disabled."""

        self.assertFalse(should_launch_tui(True))

    def test_dashboard_renders(self) -> None:
        """The dashboard should render the expected sections."""

        app = DatavizApp(
            context=PipelineContext(
                file_paths=["sales.csv"],
                output_format="html",
                extra={
                    "schema": {"columns": [{"name": "revenue"}], "row_count": 10},
                    "stats": {"revenue": {"mean": 10}},
                    "charts": [{"chart_type": "histogram", "chart_id": "histogram_revenue"}],
                    "out_dir": "./dataviz_output",
                },
            )
        )
        rendered = app.dashboard().render()
        self.assertIn("DataViz Dashboard", rendered)
        self.assertIn("Progress", rendered)
        self.assertIn("Logs", rendered)

    def test_chart_selector_toggle(self) -> None:
        """Chart selection should toggle entries by index."""

        app = DatavizApp(
            context=PipelineContext(
                file_paths=["sales.csv"],
                output_format="html",
                extra={"charts": [{"chart_type": "histogram", "chart_id": "histogram_revenue"}]},
            )
        )
        selector = app.chart_selector()
        self.assertIn("[ ]", selector.render())
        selector.toggle(0)
        self.assertIn("[x]", selector.render())

    def test_chart_preview_renders(self) -> None:
        """Chart preview should summarize the selected chart."""

        app = DatavizApp(
            context=PipelineContext(
                file_paths=["sales.csv"],
                output_format="html",
                extra={"charts": [{"chart_type": "histogram", "chart_id": "histogram_revenue"}]},
            )
        )
        rendered = app.chart_preview().render()
        self.assertIn("Chart Preview", rendered)


if __name__ == "__main__":
    unittest.main()
