# Roadmap

## Phase 0 - Repository Initialization

Branch: `phase-0-repo-initialization`

- [x] Initialize git repo
- [x] Create `pyproject.toml` with project metadata
- [ ] Create `docs/templates/` and document templates first
- [x] Write `README.md`
- [x] Write `CHANGELOG.md`
- [x] Write `CONTRIBUTING.md`
- [x] Write `AGENT_RULE.md`
- [x] Write `ROADMAP.md`
- [x] Create `.gitignore`
- [x] Create package skeleton under `dataviz/`
- [x] Create `dataviz/tools/generated/.gitkeep`
- [x] Create `dataviz/templates/dashboard/default.json`
- [x] Create `dataviz/tools/registry.json`
- [x] Create `docs/setup-windows.md`
- [ ] Initial commit on the branch

Definition of done:
- `python -m dataviz --help` runs without crashing

## Phase 1 - Core Pipeline

Branch: `phase-1-core-pipeline`

- [x] CLI entry point with subcommands and help output
- [x] Config set, update, and show commands
- [x] Config resolution by field
- [x] Reader base classes and file readers
- [x] Cache system
- [x] Session system
- [x] Cache and session subcommands
- [x] Unit tests for config, readers, cache, and session

Definition of done:
- `python -m dataviz --help` runs without crashing
- Unit tests for the core pipeline pass

## Phase 2 - Agents

Branch: `phase-2-agents`

- [x] Provider layer
- [x] Tool system
- [x] Base agent classes
- [x] Reader, EDA, Viz, and Report agents
- [x] Orchestrator and retry logic

Definition of done:
- The phase 2 test suite passes

## Phase 3 - TUI

Branch: `phase-3-tui`

- [x] Textual app skeleton
- [x] Dashboard, chart selector, preview, insight, and export screens
- [x] Progress and log components

Definition of done:
- The TUI screen models and launch gate pass the phase 3 tests

## Phase 4 - Export

Branch: `phase-4-export`

- [x] Exporters
- [x] Multi-file join support
- [x] XLSX improvements

Definition of done:
- The export and multi-file test suite passes

## Phase 5 - Polish

Branch: `phase-5-pypi`

- [ ] Documentation
- [ ] Code quality cleanup
- [ ] Packaging and publish flow
