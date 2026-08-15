# Changelog

All notable changes to DataViz CLI will be documented here.

## [0.1.2-beta]

### Fixed
- Fix `write_recommendations()` nhận `list[dict]` thay vì `list[str]` (`TypeError: sequence item 0: expected str instance, dict found`) -> Do schema tool-call hardcode `items: {"type": "object"}` cho mọi tham số kiểu list, không phân biệt phần tử là string hay dict. Đã thêm `arg_item_types` vào registry và đọc đúng type khi build schema (`dataviz/tools/registry.json`, `dataviz/providers/gemini_provider.py`, `dataviz/providers/claude_provider.py`, `dataviz/providers/openai_provider.py`)
- Fix export Markdown/Notebook hiển thị chart dưới dạng text dump (`repr()` của `vega_spec`) thay vì hình ảnh thực -> Thêm renderer SVG dùng chung, có chuỗi fallback Altair -> vl-convert -> Matplotlib -> **pure-Python (zero dependency)** để đảm bảo luôn render được kể cả khi không cài thêm package nào (`dataviz/exporters/chart_render.py`)
- Fix `_chart_to_svg()` trong PDF exporter luôn trả `None` do gọi `.decode()` vô điều kiện lên kết quả `vl_convert.vegalite_to_svg()` (vốn đã là `str`, không phải `bytes`) -> khiến toàn bộ chart trong PDF bị rỗng (`dataviz/exporters/pdf_exporter.py`)
- Fix ID không khớp giữa `HtmlExporter` (sinh `vg_0, vg_1, ...` theo counter) và `PdfExporter._inject_svg_charts()` (tìm theo `vg_{chart_id}`) -> SVG không bao giờ được chèn vào PDF (`dataviz/exporters/html_exporter.py`)
- Fix `_inject_svg_charts()` thay thế `id="vg_..."` bằng chuỗi chứa comment HTML không đóng (`<!--replaced`), làm toàn bộ nội dung phía sau chart đầu tiên trong PDF bị ẩn -> Đổi sang thay nguyên khối `<div>...</div>` (`dataviz/exporters/pdf_exporter.py`)
- Fix notebook export không hợp lệ theo chuẩn `nbformat` (thiếu `id` cho cell, cell markdown có key `outputs` không hợp lệ) (`dataviz/exporters/notebook_exporter.py`)

### Added
- Cơ chế trace tool call thật xuyên suốt agent loop (`trace_sink`) để exporter biết chính xác agent đã gọi tool nào với input gì, thay vì suy luận từ text narrative (`dataviz/agents/base.py`, `dataviz/agents/viz.py`, `dataviz/agents/report.py`, `dataviz/tools/report_tools.py`)
- Notebook export giờ dựng lại pipeline thành các cell code thật — mỗi tool call agent gọi (`auto_select_charts`, `render_charts`, `write_summary`, `write_insights`, `write_recommendations`) là 1 cell riêng kèm output thật, chart hiển thị qua mimetype `application/vnd.vegalite.v6+json` + `image/svg+xml` (`dataviz/exporters/notebook_exporter.py`)
- `render_charts()` giờ lưu ảnh SVG thật ra đĩa (`<out_dir>/charts/<chart_id>.svg`) và trả về `image_path`, thay vì chỉ giữ `vega_spec` trong bộ nhớ để exporter tái tạo sau -> Markdown/Notebook dùng file thật thay vì reconstruct (`dataviz/tools/viz_tools.py`, `dataviz/tools/registry.json`, `dataviz/agents/viz.py`)
- Render bảng schema/stats thành HTML `<table>` thật trong Markdown và Notebook export, thay vì list gạch đầu dòng phẳng (`dataviz/exporters/md_exporter.py`, `dataviz/exporters/notebook_exporter.py`)

### Changed
- Cập nhật version lên `0.1.2` (`pyproject.toml`)

## [0.1.1-beta]

### Fixed
- Fix bug model không thực sự gọi đến các agent mà hard code -> Đã bỏ hardcode và agent thực sự được call (`dataviz/agents/`, `dataviz/providers/`, `dataviz/cli.py`)

### Added
- Unit tests cho agents và orchestrator (`tests/test_agents.py`, `tests/test_orchestrator.py`)

### Changed
- Cập nhật version lên `0.1.1` (`pyproject.toml`)

## [0.1.0-rc]

### Added
- Phase 0 repository skeleton on `phase-0-repo-initialization`
- `pyproject.toml` and package entry point
- Core config, cache, session, and tool registry helpers
- Abstract base classes for agents, providers, readers, and exporters
- Phase 0 docs and dashboard template assets
- Phase 1 core pipeline branch on `phase-1-core-pipeline`
- CSV, XLSX, and Parquet reader implementations
- Core configuration merge logic with provider-level overrides
- Unit tests covering config, readers, cache, session, and CLI help
- Phase 2 agent, provider, and tool scaffolding on `phase-2-agents`
- Tool registry entries and built-in tool modules for reader, EDA, viz, and report stages
- Orchestrator and concrete phase-2 agent classes
- Tests covering registry, providers, tools, and orchestrator flow
- Phase 3 TUI skeleton on `phase-3-tui`
- Screen models for dashboard, selector, preview, insight, and export views
- Progress board and log panel components
- CLI TUI launch gate and TUI rendering tests
- Phase 4 exporter layer on `phase-4-export`
- HTML, Markdown, PDF, and Notebook exporters
- Multi-file join helper and XLSX sheet listing support
- CLI export output path wiring and export tests
- Phase 5 polish on `phase-5-pypi`
- Tutorial-style README with install and usage walkthrough
- Release metadata in `pyproject.toml`
- Detailed provider configuration guide in `docs/configuration.md`

### Changed
- `design/README.md` index updated to match the actual design file names
- CLI default command now summarizes input files through the reader layer
- `AGENT_RULE.md` removed in favor of `AGENTS.md`
- CLI now renders a basic TUI dashboard summary when enabled
- CLI now writes a report artifact for the selected output format
- README now documents the current CLI workflow and outputs
- README now links to the dedicated configuration guide

## Phase 0 - Repository Initialization

### Added
- Project skeleton, docs, and template assets
- Empty tool registry and dashboard template
