# DataViz CLI — Thiết Kế Tổng Thể

> Tài liệu thiết kế đầy đủ cho `dataviz` — CLI tool phân tích và trực quan hóa dữ liệu tự động bằng LLM.

---

## Danh Sách Tài Liệu

| File | Nội dung |
|---|---|
| [`01-overview.md`](./docs/01-overview.md) | Tổng quan dự án, stack, phân phối |
| [`02-config.md`](./docs/02-config.md) | Cấu trúc config JSON, resolution order |
| [`03-input-output.md`](./docs/03-input-output.md) | Định dạng input/output, data strategy |
| [`04-agent-architecture.md`](./docs/04-agent-architecture.md) | Kiến trúc multi-agent, luồng xử lý |
| [`05-tools.md`](./docs/05-tools.md) | Tool registry, danh sách tool, dynamic tool generation |
| [`06-providers.md`](./docs/06-providers.md) | LLM providers (OpenAI, Claude, Gemini) |
| [`07-dashboard.md`](./docs/07-dashboard.md) | Dashboard assembly, template system |
| [`08-cli.md`](./docs/08-cli.md) | CLI flags, subcommands, modes |
| [`09-tui.md`](./docs/09-tui.md) | TUI design (Textual), screens, components |
| [`10-storage.md`](./docs/10-storage.md) | Storage layout, cache, sessions |
| [`11-project-structure.md`](./docs/11-project-structure.md) | Cấu trúc thư mục dự án |
| [`12-code-style.md`](./docs/12-code-style.md) | Code style, agent rules, git workflow |
| [`13-testing.md`](./docs/13-testing.md) | Testing strategy, fixtures, coverage |
| [`00-roadmap.md`](./docs/00-roadmap.md) | Roadmap chi tiết theo từng phase |
| [`specs/registry.json`](./specs/registry.json) | Tool registry JSON mẫu đầy đủ |
| [`specs/default-template.json`](./specs/default-template.json) | Dashboard template mặc định |
| [`specs/config-schema.json`](./specs/config-schema.json) | Config JSON schema |
| [`templates/AGENT_RULE.md`](./templates/AGENT_RULE.md) | Agent rule template |
| [`templates/CHANGELOG.md`](./templates/CHANGELOG.md) | Changelog template |
| [`templates/CONTRIBUTING.md`](./templates/CONTRIBUTING.md) | Contributing guide template |

---

## Sơ Đồ Tổng Thể

```
dataviz <file> [files...] [options]
        │
        ▼
  ┌─────────────────────────────────────────────────────┐
  │                  Orchestrator Agent                  │
  │         (pipeline coordination + retry)              │
  └─────┬──────────┬──────────┬──────────────────┬──────┘
        │          │          │                  │
        ▼          ▼          ▼                  ▼
   Reader       EDA         Viz             Report
   Agent        Agent       Agent           Agent
     │            │           │               │
     ▼            ▼           ▼               ▼
  reader_      eda_        viz_           report_
  tools.py     tools.py    tools.py       tools.py
                                              │
                                             ▼
                                    assemble_dashboard()
                                              │
                                             ▼
                              HTML / MD / PDF / Notebook
```

---

## Quick Start (sau khi publish)

```bash
pip install dataviz

dataviz config set --provider claude --key sk-ant-...

dataviz mydata.csv --output html
dataviz sales.csv customers.xlsx --join-on customer_id --output pdf
dataviz bigdata.parquet --deep --output notebook
```