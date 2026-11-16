---
name: dataviz
description: Analyze tabular data files (CSV, Excel .xlsx, Parquet), choose and render charts, and export a report (HTML, PDF, Markdown, Jupyter notebook). Use when the user shares or mentions a data file and wants to explore it, profile it, check missing values or outliers, visualize it, or get a shareable report or dashboard from it.
---

# DataViz

Turn a tabular data file into insight, charts, and a report with the DataViz tools.

## Tools

Prefer the `dataviz` MCP server. It needs no LLM API key. Tool names:

| Tool | Use for |
|------|---------|
| `inspect_dataset` | First look: columns, dtypes, null counts, sample rows |
| `analyze_dataset` | EDA: `stats`, `nulls`, `correlation`, `time_series`, `categorical`, `outliers` |
| `suggest_charts` | Chart specs that fit the column types |
| `render_chart` | One chart saved as SVG (histogram, scatter, boxplot, line, heatmap, bar, violin, pie) |
| `export_report` | Full report as `html`, `md`, `pdf`, or `notebook` |

All tools take a `file_path`. Excel files accept `sheet_name`; the default is the first sheet.

## Workflow

1. Call `inspect_dataset` first. Never guess column names.
2. Match the depth to the request:
   - "What's in this file?" → `inspect_dataset`, then summarize in prose.
   - "Check quality / find problems" → `analyze_dataset` with `nulls` and `outliers`.
   - "Show me X vs Y" → `render_chart` with the columns the user named.
   - "Visualize this" with no specifics → `suggest_charts`, then `render_chart` for the best few. Do not render all of them.
   - "Give me a report / dashboard" → `export_report`. Default to `html`; use `pdf`, `md`, or `notebook` only if asked.
3. Tell the user where the files are (the tool returns absolute paths) and summarize the findings in plain language. Do not just paste raw JSON.

## Choosing charts

- One numeric column → `histogram`. Compare a numeric column across groups → `boxplot` or `violin`.
- Two numeric columns → `scatter` (add `hue` for a category).
- Date column plus a numeric column → `line`.
- Three or more numeric columns → `heatmap` for correlations.
- Category counts → `bar` or `pie` (pie only for a handful of categories).

## Notes and limits

- `export_report` writes rule-based summary, insights, and recommendations from the data itself. It does not call an LLM. Write any deeper interpretation yourself from `analyze_dataset` results.
- If a chart fails, the tool error names the cause (usually a wrong column name). Fix the argument and retry.
- `svg_path` can be `null` when no SVG backend is available. The report export still works.
- `pdf` export needs Playwright Chromium (`playwright install chromium`).
- Large files are loaded fully into memory. Warn the user about files with millions of rows.

## If the MCP server is not available

1. Install the package: `pip install dataviz` (or `pip install -e .` from the repo) and register the server (see `docs/mcp.md`).
2. If registering is not possible, the same functions can be called from Python: `from dataviz.mcp_server import inspect_dataset, export_report`.
3. The CLI `dataviz <file> --output html --no-tui --out-dir <dir>` also works, but it requires an LLM provider key first: `dataviz config set --provider claude --key <key>`.
