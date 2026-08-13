# 11 — Project Structure

## Cây Thư Mục Đầy Đủ

```
dataviz/
├── dataviz/                              # Main package
│   ├── __init__.py                       # Package version: __version__ = "0.1.0"
│   ├── cli.py                            # Typer CLI entry point + tất cả subcommands
│   ├── config.py                         # Config loading, resolution, JSON read/write
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                       # Abstract agent interface (BaseAgent)
│   │   ├── orchestrator.py               # Pipeline coordination, shared context, retry
│   │   ├── reader.py                     # File I/O, sampling, schema extraction
│   │   ├── eda.py                        # Statistical analysis, full-data pass
│   │   ├── viz.py                        # Chart selection, chart generation
│   │   └── report.py                     # Narrative, insights, assemble_dashboard call
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.json                 # Master list of all tools (built-in + generated)
│   │   ├── loader.py                     # ToolRegistry: dynamic load from registry.json
│   │   ├── reader_tools.py               # read_sample, detect_schema, read_full_stats
│   │   ├── eda_tools.py                  # compute_descriptive_stats, detect_nulls, ...
│   │   ├── viz_tools.py                  # plot_histogram, plot_bar, ..., auto_select_charts
│   │   ├── report_tools.py               # write_summary, write_insights, assemble_dashboard
│   │   └── generated/                    # Auto-generated tools — KHÔNG edit thủ công
│   │       └── .gitkeep
│   │
│   ├── templates/
│   │   └── dashboard/
│   │       └── default.json              # Built-in default dashboard layout template
│   │
│   ├── providers/
│   │   ├── __init__.py                   # get_provider() factory function
│   │   ├── base.py                       # Abstract BaseProvider (chat, format_tools)
│   │   ├── openai_provider.py            # OpenAI + OpenAI-compatible via base_url
│   │   ├── claude_provider.py            # Anthropic Claude
│   │   └── gemini_provider.py            # Google Gemini
│   │
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── app.py                        # Textual App entry point, screen routing
│   │   ├── screens/
│   │   │   ├── __init__.py
│   │   │   ├── dashboard.py              # Overview: schema summary, stats, agent log
│   │   │   ├── chart_selector.py         # Navigate charts với keyboard
│   │   │   ├── chart_preview.py          # Preview chart (browser hoặc inline Sixel)
│   │   │   ├── insight.py                # Scrollable insight narrative
│   │   │   └── export.py                 # Chọn format, trigger export
│   │   └── components/
│   │       ├── __init__.py
│   │       ├── progress.py               # ProgressBar + Spinner per agent
│   │       └── log_panel.py              # Real-time agent activity feed
│   │
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── base.py                       # Abstract BaseExporter
│   │   ├── html_exporter.py              # Self-contained Plotly HTML
│   │   ├── md_exporter.py                # Markdown + base64 embedded images
│   │   ├── pdf_exporter.py               # Matplotlib + WeasyPrint
│   │   └── notebook_exporter.py          # nbformat Jupyter notebook
│   │
│   ├── readers/
│   │   ├── __init__.py
│   │   ├── base.py                       # Abstract BaseReader
│   │   ├── csv_reader.py                 # Auto-detect delimiter, scale strategy
│   │   ├── xlsx_reader.py                # Multi-sheet support, --sheet flag
│   │   └── parquet_reader.py             # Lazy read với polars
│   │
│   ├── cache.py                          # SHA256 cache key, read/write .dataviz/cache/
│   ├── session.py                        # Session save/load/list
│   ├── tool_gen.py                       # Dynamic tool gen + pending_tools.json queue
│   └── utils.py                          # Shared utilities (logging, file helpers, ...)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                        # Shared pytest fixtures
│   │
│   ├── unit/
│   │   ├── test_config.py                 # Config resolution, JSON read/write
│   │   ├── test_readers.py                # CSV/XLSX/Parquet readers
│   │   ├── test_eda_tools.py              # EDA tool functions
│   │   ├── test_viz_tools.py              # Chart generation (mock matplotlib/plotly)
│   │   ├── test_registry.py              # ToolRegistry load/get/list_for_agent
│   │   ├── test_tool_gen.py              # Dynamic tool generation
│   │   ├── test_cache.py                  # Cache hash, read, write, invalidation
│   │   └── test_session.py               # Session save, list, open
│   │
│   ├── integration/
│   │   ├── test_pipeline_mock.py          # Full pipeline với mocked LLM
│   │   └── test_multi_file.py             # Multi-file join logic
│   │
│   ├── samples/
│   │   └── test_basic_run.py             # User-runnable end-to-end tests
│   │
│   └── fixtures/
│       ├── small_sales.csv               # < 100 rows, simple types
│       ├── medium_timeseries.csv         # 50k rows, date column
│       ├── wide_data.xlsx                # 80+ columns
│       ├── nulls_heavy.csv               # High null percentage
│       ├── multi_file_a.csv              # Join testing — file A
│       └── multi_file_b.csv              # Join testing — file B
│
├── docs/
│   ├── templates/                         # Document templates (tạo trước khi dùng)
│   │   ├── README.template.md
│   │   ├── CHANGELOG.template.md
│   │   ├── CONTRIBUTING.template.md
│   │   └── AGENT_RULE.template.md
│   ├── setup-windows.md                   # Step-by-step Windows guide
│   ├── setup-linux-mac.md
│   ├── configuration.md                   # Config JSON reference
│   ├── cli-reference.md                   # All flags and subcommands
│   ├── agent-architecture.md              # Agent pipeline + tool separation
│   ├── tool-registry.md                   # registry.json format, adding tools
│   ├── dashboard-templates.md             # Template format và customization
│   └── dev-log.md                         # Running development decisions log
│
├── ROADMAP.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── AGENT_RULE.md
├── README.md
├── pyproject.toml
└── .gitignore
```

