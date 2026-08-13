# 00 — Roadmap

## Tổng Quan Phases

| Phase | Branch | Mô tả | Ước tính |
|---|---|---|---|
| Phase 0 | `main` | Repository initialization | 1–2 ngày |
| Phase 1 | `phase-1-core-pipeline` | Core pipeline, config, readers | 3–5 ngày |
| Phase 2 | `phase-2-agents` | Agent + LLM integration | 1–2 tuần |
| Phase 3 | `phase-3-tui` | TUI (Textual) | 3–5 ngày |
| Phase 4 | `phase-4-export` | Exporters + Multi-file | 3–5 ngày |
| Phase 5 | `phase-5-pypi` | Polish, docs, PyPI publish | 3–5 ngày |

---

## Phase 0 — Repository Initialization

> Branch: `main`
> Mục tiêu: Repo skeleton sẵn sàng cho development

```
[ ] Initialize git repo
[ ] Tạo pyproject.toml với project metadata và dependencies
[ ] Tạo docs/templates/ — viết tất cả document templates trước
[ ] Viết README.md từ template
[ ] Viết CHANGELOG.md từ template
[ ] Viết CONTRIBUTING.md từ template
[ ] Viết AGENT_RULE.md từ template
[ ] Viết ROADMAP.md
[ ] Tạo .gitignore (Python standard + generated tools folder)
[ ] Tạo package skeleton (dataviz/ với tất cả __init__.py stubs)
[ ] Tạo dataviz/tools/generated/.gitkeep
[ ] Tạo dataviz/templates/dashboard/default.json
[ ] Tạo dataviz/tools/registry.json (empty tools array)
[ ] Tạo docs/setup-windows.md skeleton
[ ] Initial commit trên main
```

**Definition of Done:** `python -m dataviz --help` không crash (dù chưa có logic).

---

## Phase 1 — Core Pipeline

> Branch: `phase-1-core-pipeline`
> Mục tiêu: Infra hoạt động, không có agents

```
[ ] CLI entry point với Typer (dataviz --help works)
[ ] dataviz config set / update / show subcommands
[ ] config.py — global + local resolution per field
[ ] tool_gen_mode field trong config (immediate / deferred)
[ ] File readers:
    [ ] CSV reader — auto-detect delimiter (, ; \t)
    [ ] XLSX reader — multi-sheet support
    [ ] Parquet reader — lazy read với polars
    [ ] Abstract reader base class (readers/base.py)
    [ ] Scale strategy: small/medium/large → full/chunked/lazy
[ ] Cache system:
    [ ] SHA256 hash computation
    [ ] Cache read/write (.dataviz/cache/<hash>.json)
    [ ] Cache invalidation khi file thay đổi
[ ] Session system:
    [ ] session save (metadata.json)
    [ ] session list
    [ ] session open
[ ] dataviz session list / open subcommands
[ ] dataviz cache clear subcommand
[ ] Unit tests:
    [ ] test_config.py (tất cả resolution scenarios)
    [ ] test_readers.py (3 formats, scale strategy)
    [ ] test_cache.py (hash, read, write, invalidation)
    [ ] test_session.py (save, list, open)
[ ] Cập nhật CHANGELOG.md và ROADMAP.md
```

**Definition of Done:** tất cả unit tests pass, `dataviz config show` hoạt động.

---

## Phase 2 — Agent + LLM Integration

> Branch: `phase-2-agents`
> Mục tiêu: Full pipeline chạy được với real LLM

```
[ ] Provider layer:
    [ ] Abstract BaseProvider (providers/base.py)
    [ ] OpenAI provider (+ OpenAI-compatible via base_url)
    [ ] Claude provider
    [ ] Gemini provider
    [ ] get_provider() factory function

[ ] Tool system:
    [ ] ToolRegistry (tools/loader.py)
    [ ] Populate registry.json với tất cả built-in tools
    [ ] reader_tools.py — 4 tools
    [ ] eda_tools.py — 6 tools
    [ ] viz_tools.py — 11 tools
    [ ] report_tools.py — 4 tools (bao gồm assemble_dashboard)

[ ] Agent base class:
    [ ] BaseAgent (agents/base.py)
    [ ] Tool call loop
    [ ] _call_tool() lookup và execute
    [ ] PipelineContext dataclass
    [ ] AgentResult dataclass

[ ] Individual agents:
    [ ] Reader Agent
    [ ] EDA Agent
    [ ] Viz Agent
    [ ] Report Agent

[ ] Orchestrator:
    [ ] Pipeline sequencing
    [ ] Shared context passing
    [ ] Per-agent retry (max 3)
    [ ] --fast / --deep mode handling
    [ ] --focus flag truyền vào context
    [ ] --lang flag truyền vào Report Agent

[ ] Data strategy:
    [ ] Sampling (10–20 → AI decide → up to 100 rows)
    [ ] Full-data pass chunked/lazy

[ ] assemble_dashboard tool:
    [ ] Template JSON loading (resolution order)
    [ ] Section rendering per output format
    [ ] File writing + path return

[ ] Dynamic tool generation (tool_gen.py):
    [ ] Detect missing tool trong agent loop
    [ ] Immediate mode: generate → save → load → execute
    [ ] Deferred mode: append to pending_tools.json → continue
    [ ] Generated tool file format + saved to generated/
    [ ] registry.json update với generated: true entry
    [ ] dataviz tool-gen list / run / run --name / discard

[ ] Integration tests:
    [ ] test_pipeline_mock.py (full pipeline, mocked LLM)
    [ ] test_multi_file.py (join logic)

[ ] Cập nhật CHANGELOG.md và ROADMAP.md
```

