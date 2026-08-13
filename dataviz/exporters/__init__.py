from .base import BaseExporter
from .html_exporter import HtmlExporter
from .md_exporter import MdExporter
from .notebook_exporter import NotebookExporter
from .pdf_exporter import PdfExporter


def get_exporter(output_format: str) -> BaseExporter:
    """Return the exporter for a requested output format."""

    if output_format == "md":
        return MdExporter()
    if output_format == "pdf":
        return PdfExporter()
    if output_format == "notebook":
        return NotebookExporter()
    return HtmlExporter()


__all__ = ["BaseExporter", "HtmlExporter", "MdExporter", "PdfExporter", "NotebookExporter", "get_exporter"]