---

## `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "dataviz"
version = "0.1.0"
description = "Automated data visualization CLI powered by LLM agents"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [{ name = "Your Name", email = "you@example.com" }]

keywords = ["dataviz", "cli", "data", "visualization", "llm", "eda", "ai"]

classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Visualization",
]

dependencies = [
    "typer>=0.12",
    "textual>=0.60",
    "pandas>=2.0",
    "polars>=0.20",
    "plotly>=5.0",
    "matplotlib>=3.8",
    "seaborn>=0.13",
    "openpyxl>=3.1",
    "pyarrow>=14.0",
    "weasyprint>=60.0",
    "nbformat>=5.9",
    "anthropic>=0.25",
    "openai>=1.30",
    "google-generativeai>=0.5",
    "rich>=13.0",
]

[project.scripts]
dataviz = "dataviz.cli:app"

[project.urls]
Homepage = "https://github.com/yourname/dataviz"
Documentation = "https://github.com/yourname/dataviz/docs"
Issues = "https://github.com/yourname/dataviz/issues"

[tool.hatch.build.targets.wheel]
packages = ["dataviz"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]

[tool.coverage.run]
source = ["dataviz"]
omit = ["dataviz/tools/generated/*", "tests/*"]
```

---

## Module Dependency Graph

```
cli.py
  └── config.py
  └── agents/orchestrator.py
        ├── agents/reader.py
        │     └── tools/loader.py → tools/reader_tools.py
        ├── agents/eda.py
        │     └── tools/loader.py → tools/eda_tools.py
        ├── agents/viz.py
        │     └── tools/loader.py → tools/viz_tools.py
        └── agents/report.py
              └── tools/loader.py → tools/report_tools.py
                                         └── exporters/
  └── tui/app.py
        └── tui/screens/
        └── tui/components/
  └── cache.py
  └── session.py
  └── tool_gen.py
        └── tools/loader.py (register_generated)

providers/__init__.py (get_provider)
  ├── providers/openai_provider.py
  ├── providers/claude_provider.py
  └── providers/gemini_provider.py
```

---

## Naming Conventions

| Thành phần | Convention | Ví dụ |
|---|---|---|
| Module names | snake_case | `reader_tools.py`, `openai_provider.py` |
| Class names | PascalCase | `BaseAgent`, `ToolRegistry`, `ClaudeProvider` |
| Function names | snake_case | `read_sample`, `detect_schema`, `assemble_dashboard` |
| Tool names (registry) | snake_case | `"read_sample"`, `"plot_histogram"` |
| Constants | UPPER_SNAKE | `GLOBAL_CONFIG_PATH`, `BUILT_IN_DEFAULTS` |
| Type aliases | PascalCase | `PipelineContext`, `AgentResult` |