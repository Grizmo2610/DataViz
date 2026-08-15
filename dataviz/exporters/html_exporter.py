from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseExporter

# Vega / Vega-Lite / Vega-Embed CDN versions (pinned for reproducibility)
_VEGA_VERSION = "5"
_VEGALITE_VERSION = "5"
_VEGAEMBED_VERSION = "6"

_FONT_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"

_HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="{font_url}" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/vega@{vega}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@{vegalite}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@{vegaembed}"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #f7f8fc;
      --surface: #ffffff;
      --border: #e4e6f0;
      --text-primary: #1a1a2e;
      --text-secondary: #555770;
      --text-muted: #9092a8;
      --accent: #4361ee;
      --accent-light: #eef0fd;
      --radius: 10px;
      --shadow: 0 1px 4px rgba(30,30,60,.06), 0 4px 16px rgba(30,30,60,.04);
    }}

    body {{
      font-family: Inter, 'IBM Plex Sans', system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.65;
      background: var(--bg);
      color: var(--text-primary);
      padding: 0 0 4rem;
    }}

    /* ── Header ── */
    .report-header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 2.5rem 0 2rem;
      margin-bottom: 2.5rem;
    }}
    .report-header .inner {{
      max-width: 900px;
      margin: 0 auto;
      padding: 0 2rem;
    }}
    .report-header h1 {{
      font-size: 1.75rem;
      font-weight: 600;
      color: var(--text-primary);
      letter-spacing: -.02em;
    }}
    .report-header .subtitle {{
      color: var(--text-secondary);
      margin-top: .35rem;
      font-size: .95rem;
    }}
    .report-header .meta {{
      display: flex;
      gap: 1.5rem;
      margin-top: 1.25rem;
      flex-wrap: wrap;
    }}
    .report-header .meta-item {{
      display: flex;
      flex-direction: column;
      background: var(--accent-light);
      padding: .5rem 1rem;
      border-radius: 6px;
    }}
    .report-header .meta-item .label {{
      font-size: .75rem;
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--accent);
    }}
    .report-header .meta-item .value {{
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
    }}

    /* ── Main layout ── */
    .report-body {{
      max-width: 900px;
      margin: 0 auto;
      padding: 0 2rem;
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }}

    /* ── Section card ── */
    .section-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    .section-card .card-header {{
      padding: 1.1rem 1.5rem .9rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: .6rem;
    }}
    .section-card .card-header h2 {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--text-primary);
      letter-spacing: -.01em;
    }}
    .section-card .card-header .pill {{
      font-size: .7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .07em;
      padding: .2rem .55rem;
      border-radius: 999px;
      background: var(--accent-light);
      color: var(--accent);
    }}
    .section-card .card-body {{
      padding: 1.25rem 1.5rem;
    }}

    /* ── Summary text ── */
    .summary-text {{
      color: var(--text-secondary);
      font-size: .97rem;
    }}

    /* ── Stats grid ── */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: .85rem;
    }}
    .stat-item {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: .75rem 1rem;
    }}
    .stat-item .stat-col {{
      font-size: .8rem;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: .4rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .stat-item .stat-row {{
      display: flex;
      justify-content: space-between;
      font-size: .8rem;
      color: var(--text-secondary);
      padding: .1rem 0;
    }}
    .stat-item .stat-row .val {{
      font-weight: 500;
      color: var(--text-primary);
      font-variant-numeric: tabular-nums;
    }}

    /* ── Chart grid ── */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 1.25rem;
    }}
    .chart-card {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
    }}
    .chart-card .chart-title {{
      font-size: .85rem;
      font-weight: 600;
      color: var(--text-secondary);
      margin-bottom: .65rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .chart-card .vega-container {{
      width: 100%;
      min-height: 260px;
    }}

    /* ── Insights / recommendations ── */
    .insights-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: .65rem;
    }}
    .insights-list li {{
      display: flex;
      gap: .75rem;
      font-size: .95rem;
      color: var(--text-secondary);
      line-height: 1.55;
    }}
    .insights-list li::before {{
      content: "";
      flex-shrink: 0;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--accent);
      margin-top: .55rem;
    }}

    /* ── Schema table ── */
    .schema-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: .88rem;
    }}
    .schema-table th {{
      text-align: left;
      font-weight: 600;
      font-size: .75rem;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: var(--text-muted);
      padding: .5rem .75rem;
      border-bottom: 1px solid var(--border);
    }}
    .schema-table td {{
      padding: .55rem .75rem;
      color: var(--text-secondary);
      border-bottom: 1px solid var(--border);
    }}
    .schema-table tr:last-child td {{ border-bottom: none; }}
    .schema-table td:first-child {{
      font-weight: 500;
      color: var(--text-primary);
      font-family: 'IBM Plex Mono', 'Fira Mono', monospace;
      font-size: .82rem;
    }}
    .dtype-badge {{
      display: inline-block;
      font-size: .72rem;
      padding: .15rem .45rem;
      border-radius: 4px;
      background: var(--bg);
      border: 1px solid var(--border);
      font-family: monospace;
      color: var(--text-muted);
    }}

    /* ── Null bar ── */
    .null-bar-wrap {{
      display: flex;
      align-items: center;
      gap: .5rem;
    }}
    .null-bar {{
      flex: 1;
      height: 5px;
      background: var(--border);
      border-radius: 3px;
      overflow: hidden;
    }}
    .null-bar-fill {{
      height: 100%;
      background: #e63946;
      border-radius: 3px;
    }}
    .null-pct {{
      font-size: .78rem;
      color: var(--text-muted);
      min-width: 36px;
      text-align: right;
    }}

    /* ── Footer ── */
    .report-footer {{
      text-align: center;
      color: var(--text-muted);
      font-size: .82rem;
      margin-top: 3rem;
    }}
  </style>
