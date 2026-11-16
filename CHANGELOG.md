# Changelog

All notable changes to DataViz CLI will be documented here.

## [Unreleased]

### Added
- MCP server exposing `inspect_dataset`, `analyze_dataset`, `suggest_charts`, `render_chart`, and `export_report`; runs without an LLM API key and supports `mcp` 1.x and 2.x. New console command `dataviz-mcp`. (`dataviz/mcp_server.py`, `pyproject.toml`)
- Agent skill describing when and how to use the MCP tools, with CLI fallback. (`skills/dataviz/SKILL.md`)
- MCP server and skill documentation. (`docs/mcp.md`, `README.md`)
- Tests for the MCP server. (`tests/test_mcp_server.py`)

### Fixed
- String columns were not treated as categorical on pandas 3, where the dtype is reported as `str`, so no boxplot was suggested and the summary counted zero categorical columns. (`dataviz/tools/viz_tools.py`, `dataviz/tools/report_tools.py`)

---

## [0.1.2-beta]

### Fixed
- Fixed `write_recommendations()` receiving `list[dict]` instead of `list[str]` (`TypeError: sequence item 0: expected str instance, dict found`) — the tool-call schema was hardcoding `items: {"type": "object"}` for every list-type parameter regardless of whether elements were strings or dicts. Added `arg_item_types` to the registry and updated schema building to read the correct type. (`dataviz/tools/registry.json`, `dataviz/providers/gemini_provider.py`, `dataviz/providers/claude_provider.py`, `dataviz/providers/openai_provider.py`)
- Fixed Markdown/Notebook export rendering charts as raw text (`repr()` of `vega_spec`) instead of actual images — added a shared SVG renderer with a fallback chain: Altair → vl-convert → Matplotlib → **pure-Python (zero dependencies)**, ensuring charts always render regardless of which packages are installed. (`dataviz/exporters/chart_render.py`)
- Fixed `_chart_to_svg()` in the PDF exporter always returning `None` due to unconditionally calling `.decode()` on the result of `vl_convert.vegalite_to_svg()`, which already returns `str`, not `bytes` — this caused all charts in PDF output to be empty. (`dataviz/exporters/pdf_exporter.py`)
- Fixed mismatched IDs between `HtmlExporter` (generating `vg_0, vg_1, ...` via a counter) and `PdfExporter._inject_svg_charts()` (looking up by `vg_{chart_id}`) — SVGs were never injected into PDF output. (`dataviz/exporters/html_exporter.py`)
- Fixed `_inject_svg_charts()` replacing `id="vg_..."` with a string containing an unclosed HTML comment (`<!--replaced`), causing all content after the first chart in a PDF to be hidden — replaced the approach to substitute the entire `<div>...</div>` block instead. (`dataviz/exporters/pdf_exporter.py`)
- Fixed notebook export producing invalid `nbformat` output — cells were missing required `id` fields, and markdown cells had an invalid `outputs` key. (`dataviz/exporters/notebook_exporter.py`)

### Added
- Tool-call trace mechanism (`trace_sink`) propagated through the full agent loop, giving exporters precise visibility into which tools the agent called and with what inputs — replacing the previous approach of inferring this from the text narrative. (`dataviz/agents/base.py`, `dataviz/agents/viz.py`, `dataviz/agents/report.py`, `dataviz/tools/report_tools.py`)
- Notebook export now reconstructs the pipeline as real code cells — each tool call made by the agent (`auto_select_charts`, `render_charts`, `write_summary`, `write_insights`, `write_recommendations`) becomes its own cell with real outputs; charts are displayed via the `application/vnd.vegalite.v6+json` and `image/svg+xml` MIME types. (`dataviz/exporters/notebook_exporter.py`)
- `render_charts()` now saves actual SVG images to disk (`<out_dir>/charts/<chart_id>.svg`) and returns `image_path`, instead of keeping only `vega_spec` in memory for exporters to reconstruct later — Markdown and Notebook export now reference real files. (`dataviz/tools/viz_tools.py`, `dataviz/tools/registry.json`, `dataviz/agents/viz.py`)
- Schema and stats tables are now rendered as real HTML `<table>` elements in Markdown and Notebook export, replacing the previous flat bullet-list format. (`dataviz/exporters/md_exporter.py`, `dataviz/exporters/notebook_exporter.py`)

### Changed
- Bumped version to `0.1.2`. (`pyproject.toml`)

---

## [0.1.1-beta]

### Fixed
- Fixed agents not actually being called — provider was hardcoded to bypass the agent layer. Removed the hardcode; agents are now properly invoked. (`dataviz/agents/`, `dataviz/providers/`, `dataviz/cli.py`)

### Added
- Unit tests for agents and orchestrator. (`tests/test_agents.py`, `tests/test_orchestrator.py`)

### Changed
- Bumped version to `0.1.1`. (`pyproject.toml`)

---

## [0.1.0-rc]

### Added
- Phase 0: repository skeleton on `phase-0-repo-initialization`
- `pyproject.toml` and package entry point
- Core config, cache, session, and tool registry helpers
- Abstract base classes for agents, providers, readers, and exporters
- Phase 0 docs and dashboard template assets
- Phase 1: core pipeline branch on `phase-1-core-pipeline`
- CSV, XLSX, and Parquet reader implementations
- Core configuration merge logic with provider-level overrides
- Unit tests covering config, readers, cache, session, and CLI help
- Phase 2: agent, provider, and tool scaffolding on `phase-2-agents`
- Tool registry entries and built-in tool modules for reader, EDA, viz, and report stages
- Orchestrator and concrete phase-2 agent classes
- Tests covering registry, providers, tools, and orchestrator flow
- Phase 3: TUI skeleton on `phase-3-tui`
- Screen models for dashboard, selector, preview, insight, and export views
- Progress board and log panel components
- CLI TUI launch gate and TUI rendering tests
- Phase 4: exporter layer on `phase-4-export`
- HTML, Markdown, PDF, and Notebook exporters
- Multi-file join helper and XLSX sheet listing support
- CLI export output path wiring and export tests
- Phase 5: polish on `phase-5-pypi`
- Tutorial-style README with install and usage walkthrough
- Release metadata in `pyproject.toml`
- Detailed provider configuration guide in `docs/configuration.md`

### Changed
- `design/README.md` index updated to match actual design file names
- CLI default command now summarizes input files through the reader layer
- `AGENT_RULE.md` removed in favor of `AGENTS.md`
- CLI now renders a basic TUI dashboard summary when enabled
- CLI now writes a report artifact for the selected output format
- README now documents the current CLI workflow and outputs
- README now links to the dedicated configuration guide

---

## Phase 0 — Repository Initialization

### Added
- Project skeleton, docs, and template assets
- Empty tool registry and dashboard template