**Definition of Done:** `dataviz tests/fixtures/small_sales.csv --output html --no-tui` tạo ra file HTML hợp lệ với charts và insights.

---

## Phase 3 — TUI (Textual)

> Branch: `phase-3-tui`
> Mục tiêu: Interactive terminal UI hoạt động đầy đủ

```
[ ] Textual app skeleton (tui/app.py)
[ ] Screen routing (Screen stack)
[ ] Dashboard screen:
    [ ] Tree component (EDA / Charts / Insights / Export)
    [ ] DataTable cho schema
    [ ] DataTable cho stats
[ ] Chart selector screen:
    [ ] List view với keyboard navigation
    [ ] Multi-select với Space
[ ] Chart preview screen:
    [ ] Sixel detection
    [ ] Browser fallback
    [ ] Chart metadata display
[ ] Insight screen:
    [ ] Scrollable Markdown renderer
[ ] Export screen:
    [ ] Format radio buttons
    [ ] Out-dir input
    [ ] Session name input
    [ ] Export trigger
[ ] Components:
    [ ] ProgressBar + Spinner per agent (real-time update)
    [ ] Log panel (agent activity feed, auto-scroll)
    [ ] Footer keyboard shortcuts (context-aware)
[ ] --interactive flag:
    [ ] Q&A loop sau khi report xong
    [ ] Reuse existing context (không chạy lại pipeline)
[ ] --no-tui flag (skip TUI, plain terminal output)
[ ] TUI auto-skip khi output bị pipe
[ ] TUI tests (Textual test client)
[ ] Cập nhật CHANGELOG.md và ROADMAP.md
```

**Definition of Done:** Full TUI workflow từ Dashboard → Chart Selector → Preview → Export hoạt động với keyboard.

---

## Phase 4 — Exporters & Multi-file

> Branch: `phase-4-export`
> Mục tiêu: Tất cả output formats + multi-file join

```
[ ] Exporters:
    [ ] Abstract BaseExporter
    [ ] HTML exporter (Plotly, self-contained)
    [ ] Markdown exporter (base64 images)
    [ ] PDF exporter (Matplotlib + WeasyPrint)
    [ ] Jupyter Notebook exporter (nbformat)
    [ ] Vietnamese font support trong PDF

[ ] Multi-file:
    [ ] Auto schema detection across files
    [ ] Auto join key inference (AI)
    [ ] --join-on flag (explicit)
    [ ] --join-type flag (inner/left/outer)

[ ] XLSX improvements:
    [ ] Multi-sheet listing
    [ ] --sheet flag
    [ ] TUI sheet selector

[ ] Export tests:
    [ ] HTML output is valid HTML5
    [ ] PDF output is valid PDF
    [ ] Markdown output có embedded images
    [ ] Notebook output có valid nbformat
    [ ] Multi-file inner join result
    [ ] Multi-file left join result

[ ] Cập nhật CHANGELOG.md và ROADMAP.md
```

**Definition of Done:** Tất cả 4 output formats hoạt động với `small_sales.csv`. Multi-file join hoạt động với `multi_file_a.csv` + `multi_file_b.csv`.

---

## Phase 5 — Polish & PyPI

> Branch: `phase-5-pypi`
> Mục tiêu: Production-ready, publishable

```
[ ] Documentation:
    [ ] docs/setup-windows.md — đầy đủ, step-by-step
    [ ] docs/setup-linux-mac.md
    [ ] docs/cli-reference.md — tất cả flags + examples
    [ ] docs/agent-architecture.md — diagrams + tool lists
    [ ] docs/configuration.md — config JSON reference
    [ ] docs/tool-registry.md — registry.json format
    [ ] docs/dashboard-templates.md — template customization
    [ ] docs/dev-log.md — finalized

[ ] README.md:
    [ ] Install instructions
    [ ] Quickstart với examples
    [ ] Screenshots/GIFs của TUI
    [ ] Provider setup section
    [ ] Link đến docs

[ ] CONTRIBUTING.md:
    [ ] Branch rules
    [ ] Commit style
    [ ] Test requirements
    [ ] How to add a new tool
    [ ] How to add a new provider

[ ] Code quality:
    [ ] Test coverage ≥ 80%
    [ ] Không có bare excepts
    [ ] Tất cả public functions có docstrings
    [ ] Type hints đầy đủ

[ ] pyproject.toml:
    [ ] Classifiers đầy đủ
    [ ] Keywords
    [ ] License
    [ ] URLs (homepage, docs, issues)

[ ] Sample test suite:
    [ ] tests/samples/ runnable bởi end users
    [ ] README note về requirements (API key cần thiết)

[ ] Build + Publish:
    [ ] python -m build
    [ ] Test trên TestPyPI
    [ ] pip install --index-url https://test.pypi.org/simple/ dataviz
    [ ] Verify install + basic run
    [ ] twine upload dist/*
    [ ] git tag v0.1.0

[ ] Final:
    [ ] CHANGELOG.md entry cho v0.1.0
    [ ] ROADMAP.md đánh dấu tất cả phases complete
    [ ] GitHub Release với release notes
```

**Definition of Done:** `pip install dataviz` từ PyPI hoạt động, `dataviz mydata.csv` tạo report thành công.

---

## Dependency Map Giữa Các Phases

```
Phase 0 (skeleton)
    ↓
Phase 1 (config + readers + cache)
    ↓
Phase 2 (agents + LLM + tools)    ← Core value delivered here
    ↓
Phase 3 (TUI)                      ← Có thể song song với Phase 4
Phase 4 (exporters + multi-file)   ← Có thể song song với Phase 3
    ↓
Phase 5 (polish + PyPI)
```

Phase 3 và 4 có thể làm song song (branches độc lập nhau, merge vào cùng target khi xong).