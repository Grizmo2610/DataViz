# Agent Rules — DataViz CLI

Rules that govern how AI agents (coding agents, LLM assistants) work on this codebase.
Read this file before reading anything else. These rules are non-negotiable.

---

## Reading files

- Always list the top-level directory first, then decide which subdirectories to open.
- Read files selectively based on what the current task actually needs.
- Never read the entire file tree blindly.
- Never use link-tree-style output as a substitute for reading actual file content.
- If a file's name is ambiguous, open it and read the first 20–30 lines to confirm relevance before reading further.

## Before writing any code

- Read `SPEC.md` (or the relevant spec file) before touching any code.
- Read `ROADMAP.md` to understand which phase is active and what the current task scope is.
- Read `AGENTS.md` at the start of every session.
- Read the relevant existing source files in the area you will modify — do not assume their content.
- Check `dataviz/tools/registry.json` before assuming a tool exists or does not exist.

## Branch rules

- All work after Phase 0 must happen on a dedicated branch.
- Branch naming: `phase-N-short-description` for phases, `feat/short-description` for standalone features, `fix/short-description` for bug fixes.
- Never commit directly to `main` after Phase 0.
- Never merge into `main` without explicit instruction from the project owner.

## Commit rules

- Commit after every meaningful, self-contained change — not after every file save.
- Commit messages must be clear and specific. Describe what changed and why.
- Good: `add chunked parquet reader for large file support`
- Good: `fix null detection when entire column is NaN`
- Bad: `fix bug`, `wip`, `update`, `changes`
- Never commit broken code. Run tests before committing.

## Code must be tested before it is done

- Writing code is not done. Code is done when tests pass.
- Run the relevant test suite after every significant change.
- If tests fail, fix them before moving to the next task.
- Never skip tests to save time.

## Code style

- All variable names, function names, file paths, module names: English only.
- All comments and docstrings: English only.
- Report language (user-facing output) is controlled by `--lang` flag — not hardcoded.
- Every function and class must have a Google-style docstring.
- Use plain inline comments: `# this does X`
- Never use section dividers in comments: no `# ===`, `# ---`, `# ***`, `# >>>`.
- No file-level summary block at the top of source files.

## Docstring format (Google style)

```python
def function_name(arg1: type, arg2: type) -> return_type:
    """One-line summary of what this function does.

    Longer description if needed. Explain the why, not just the what.

    Args:
        arg1: Description of arg1.
        arg2: Description of arg2.

    Returns:
        Description of the return value.

    Raises:
        ErrorType: When and why this error is raised.
    """
```

## Agent & tool separation

- Agents decide what to do. Tools do the actual work.
- Agents never call pandas, plotly, matplotlib, or any I/O library directly.
- Agents never build HTML, Markdown, or chart strings inline.
- Agents never read files directly — always call a reader tool.
- Every side effect (file read, stat computation, chart render, file write) lives inside a tool function.
- If a task cannot be done with existing tools, follow the dynamic tool generation flow defined in `SPEC.md`.

## Tool registry

- `dataviz/tools/registry.json` is the single source of truth for all available tools.
- Any new tool (built-in or generated) must be registered there before agents can use it.
- Never add generated tool code to core tool files (`reader_tools.py`, `eda_tools.py`, etc.).
- Generated tools go to `dataviz/tools/generated/` only.

## Changelog

- Update `CHANGELOG.md` at the end of every completed phase.
- Each phase is one section in the changelog.
- Use the format defined in `templates/CHANGELOG.md`.
- Never leave `CHANGELOG.md` empty or stale after a phase is done.

## Roadmap tracking

- Update `ROADMAP.md` when starting a phase (mark tasks in progress) and when finishing (mark tasks done).
- If a task turns out to be more complex than the roadmap describes, add sub-tasks inline — do not silently skip them.

## Templates

- All document files (README, CHANGELOG, CONTRIBUTING, AGENT_RULE) must be created from their templates in `docs/templates/`.
- If a template does not exist for a document type you need, create the template first, then create the document from it.
- Never create a document file from scratch if a template exists.

## Config files

- All config files use plain JSON (`.json`). No TOML, YAML, or JSONC.
- Validate config structure against `specs/config-schema.json` when loading.
- Never hardcode API keys, model names, or provider URLs in source code.

## What not to do

- Do not read files as a link tree and treat that as understanding the codebase.
- Do not merge into `main` without explicit instruction.
- Do not commit code that has failing tests.
- Do not write tools inside agent files — tools and agents are separate modules.
- Do not add sections dividers (`# ===`, `# ---`) in source files.
- Do not write a file-level docstring summary at the top of Python files.
- Do not use TOML or YAML for any config file.
- Do not put generated tool code into core tool files.
- Do not skip updating `CHANGELOG.md` and `ROADMAP.md` after completing a phase.
