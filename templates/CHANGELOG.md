# Changelog

All notable changes to DataViz CLI are documented here.
Each completed phase is one section. Changes within a phase are grouped by type.

Format per entry: `short description (module or file affected)`

---

## [Unreleased]

Changes that are merged but not yet tagged as a release.

### Added

### Fixed

### Changed

### Removed

---

## Phase 0 — Repository Initialization

Initial repository setup. All work on `main`.

### Added

- Project structure and package skeleton
- `pyproject.toml` with dependencies and metadata
- `.gitignore` for Python projects
- Document templates: `README`, `CHANGELOG`, `CONTRIBUTING`, `AGENT_RULE`
- `ROADMAP.md` with full phase breakdown
- `SPEC.md` with full system specification
- `specs/config-schema.json` — JSON schema for config validation
- `dataviz/tools/registry.json` — empty tool registry, populated in Phase 1
- `dataviz/templates/dashboard/default.json` — default dashboard layout template
- `docs/setup-windows.md` skeleton
- `dataviz/tools/generated/.gitkeep`

---

<!--
HOW TO ADD A NEW SECTION
========================

Copy this block above the previous latest phase section and fill it in:

## Phase N — Short Phase Name

Brief one-line description of what this phase delivered.
Branch: `phase-N-short-name`

### Added
- feature or file added (module)

### Fixed
- bug description and what caused it (module)

### Changed
- what changed and why (module)

### Removed
- what was removed and why (module)

Rules:
- One section per completed phase.
- Do not add entries for work in progress — only completed, tested, committed work.
- Keep entries short and specific. Bad: "fixed stuff". Good: "fix null detection when entire column is NaN (eda_tools.py)".
- The phase section header must include the phase number and name exactly as in ROADMAP.md.
-->