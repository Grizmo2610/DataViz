# DataViz

DataViz is a CLI for automated tabular data analysis, chart selection, and report export.

## Install

```bash
pip install -e .
```

## Tutorial

### 1. See the CLI

```bash
python -m dataviz --help
```

### 2. Configure a provider

```bash
python -m dataviz config set --provider claude --key sk-ant-...
python -m dataviz config show
```

### 3. Analyze a single file

```bash
python -m dataviz sales.csv --output html --no-tui
```

This prints a summary, reads the file with the matching reader, and writes a report artifact to `./dataviz_output/report.html`.

### 4. Use another output format

```bash
python -m dataviz sales.csv --output md --no-tui
python -m dataviz sales.csv --output pdf --no-tui
python -m dataviz sales.csv --output notebook --no-tui
```

### 5. Analyze multiple files

```bash
python -m dataviz orders.csv customers.csv --join-on customer_id --output html --no-tui
```

If you do not pass `--join-on`, DataViz tries to infer a join key from the shared columns.

### 6. Reuse a saved session

```bash
python -m dataviz sales.csv --session q3-review --no-tui
python -m dataviz session list
python -m dataviz session open q3-review
```

### 7. Clear cache or inspect pending tools

```bash
python -m dataviz cache clear
python -m dataviz tool-gen list
```

## Current scope

- Phase 5 polish is in progress
- The TUI is a terminal dashboard model, not a full interactive Textual UI yet
- Exporters currently write working report files for smoke testing and development

## Docs

- [Design overview](design/README.md)
- [Roadmap](ROADMAP.md)
