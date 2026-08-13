from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dataviz.exporters import get_exporter


class ExporterTests(unittest.TestCase):
    """Verify exporter output files and formats."""

    def test_html_exporter_writes_html(self) -> None:
        """HTML export should create a .html file."""

        with tempfile.TemporaryDirectory() as tmp:
            exporter = get_exporter("html")
            path = exporter.write([exporter.render_section({"title": "Summary"}, "Hello")], tmp)
            self.assertEqual(path.suffix, ".html")
            self.assertTrue(path.exists())

    def test_markdown_exporter_writes_md(self) -> None:
        """Markdown export should create a .md file."""

        with tempfile.TemporaryDirectory() as tmp:
            exporter = get_exporter("md")
            path = exporter.write([exporter.render_section({"title": "Summary"}, "Hello")], tmp)
            self.assertEqual(path.suffix, ".md")
            self.assertTrue(path.exists())

    def test_notebook_exporter_writes_ipynb(self) -> None:
        """Notebook export should create a .ipynb file."""

        with tempfile.TemporaryDirectory() as tmp:
            exporter = get_exporter("notebook")
            path = exporter.write([exporter.render_section({"title": "Summary"}, "Hello")], tmp)
            self.assertEqual(path.suffix, ".ipynb")
            self.assertTrue(path.exists())

    def test_pdf_exporter_writes_pdf(self) -> None:
        """PDF export should create a .pdf file."""

        with tempfile.TemporaryDirectory() as tmp:
            exporter = get_exporter("pdf")
            path = exporter.write([exporter.render_section({"title": "Summary"}, "Hello")], tmp)
            self.assertEqual(path.suffix, ".pdf")
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
