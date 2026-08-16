# Usage Guide

## Command Reference

```
dataviz [files...] [options]
dataviz config set   --provider NAME --key KEY [--model MODEL] [--base-url URL]
dataviz config update --provider NAME [--key KEY] [--model MODEL] [--base-url URL]
dataviz config show
dataviz session list
dataviz session open NAME
dataviz cache clear
dataviz tool-gen list
dataviz tool-gen run
dataviz tool-gen discard
dataviz --version
```

---

## Analyzing a File

```bash
dataviz sales.csv --output html --no-tui
```

### Output Formats

```bash
# HTML (default) — interactive charts with zoom and tooltips
dataviz sales.csv --output html --no-tui

# PDF — A4 layout, suitable for printing or email
dataviz sales.csv --output pdf --no-tui

# Markdown — plain text, easy to embed in wikis or Git repos
dataviz sales.csv --output md --no-tui

# Jupyter Notebook — open in JupyterLab for further analysis
dataviz sales.csv --output notebook --no-tui
```

### Other Analysis Options

```bash
# Custom output directory
dataviz sales.csv --output html --out-dir ./reports/q3 --no-tui

# Select a sheet from an Excel file
dataviz data.xlsx --sheet "Sheet2" --output html --no-tui

# Focus analysis on a specific topic
dataviz sales.csv --focus "revenue trends by region" --output html --no-tui

# Set the report language
dataviz sales.csv --lang en --output html --no-tui    # English
dataviz sales.csv --lang vi --output html --no-tui    # Vietnamese
dataviz sales.csv --lang auto --output html --no-tui  # Auto-detect (default)

# Fast mode — samples and basic stats only
dataviz sales.csv --fast --output html --no-tui

# Deep mode — adds correlation, outlier detection, and time-series analysis
dataviz sales.csv --deep --output html --no-tui
```

---

## Multi-file Join

```bash
# Auto-infer the join key (files must share a column with the same name)
dataviz orders.csv customers.csv --output html --no-tui

# Specify the join key explicitly
dataviz orders.csv customers.csv --join-on customer_id --output html --no-tui

# Specify the join type
dataviz orders.csv customers.csv --join-on customer_id --join-type inner --output html --no-tui
dataviz orders.csv customers.csv --join-on customer_id --join-type left  --output html --no-tui
dataviz orders.csv customers.csv --join-on customer_id --join-type outer --output html --no-tui
```

> **Large files:** DataViz will warn when a file exceeds 500,000 rows. Make sure you have enough RAM before joining large datasets.

---

## Sessions

Sessions let you save and reopen analysis results.

```bash
# Run and save a named session
dataviz sales.csv --session q3-review --output html --no-tui

# List saved sessions
dataviz session list

# Reopen a session
dataviz session open q3-review
```

---

## Cache

```bash
# Clear all cached files
dataviz cache clear

# Skip the cache for a single run
dataviz sales.csv --no-cache --output html --no-tui
```

---

## Tool Generation

```bash
# List pending tool-gen tasks
dataviz tool-gen list

# Run all pending tasks
dataviz tool-gen run

# Discard all pending tasks
dataviz tool-gen discard
```

---

## All Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--output` | `html` | Output format: `html`, `pdf`, `md`, `notebook` |
| `--out-dir` | `./dataviz_output` | Directory for the report |
| `--lang` | `auto` | Report language: `en`, `vi`, `auto` |
| `--fast` | off | Fast analysis mode |
| `--deep` | off | Deep analysis mode |
| `--focus` | — | Topic hint for the LLM |
| `--sheet` | — | Sheet name for Excel files |
| `--join-on` | — | Column name to join on |
| `--join-type` | `inner` | Join type: `inner`, `left`, `outer` |
| `--provider` | from config | Override LLM provider for this run |
| `--model` | from config | Override model for this run |
| `--no-cache` | off | Skip the cache |
| `--session NAME` | — | Save results to a named session |
| `--no-tui` | off | Run in plain CLI mode (no TUI) |
| `--template` | `default` | Dashboard template name |
| `--version` | — | Print version and exit |

---

## Output Structure

```
dataviz_output/
├── report.html      # Interactive HTML report
├── report.pdf       # PDF report  (--output pdf)
├── report.md        # Markdown report  (--output md)
└── report.ipynb     # Jupyter Notebook  (--output notebook)
```
