# Changelog

All notable changes to DataViz CLI will be documented here.

## [Unreleased]

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

### Changed
- `design/README.md` index updated to match the actual design file names
- CLI default command now summarizes input files through the reader layer
- `AGENT_RULE.md` removed in favor of `AGENTS.md`

## Phase 0 - Repository Initialization

### Added
- Project skeleton, docs, and template assets
- Empty tool registry and dashboard template
