from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseExporter
from .html_exporter import HtmlExporter

# Vega CLI renders specs to SVG for PDF (no browser needed)
_VEGA_VERSION = "5"
_VEGALITE_VERSION = "5"


class PdfExporter(BaseExporter):
    """Render a PDF report via WeasyPrint.

    Strategy:
    1. Build a print-optimised HTML (charts converted to inline SVG via Altair's
       SVG renderer so WeasyPrint doesn't need JavaScript).
    2. Run WeasyPrint on that HTML → PDF.
    """

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Delegate section rendering to the HTML exporter (reuse its logic)."""
        return self._html_exporter.render_section(section, content)

    def write(
        self,
        rendered_sections: list[str],
        out_dir: str | Path,
        **kwargs: Any,
    ) -> Path:
        """Write the PDF report to *out_dir/report.pdf*.

        Falls back to writing a plain-text placeholder when WeasyPrint is not
        installed, so the pipeline never hard-crashes on missing optional deps.
        """
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        pdf_path = out_path / "report.pdf"

        # Build print HTML first (charts are already inline SVG at this point)
        html_content = self._build_print_html(rendered_sections, **kwargs)

        try:
            from weasyprint import HTML  # type: ignore[import]
            HTML(string=html_content, base_url=str(out_path)).write_pdf(str(pdf_path))
        except ImportError:
            pdf_path.write_text(
                "WeasyPrint not installed. Run: pip install weasyprint\n\n" + html_content,
                encoding="utf-8",
            )

        return pdf_path

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def __init__(self) -> None:
        self._html_exporter = HtmlExporter()

    def _chart_to_svg(self, vega_spec: dict[str, Any]) -> str | None:
        """Convert a Vega-Lite spec to an SVG string using Altair's renderer.

        Returns None on failure (chart will be omitted from PDF).
        """
        from .chart_render import chart_to_svg
        return chart_to_svg(vega_spec)

    def _build_print_html(self, rendered_sections: list[str], **kwargs: Any) -> str:
        """Build a print-optimised HTML document with inline SVG charts."""
        import datetime

        title = kwargs.get("title", "DataViz Report")
        meta = kwargs.get("meta", {})
        charts: list[dict[str, Any]] = kwargs.get("charts", [])

        # Replace vega-embed placeholders with inline SVG
        body = "\n".join(rendered_sections)
        body = self._inject_svg_charts(body, charts)

        meta_rows = "".join(
            f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in meta.items()
        )
        meta_table = f"<table class='meta-table'>{meta_rows}</table>" if meta_rows else ""

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --border: #dde0ee;
      --text: #1a1a2e;
      --muted: #666880;
      --accent: #4361ee;
    }}
    body {{
      font-family: Inter, 'Helvetica Neue', Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.6;
      color: var(--text);
      padding: 0;
    }}
    /* Print page setup */
    @page {{
      size: A4;
      margin: 18mm 20mm 18mm 20mm;
      @bottom-center {{
        content: "Page " counter(page) " of " counter(pages);
        font-size: 9pt;
        color: var(--muted);
      }}
    }}
    /* Header */
    .report-header {{
      border-bottom: 2px solid var(--accent);
      padding-bottom: 1rem;
      margin-bottom: 1.5rem;
    }}
    .report-header h1 {{
      font-size: 18pt;
      font-weight: 600;
      color: var(--text);
      letter-spacing: -.02em;
    }}
    .report-header .subtitle {{
      color: var(--muted);
      font-size: 10pt;
      margin-top: .2rem;
    }}
    .meta-table {{
      margin-top: .8rem;
      border-collapse: collapse;
      font-size: 9.5pt;
    }}
    .meta-table th, .meta-table td {{
      padding: .2rem .6rem;
      border: 1px solid var(--border);
    }}
    .meta-table th {{
      font-weight: 500;
      color: var(--muted);
      background: #f5f6fc;
      text-align: left;
    }}
    /* Sections */
    .section-card {{
      margin-bottom: 1.4rem;
      border: 1px solid var(--border);
      border-radius: 6px;
      page-break-inside: avoid;
      overflow: hidden;
    }}
    .section-card .card-header {{
      padding: .55rem .9rem;
      border-bottom: 1px solid var(--border);
      background: #f5f6fc;
    }}
    .section-card .card-header h2 {{
      font-size: 10.5pt;
      font-weight: 600;
      color: var(--text);
    }}
    .section-card .card-body {{
      padding: .9rem;
    }}
    /* Charts — inline SVG */
    .charts-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: .8rem;
    }}
    .chart-card {{
      page-break-inside: avoid;
      border: 1px solid var(--border);
      border-radius: 5px;
      padding: .6rem;
    }}
    .chart-title {{
      font-size: 9pt;
      font-weight: 600;
      color: var(--muted);
      margin-bottom: .4rem;
    }}
    .chart-card svg {{
      width: 100%;
      height: auto;
    }}
    /* Stats */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: .5rem;
    }}
    .stat-item {{
      border: 1px solid var(--border);
      border-radius: 5px;
      padding: .5rem .7rem;
      font-size: 9pt;
    }}
    .stat-item .stat-col {{
      font-weight: 600;
      font-size: 9.5pt;
      margin-bottom: .25rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .stat-item .stat-row {{
      display: flex;
      justify-content: space-between;
      color: var(--muted);
    }}
    .stat-item .stat-row .val {{
      font-weight: 500;
      color: var(--text);
    }}
    /* Schema table */
    .schema-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 9.5pt;
    }}
    .schema-table th {{
      font-size: 8.5pt;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--muted);
      padding: .3rem .6rem;
      border-bottom: 1px solid var(--border);
      text-align: left;
    }}
    .schema-table td {{
      padding: .3rem .6rem;
      color: var(--muted);
      border-bottom: 1px solid var(--border);
    }}
    .schema-table td:first-child {{
      font-weight: 500;
      color: var(--text);
      font-family: monospace;
      font-size: 8.5pt;
    }}
    /* Insights */
    .insights-list {{
      list-style: none;
    }}
    .insights-list li {{
      display: flex;
      gap: .5rem;
      font-size: 10.5pt;
      color: var(--muted);
      padding: .2rem 0;
    }}
    .insights-list li::before {{
      content: "•";
      color: var(--accent);
      font-weight: 700;
    }}
    /* Footer */
    .report-footer {{
      text-align: center;
      color: var(--muted);
      font-size: 8.5pt;
      margin-top: 2rem;
      padding-top: .8rem;
      border-top: 1px solid var(--border);
    }}
    /* Misc */
    .null-bar-wrap {{ display: flex; align-items: center; gap: .35rem; }}
    .null-bar {{ flex:1; height:4px; background:#eee; border-radius:3px; overflow:hidden; }}
    .null-bar-fill {{ height:100%; background:#e63946; border-radius:3px; }}
    .null-pct {{ font-size:8pt; color:var(--muted); min-width:32px; text-align:right; }}
    .dtype-badge {{ font-size:8pt; font-family:monospace; padding:.1rem .35rem; background:#f0f1f8; border-radius:3px; }}
    .pill {{ font-size:8pt; font-weight:600; text-transform:uppercase; letter-spacing:.07em;
             padding:.15rem .45rem; border-radius:999px; background:#eef0fd; color:var(--accent); }}
    .summary-text {{ font-size:10.5pt; color:var(--muted); }}
  </style>
</head>
<body>
<header class="report-header">
  <h1>{title}</h1>
  <p class="subtitle">Automated EDA report</p>
  {meta_table}
</header>

{body}

<footer class="report-footer">
  Generated by DataViz &mdash; {datetime.date.today().isoformat()}
</footer>
</body>
</html>"""

    def _inject_svg_charts(self, html: str, charts: list[dict[str, Any]]) -> str:
        """Replace vega-embed placeholder divs with inline SVG in the HTML body.

        HtmlExporter emits each chart as an empty
        ``<div id="vg_{chart_id}" class="vega-container"></div>`` that a
        <script> fills in client-side via vega-embed. WeasyPrint doesn't run
        JavaScript, so for PDF we replace that *whole* placeholder element
        with the rendered SVG -- replacing only a fragment of it (e.g. just
        the id attribute) would leave the tag unbalanced and corrupt the
        rest of the document.
        """
        if not charts:
            return html

        for chart in charts:
            spec = chart.get("vega_spec")
            chart_id = chart.get("chart_id", "")
            if not spec or spec.get("_stub") or not chart_id:
                continue
            svg = self._chart_to_svg(spec)
            placeholder = f'<div id="vg_{chart_id}" class="vega-container"></div>'
            if svg:
                replacement = f'<div id="vg_{chart_id}" class="vega-container">{svg}</div>'
            else:
                replacement = (
                    f'<div id="vg_{chart_id}" class="vega-container">'
                    f'<p style="color:#e63946;font-size:.85rem">Chart could not be rendered.</p></div>'
                )
            html = html.replace(placeholder, replacement)

        return html