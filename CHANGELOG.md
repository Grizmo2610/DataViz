# Changelog

All notable changes to DataViz CLI will be documented here.
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