</head>
<body>

<header class="report-header">
  <div class="inner">
    <h1>{title}</h1>
    <p class="subtitle">Automated EDA report</p>
    {meta_html}
  </div>
</header>

<main class="report-body">
  {body}
</main>

<footer class="report-footer">
  Generated by DataViz &mdash; {date}
</footer>

<script>
{embed_scripts}
</script>

</body>
</html>
"""


class HtmlExporter(BaseExporter):
    """Render a polished, self-contained HTML report with interactive Vega charts."""

    # ------------------------------------------------------------------ #
    # BaseExporter interface                                               #
    # ------------------------------------------------------------------ #

    def render_section(self, section: dict[str, Any], content: Any) -> str:
        """Render a single section.  Dispatches to specialised renderers."""
        section_id = section.get("id", "")
        title = section.get("title", section_id.title())
        pill = section.get("pill", "")

        if section_id == "charts":
            body_html = self._render_charts(content)
        elif section_id == "schema":
            body_html = self._render_schema(content)
        elif section_id == "stats":
            body_html = self._render_stats(content)
        elif section_id in ("insights", "recommendations", "summary"):
            body_html = self._render_text(content)
        else:
            body_html = self._render_generic(content)

        header_html = f"""
        <div class="card-header">
          <h2>{title}</h2>
          {f'<span class="pill">{pill}</span>' if pill else ''}
        </div>"""

        return f'<div class="section-card">{header_html}<div class="card-body">{body_html}</div></div>'

    def write(
        self,
        rendered_sections: list[str],
        out_dir: str | Path,
        **kwargs: Any,
    ) -> Path:
        """Write the HTML report to *out_dir/report.html*."""
        import datetime

        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "report.html"

        title = kwargs.get("title", "DataViz Report")
        meta = kwargs.get("meta", {})

        meta_items = "".join(
            f'<div class="meta-item"><span class="label">{k}</span>'
            f'<span class="value">{v}</span></div>'
            for k, v in meta.items()
        )
        meta_html = f'<div class="meta">{meta_items}</div>' if meta_items else ""

        file_path.write_text(
            _HTML_TEMPLATE.format(
                title=title,
                font_url=_FONT_URL,
                vega=_VEGA_VERSION,
                vegalite=_VEGALITE_VERSION,
                vegaembed=_VEGAEMBED_VERSION,
                meta_html=meta_html,
                body="\n".join(rendered_sections),
                embed_scripts=self._embed_scripts,
                date=datetime.date.today().isoformat(),
            ),
            encoding="utf-8",
        )
        self._embed_scripts = ""
        return file_path

    # ------------------------------------------------------------------ #
    # Section renderers                                                    #
    # ------------------------------------------------------------------ #

    def __init__(self) -> None:
        self._embed_scripts = ""
        self._chart_counter = 0

    def _render_charts(self, charts: list[dict[str, Any]]) -> str:
        if not charts:
            return '<p style="color:var(--text-muted)">No charts generated.</p>'

        cards = []
        for chart in charts:
            spec = chart.get("vega_spec")
            title = chart.get("title", chart.get("chart_id", "Chart"))
            # Keyed by the chart's own chart_id (stable across exporters) so
            # PdfExporter._inject_svg_charts, which looks up id="vg_{chart_id}",
            # can actually find and replace this placeholder. Falls back to a
            # counter only for charts missing a chart_id.
            cid = f"vg_{chart.get('chart_id') or self._chart_counter}"
            self._chart_counter += 1

            if spec and not spec.get("_stub"):
                spec_json = json.dumps(spec)
                self._embed_scripts += (
                    f'vegaEmbed("#{cid}", {spec_json}, '
                    f'{{renderer:"svg",actions:{{export:true,source:false,editor:false}}}});\n'
                )
                container = f'<div id="{cid}" class="vega-container"></div>'
            else:
                err = chart.get("error", "Chart unavailable")
                container = f'<p style="color:#e63946;font-size:.85rem">{err}</p>'

            cards.append(
                f'<div class="chart-card">'
                f'<div class="chart-title">{title}</div>'
                f'{container}</div>'
            )

        return f'<div class="charts-grid">{"".join(cards)}</div>'

    def _render_schema(self, schema: dict[str, Any]) -> str:
        columns = schema.get("columns", [])
        if not columns:
            return "<p>No schema available.</p>"

        rows = ""
        for col in columns:
            null_count = col.get("null_count", 0)
            unique = col.get("unique_count", "–")
            dtype = col.get("dtype", "unknown")
            # null bar
            total = schema.get("row_count", 1) or 1
            null_pct = null_count / total
            bar = (
                f'<div class="null-bar-wrap">'
                f'<div class="null-bar"><div class="null-bar-fill" style="width:{null_pct*100:.1f}%"></div></div>'
                f'<span class="null-pct">{null_pct*100:.1f}%</span>'
                f'</div>'
            )
            rows += (
                f"<tr>"
                f"<td>{col['name']}</td>"
                f'<td><span class="dtype-badge">{dtype}</span></td>'
                f"<td>{unique:,}</td>"
                f"<td>{bar}</td>"
                f"</tr>"
            )

        return (
            f'<table class="schema-table">'
            f"<thead><tr><th>Column</th><th>Type</th><th>Unique</th><th>Nulls</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )

    def _render_stats(self, stats: Any) -> str:
        """Render numeric stats grid. stats can be the full read_full_stats dict."""
        columns = []
        if isinstance(stats, dict):
            # read_full_stats format: {row_count, column_count, columns: [...]}
            columns = stats.get("columns", [])
            if not columns and "row_count" in stats:
                # minimal stats — just show counts
                return (
                    f'<div class="stats-grid">'
                    f'<div class="stat-item"><div class="stat-col">Dataset</div>'
                    f'<div class="stat-row"><span>Rows</span><span class="val">{stats.get("row_count",0):,}</span></div>'
                    f'<div class="stat-row"><span>Columns</span><span class="val">{stats.get("column_count",0)}</span></div>'
                    f'</div></div>'
                )

        numeric_cols = [c for c in columns if "min" in c]
        if not numeric_cols:
            return '<p style="color:var(--text-muted)">No numeric statistics available.</p>'

        cards = []
        for col in numeric_cols:
            rows = ""
            for key in ("min", "mean", "50%", "max", "std"):
                val = col.get(key)
                if val is not None:
                    label = {"50%": "median"}.get(key, key)
                    rows += f'<div class="stat-row"><span>{label}</span><span class="val">{val:,.4g}</span></div>'
            cards.append(
                f'<div class="stat-item">'
                f'<div class="stat-col">{col["name"]}</div>'
                f'{rows}</div>'
            )

        return f'<div class="stats-grid">{"".join(cards)}</div>'

    def _render_text(self, content: Any) -> str:
        if isinstance(content, list):
            items = "".join(f"<li>{item}</li>" for item in content)
            return f'<ul class="insights-list">{items}</ul>'
        if isinstance(content, str):
            paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
            if len(paragraphs) > 1:
                items = "".join(f"<li>{p}</li>" for p in paragraphs)
                return f'<ul class="insights-list">{items}</ul>'
            return f'<p class="summary-text">{content}</p>'
        return f"<p>{content}</p>"

    def _render_generic(self, content: Any) -> str:
        if isinstance(content, dict):
            rows = "".join(
                f'<div class="stat-row"><span>{k}</span><span class="val">{v}</span></div>'
                for k, v in content.items()
            )
            return f'<div class="stat-item">{rows}</div>'
        if isinstance(content, list):
            items = "".join(f"<li>{item}</li>" for item in content)
            return f'<ul class="insights-list">{items}</ul>'
        return f"<pre>{content}</pre>"