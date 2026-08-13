# 01 — Tổng Quan Dự Án

## Mục Tiêu

`dataviz` là CLI tool mã nguồn mở tự động:
1. Đọc file dữ liệu dạng bảng (CSV, XLSX, Parquet)
2. Dùng multi-agent LLM pipeline để thực hiện EDA
3. Tạo chart phù hợp với dữ liệu
4. Xuất dashboard dưới nhiều định dạng

Thiết kế cho **phân phối rộng rãi qua PyPI** — người dùng chỉ cần `pip install dataviz`.

---

## Stack Kỹ Thuật

| Thành phần | Lựa chọn | Lý do |
|---|---|---|
| Ngôn ngữ | Python 3.11+ | Hệ sinh thái data phong phú |
| CLI framework | Typer | Type hints, auto-help, subcommands |
| TUI framework | Textual | Component-based, cross-platform |
| Data processing | pandas + polars | pandas cho small/medium, polars lazy cho large |
| Distribution | PyPI (`pip install dataviz`) | Phổ biến, dễ cài |
| Primary dev OS | Windows | Mọi doc phải có Windows variant |
| Secondary OS | Linux / macOS | Phải hoạt động trên cả hai |

---

## Nguyên Tắc Thiết Kế

### 1. Agent-first, tool-only side effects
Agents chỉ ra quyết định (gọi tool nào, với args gì). **Mọi side effect** (đọc file, tính toán, vẽ chart, ghi output) đều xảy ra **trong tool**, không bao giờ trong agent.

### 2. No framework lock-in
Không dùng LangChain, LlamaIndex, hay bất kỳ agent framework nào. Toàn bộ agent loop được viết từ đầu — dễ debug, dễ mở rộng, không phụ thuộc breaking changes của bên thứ ba.

### 3. Provider-agnostic
Hỗ trợ OpenAI, Claude, Gemini, và mọi endpoint tương thích OpenAI. Người dùng chọn provider một lần, dùng mãi.

### 4. Config resolution rõ ràng
```
CLI flag → .dataviz/config.json → ~/.config/dataviz/config.json → built-in default
```
Mỗi field được resolve độc lập — không override toàn bộ file.

### 5. Dynamic extensibility
Khi agent gặp task không có tool sẵn, nó có thể tự generate tool mới (immediate mode) hoặc queue lại để review sau (deferred mode).

---

## LLM Providers Được Hỗ Trợ

| Provider | Models mẫu | Ghi chú |
|---|---|---|
| **OpenAI** | `gpt-4o`, `gpt-4-turbo` | Cũng dùng cho OpenAI-compatible |
| **OpenAI-compatible** | Tuỳ endpoint | Azure OpenAI, Together, Groq, v.v. |
| **Claude** | `claude-sonnet-4-6` | Anthropic |
| **Gemini** | `gemini-1.5-pro` | Google |

---

## Vòng Đời Một Lệnh

```
dataviz data.csv --output html --deep
```

```
1. CLI parse args (Typer)
2. Config resolution (CLI > local > global > default)
3. Orchestrator khởi tạo với context:
   { file: "data.csv", output: "html", mode: "deep", provider: "claude", ... }
4. Reader Agent:
   - read_sample(20 rows)
   - detect_schema()
   - [nếu cần] read_sample(100 rows)
   - read_full_stats()
5. EDA Agent:
   - compute_descriptive_stats()
   - detect_nulls()
   - detect_outliers()
   - compute_correlation()
   - detect_time_series()
   - detect_categorical_distributions()
6. Viz Agent:
   - auto_select_charts(schema, stats)  ← AI chọn
   - [gọi các plot_* tools tương ứng]
7. Report Agent:
   - write_summary()
   - write_insights()
   - write_recommendations()
   - assemble_dashboard()
8. TUI hiển thị kết quả (Textual)
9. Ghi output file → ./dataviz_output/report.html
```

---

## Dependencies Chính

```toml
[project]
requires-python = ">=3.11"

dependencies = [
    "typer>=0.12",
    "textual>=0.60",
    "pandas>=2.0",
    "polars>=0.20",
    "plotly>=5.0",
    "matplotlib>=3.8",
    "seaborn>=0.13",
    "openpyxl>=3.1",        # XLSX reader
    "pyarrow>=14.0",         # Parquet reader
    "weasyprint>=60.0",      # PDF export
    "nbformat>=5.9",         # Jupyter notebook export
    "anthropic>=0.25",       # Claude provider
    "openai>=1.30",          # OpenAI provider
    "google-generativeai>=0.5",  # Gemini provider
    "rich>=13.0",            # Console output
]
```