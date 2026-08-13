# 08 — CLI Flags & Modes

## Entry Point

```bash
dataviz <file> [files...] [OPTIONS]
```

Dùng **Typer** — auto-generates `--help`, type validation, và subcommands.

---

## Full Flag Reference

```
Arguments:
  file          Một hoặc nhiều input files (CSV, XLSX, Parquet)

Options:
  --output      Output format: html | md | pdf | notebook   [default: html]
  --out-dir     Output directory                            [default: ./dataviz_output]
  --lang        Report language: en | vi | auto             [default: auto]
  --fast        Fast mode: ít charts, quick analysis
  --deep        Deep mode: thorough analysis, nhiều charts hơn
  --interactive Launch interactive Q&A session sau khi report xong
  --focus TEXT  Hướng dẫn AI tập trung vào gì (vd: "sales trends by region")
  --sheet TEXT  Sheet name cho XLSX files                   [default: first sheet]
  --join-on     Tên cột để join nhiều files
  --join-type   Join type: inner | left | outer             [default: inner]
  --provider    Override default LLM provider cho lần chạy này
  --model       Override default model cho lần chạy này
  --no-cache    Bỏ qua cache, force re-analysis
  --session     Đặt tên session để lưu và truy xuất sau
  --no-tui      Tắt TUI, chỉ output ra terminal
  --version     Hiển thị version và thoát
  --help        Hiển thị help message

Subcommands:
  dataviz config set      Set API key và provider
  dataviz config update   Update config đã có
  dataviz config show     Hiển thị config hiện tại (keys bị mask)
  dataviz session list    Liệt kê saved sessions
  dataviz session open    Mở lại một saved session
  dataviz cache clear     Xoá local cache
  dataviz tool-gen list   Hiển thị pending tool requests
  dataviz tool-gen run    Generate pending tools
  dataviz tool-gen discard Xoá pending tool requests
```

---

## Mode Comparison

| Flag | Charts | Depth | Speed | Use case |
|---|---|---|---|---|
| `--fast` | 3–5 | Surface only | Nhanh | Preview nhanh, file lớn |
| (default) | 6–10 | Balanced | Vừa | Phân tích thông thường |
| `--deep` | 10–20+ | Full EDA + insights | Chậm | Phân tích kỹ lưỡng |

---

## Examples

### Cơ bản

```bash
# Phân tích CSV, output HTML
dataviz sales.csv

# Chỉ định format
dataviz sales.csv --output pdf

# Fast mode cho preview nhanh
dataviz bigfile.parquet --fast

# Deep analysis
dataviz data.csv --deep --output notebook
```

### Hướng dẫn focus

```bash
# AI sẽ ưu tiên phân tích revenue theo region
dataviz sales.csv --focus "revenue trends by region"

# Tập trung vào missing values
dataviz data.csv --focus "data quality and missing values"
```

### Multi-file

```bash
# Auto-detect join key
dataviz sales.csv customers.xlsx

# Explicit join key
dataviz sales.csv customers.xlsx --join-on customer_id

# Outer join
dataviz orders.csv products.csv --join-on product_id --join-type outer
```

### Provider override

```bash
# Dùng OpenAI cho lần này (dù default là claude)
dataviz data.csv --provider openai

# Dùng model cụ thể
dataviz data.csv --provider openai --model gpt-4-turbo
```

### Session management

```bash
# Lưu session
dataviz data.csv --session q3-analysis

# Xem danh sách sessions
dataviz session list

# Mở lại session
dataviz session open q3-analysis
```

### XLSX multi-sheet

```bash
# Sheet mặc định (đầu tiên)
dataviz report.xlsx

# Sheet cụ thể
dataviz report.xlsx --sheet "Q3 Revenue"
```

### Config

```bash
# Set Claude
dataviz config set --provider claude --key sk-ant-...

# Set OpenAI compatible (Groq)
dataviz config set --provider openai --key gsk_...
dataviz config update --provider openai --model llama-3.1-70b

# Xem config
dataviz config show
```

---

## CLI Implementation (Typer)

**File:** `dataviz/cli.py`

```python
import typer
from typing import Optional

app = typer.Typer(name="dataviz", help="Automated data visualization CLI.")

@app.command()
def main(
    files: list[str] = typer.Argument(..., help="Input files (CSV, XLSX, Parquet)"),
    output: str = typer.Option("html", "--output", help="Output format: html|md|pdf|notebook"),
    out_dir: str = typer.Option("./dataviz_output", "--out-dir"),
    lang: str = typer.Option("auto", "--lang"),
    fast: bool = typer.Option(False, "--fast"),
    deep: bool = typer.Option(False, "--deep"),
    interactive: bool = typer.Option(False, "--interactive"),
    focus: Optional[str] = typer.Option(None, "--focus"),
    sheet: Optional[str] = typer.Option(None, "--sheet"),
    join_on: Optional[str] = typer.Option(None, "--join-on"),
    join_type: str = typer.Option("inner", "--join-type"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    no_cache: bool = typer.Option(False, "--no-cache"),
    session: Optional[str] = typer.Option(None, "--session"),
    no_tui: bool = typer.Option(False, "--no-tui"),
):
    """Analyze tabular data files and generate visualizations."""
    ...

# Config subcommands
config_app = typer.Typer()
app.add_typer(config_app, name="config")

@config_app.command("set")
def config_set(
    provider: str = typer.Option(..., "--provider"),
    key: str = typer.Option(..., "--key"),
):
    """Set API key for a provider."""
    ...

@config_app.command("update")
def config_update(
    provider: str = typer.Option(..., "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
):
    """Update provider settings."""
    ...

@config_app.command("show")
def config_show():
    """Display current config (keys masked)."""
    ...

# Session subcommands
session_app = typer.Typer()
app.add_typer(session_app, name="session")

# Cache subcommands
cache_app = typer.Typer()
app.add_typer(cache_app, name="cache")

# Tool-gen subcommands
toolgen_app = typer.Typer()
app.add_typer(toolgen_app, name="tool-gen")
```

---

## `--interactive` Mode

Sau khi report được tạo xong, `--interactive` mở Q&A session:

```
✅ Report generated: ./dataviz_output/report.html

Interactive mode — type questions about your data.
Type 'exit' to quit.

> What's the main driver of revenue growth?
> Show me the top 5 products by revenue
> Is there correlation between discount rate and returns?
```

Agent nhận câu hỏi, tra cứu context đã có (schema, stats, charts), trả lời dựa trên kết quả phân tích đã có — không chạy lại pipeline.

---

## Error Messages

Tất cả error messages phải rõ ràng, có actionable hint:

```
❌ Error: No API key configured for provider 'claude'.
   Run: dataviz config set --provider claude --key sk-ant-...

❌ Error: File not found: 'sales.cvs'
   Did you mean: 'sales.csv'?

❌ Error: Cannot determine join key between 'orders.csv' and 'customers.csv'.
   Specify manually: --join-on customer_id

❌ Error: Sheet 'Q4 Revenue' not found in 'report.xlsx'.
   Available sheets: Q1 Revenue, Q2 Revenue, Q3 Revenue
```