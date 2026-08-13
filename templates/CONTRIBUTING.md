# Contributing to DataViz CLI

Thank you for contributing. This guide covers everything you need to set up, develop, test, and submit changes correctly.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup on Windows](#setup-on-windows)
- [Setup on Linux / macOS](#setup-on-linux--macos)
- [Project structure overview](#project-structure-overview)
- [Before you write any code](#before-you-write-any-code)
- [Branch and commit rules](#branch-and-commit-rules)
- [Code style](#code-style)
- [Testing](#testing)
- [Updating the changelog](#updating-the-changelog)
- [Submitting changes](#submitting-changes)

---

## Prerequisites

- Python 3.11 or higher
- Git
- A terminal (PowerShell or Command Prompt on Windows, bash/zsh on Linux/macOS)
- An API key for at least one supported LLM provider (Claude, OpenAI, Gemini, or OpenAI-compatible)

---

## Setup on Windows

**1. Install Python 3.11+**

Download from [python.org](https://www.python.org/downloads/).
During installation, check **"Add Python to PATH"**.

Verify:
```bat
python --version
```

**2. Clone the repository**

```bat
git clone https://github.com/your-org/dataviz.git
cd dataviz
```

**3. Create a virtual environment**

```bat
python -m venv .venv
```

**4. Activate the virtual environment**

```bat
.venv\Scripts\activate
```

You should see `(.venv)` at the start of your prompt.

If you get an execution policy error, run this first in PowerShell as administrator:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**5. Upgrade pip**

```bat
python -m pip install --upgrade pip
```

**6. Install the package in editable mode with dev dependencies**

```bat
pip install -e ".[dev]"
```

**7. Set your API key**

```bat
dataviz config set --provider claude --key sk-ant-...
dataviz config show
```

**8. Verify everything works**

```bat
dataviz --help
python -m pytest tests/ -v
```

---

## Setup on Linux / macOS

**1. Clone the repository**

```bash
git clone https://github.com/your-org/dataviz.git
cd dataviz
```

**2. Create and activate a virtual environment**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**3. Install with dev dependencies**

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

**4. Set your API key and verify**

```bash
dataviz config set --provider claude --key sk-ant-...
dataviz --help
python -m pytest tests/ -v
```

---

## Project structure overview

Read `SPEC.md` for the full specification. The key areas for contributors:

```
dataviz/
├── agents/         # Agent logic — only tool calls, no direct I/O
├── tools/          # All tool implementations + registry.json
│   └── generated/  # Auto-generated tools — never edit manually
├── providers/      # LLM provider adapters (OpenAI, Claude, Gemini)
├── readers/        # File readers (CSV, XLSX, Parquet)
├── exporters/      # Output exporters (HTML, MD, PDF, Notebook)
├── tui/            # Textual TUI screens and components
└── templates/      # Dashboard layout templates (JSON)
```

---

## Before you write any code

1. Read `AGENT_RULE.md` — the rules that govern all development on this project.
2. Read `SPEC.md` — the full system specification.
3. Read `ROADMAP.md` — the current phase and active tasks.
4. Read the source files in the area you plan to modify.
5. Check `dataviz/tools/registry.json` before assuming a tool exists or does not exist.

---

## Branch and commit rules

**Never commit directly to `main`.**
Phase 0 (repo initialization) is the only exception.

**Create a branch for your work:**

```bat
# Windows
git checkout -b feat/your-feature-name

# Linux / macOS
git checkout -b feat/your-feature-name
```

Branch naming:
- `phase-N-short-description` — for phase work
- `feat/short-description` — for new features
- `fix/short-description` — for bug fixes
- `docs/short-description` — for documentation only changes

**Commit rules:**
- Commit after each meaningful, self-contained change.
- Message must be clear and specific.
- Good: `add chunked parquet reader for files over 1M rows`
- Good: `fix null detection when entire column is NaN in eda_tools`
- Bad: `fix`, `wip`, `update`, `changes`
- Never commit code with failing tests.

**Run tests before every commit:**

```bat
python -m pytest tests/ -v
```

---

## Code style

- All variable names, function names, file paths, module names: **English only**
- All comments and docstrings: **English only**
- Every function and class must have a **Google-style docstring**
- Use plain inline comments: `# this does X`
- No section dividers: never `# ===`, `# ---`, `# ***`
- No file-level summary block at the top of Python files

**Docstring format:**

```python
def read_sample(file_path: str, n_rows: int = 20) -> pd.DataFrame:
    """Read the first N rows of a file for schema inspection.

    Args:
        file_path: Absolute or relative path to the input file.
        n_rows: Number of rows to read. Defaults to 20.

    Returns:
        A DataFrame containing the sampled rows.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnsupportedFormatError: If the file extension is not supported.
    """
```

**Agent & tool separation rule:**
Agents only call tools. Agents never call pandas, plotly, or matplotlib directly.
All side effects live inside tool functions. See `SPEC.md` and `AGENT_RULE.md` for details.

**Config files:**
All config uses plain JSON (`.json`). No TOML, YAML, or JSONC.

---

## Testing

Tests live in `tests/`. Three categories:

| Category | Location | Purpose |
|---|---|---|
| Unit tests | `tests/unit/` | Individual functions and tools |
| Integration tests | `tests/integration/` | Full pipeline with mocked LLM |
| Sample tests | `tests/samples/` | User-runnable end-to-end examples |

**Run all tests:**

```bat
python -m pytest tests/ -v --cov=dataviz --cov-report=term-missing
```

**Run a specific file:**

```bat
python -m pytest tests/unit/test_readers.py -v
```

**Run sample tests only:**

```bat
python -m pytest tests/samples/ -v
```

Code is not done until all tests pass. Fix test failures before committing.

If you add a new feature, add tests for it in the appropriate category.
Fixture files (sample CSV, XLSX, Parquet) go in `tests/fixtures/`.

---

## Updating the changelog

After completing any significant piece of work, update `CHANGELOG.md`:

1. Add your changes under `## [Unreleased]` in the appropriate group (`Added`, `Fixed`, `Changed`, `Removed`).
2. When a phase is fully complete, move the unreleased entries into a new phase section following the format in `templates/CHANGELOG.md`.

Keep entries short and specific. Reference the affected module or file in parentheses.

---

## Submitting changes

1. Make sure all tests pass: `python -m pytest tests/ -v`
2. Make sure `CHANGELOG.md` is updated.
3. Make sure `ROADMAP.md` reflects current task status.
4. Push your branch: `git push origin feat/your-feature-name`
5. Open a pull request against `main`.
6. Do not merge your own PR — wait for review.

If you are the sole developer, open the PR anyway and review your own diff before merging.
This catches mistakes that are invisible when writing code.