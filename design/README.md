# DataViz CLI - Thiết Kế Tổng Thể

> Tài liệu chỉ mục cho bộ thiết kế của `dataviz`, CLI tool phân tích và trực quan hóa dữ liệu tự động bằng LLM.

---

## Tài Liệu

| File | Nội dung |
|---|---|
| [`00 - roadmap.md`](./00%20-%20roadmap.md) | Tổng quan phase, branch, và tiến độ |
| [`01 - Overview.md`](./01%20-%20Overview.md) | Tổng quan dự án, stack, phân phối |
| [`02 - config.md`](./02%20-%20config.md) | Cấu trúc config JSON và resolution order |
| [`03 - io.md`](./03%20-%20io.md) | Định dạng input/output và data strategy |
| [`04 - agent.md`](./04%20-%20agent.md) | Kiến trúc multi-agent và luồng xử lý |
| [`05 - tools.md`](./05%20-%20tools.md) | Tool registry, danh sách tool, dynamic generation |
| [`06 - providers.md`](./06%20-%20providers.md) | LLM providers: OpenAI, Claude, Gemini |
| [`07 - dashboard.md`](./07%20-%20dashboard.md) | Dashboard assembly và template system |
| [`08 - cli.md`](./08%20-%20cli.md) | CLI flags, subcommands, và modes |
| [`09 - tui.md`](./09%20-%20tui.md) | TUI design, screens, và components |
| [`10 - storage.md`](./10%20-%20storage.md) | Storage layout, cache, và sessions |
| [`11 - structure.md`](./11%20-%20structure.md) | Cấu trúc thư mục dự án |
| [`12 - code-style.md`](./12%20-%20code-style.md) | Code style, agent rules, và git workflow |
| [`13 - testing.md`](./13%20-%20testing.md) | Testing strategy, fixtures, và coverage |
| [`specs/registry.json`](./specs/registry.json) | Tool registry JSON mẫu đầy đủ |
| [`specs/default-template.json`](./specs/default-template.json) | Dashboard template mặc định |
| [`specs/config-schema.json`](./specs/config-schema.json) | Config JSON schema |
| [`templates/CHANGELOG.md`](./templates/CHANGELOG.md) | Changelog template |
| [`templates/CONTRIBUTING.md`](./templates/CONTRIBUTING.md) | Contributing guide template |

---

## Sơ Đồ Tổng Thể

```text
dataviz <file> [files...] [options]
        |
        v
  ┌─────────────────────────────────────────────────────────┐
  │                  Orchestrator Agent                     │
  │            (pipeline coordination + retry)              │
  └──────────────┬──────────────┬──────────────┬────────────┘
                 │              │              │
                 v              v              v
             Reader Agent     EDA Agent     Viz Agent      Report Agent
                 │              │              │              │
                 v              v              v              v
            reader_tools    eda_tools      viz_tools     report_tools
                                                        │
                                                        v
                                              assemble_dashboard()
                                                        │
                                                        v
                                         HTML / MD / PDF / Notebook
```

---

## Quick Start

```bash
pip install dataviz

dataviz config set --provider claude --key sk-ant-...

dataviz mydata.csv --output html
dataviz sales.csv customers.xlsx --join-on customer_id --output pdf
dataviz bigdata.parquet --deep --output notebook
```
