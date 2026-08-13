# 12 — Code Style & Agent Rules

## Ngôn Ngữ

| Thành phần | Ngôn ngữ |
|---|---|
| Variable names, function names, file paths, module names | **English** |
| Comments và docstrings | **English** |
| Nội dung report output | Theo `--lang` flag (`en`, `vi`, `auto`) |

---

## Docstrings

**Google style** cho mọi function và class:

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

**Class docstrings:**

```python
class ToolRegistry:
    """Dynamic tool loader from registry.json.

    Loads all tool functions at startup. Supports runtime
    registration of dynamically generated tools.

    Attributes:
        _tools: Internal dict mapping tool name to callable.
        _registry: List of tool entry dicts from registry.json.
    """
```

---

## Comments

```python
# Correct: plain inline comment
result = compute_stats(df)   # skip nulls by default

# WRONG: section dividers
# === Data Loading ===
# --- helpers ---
# *** IMPORTANT ***

# WRONG: file-level summary block at top of file
# """
# This module handles all data reading operations.
# Author: ...
# """
```

Quy tắc:
- Dùng plain inline comments: `# this does X`
- **Không** dùng section dividers: `# ===`, `# ---`, `# ***`
- **Không** có file-level summary block ở đầu file

---

## Type Hints

Bắt buộc cho tất cả public functions:

```python
# Correct
def plot_histogram(col: str, engine: str = "plotly") -> dict:
    ...

def run_agent_with_retry(
    agent: BaseAgent,
    context: PipelineContext,
    max_retries: int = 3,
) -> AgentResult:
    ...

# Sử dụng | cho Optional (Python 3.10+)
def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
    ...
```

---

## Error Handling

```python
# Luôn raise custom exceptions với message rõ ràng
class ToolNotFoundError(Exception):
    """Raised when a requested tool is not in the registry."""

class AgentMaxRetriesError(Exception):
    """Raised when an agent exhausts all retry attempts."""

class UnknownProviderError(Exception):
    """Raised when a provider name is not supported."""

# Không bao giờ bare except
# WRONG:
try:
    result = tool()
except:
    pass

# Correct:
try:
    result = tool()
except ToolExecutionError as e:
    log.error(f"Tool failed: {e}")
    raise
```

---

## Git Workflow

### Branch naming

| Branch | Mục đích |
|---|---|
| `main` | Chỉ Phase 0 (initial repo setup) |
| `phase-1-core-pipeline` | Phase 1 |
| `phase-2-agents` | Phase 2 |
| `phase-3-tui` | Phase 3 |
| `phase-4-export` | Phase 4 |
| `phase-5-pypi` | Phase 5 |
| `feat/<description>` | Feature nhỏ độc lập |
| `fix/<description>` | Bug fix |

### Merge rules

- **Không bao giờ** merge trực tiếp vào `main` — PRs only (hoặc manual review)
- `main` chỉ nhận Phase 0 initial commit
- Mỗi phase merge vào `main` sau khi tests pass + review

### Commit messages

```
# Good
add chunked reader for large parquet files
fix null detection when all values in column are NaN
implement EDA agent tool loop with retry logic
add Plotly HTML exporter with self-contained output

# Bad
fix bug
wip
update stuff
```

Format: **`<verb> <what>`** — không cần conventional commits prefix, nhưng phải rõ ràng và descriptive.

---

## Agent Rules (AGENT_RULE.md)

Đây là rules cho **coding agent** (Claude Code, v.v.) khi làm việc với repo này:

### Reading files

- Luôn đọc directory top-level trước
- Quyết định có chọn lọc file nào cần mở dựa trên tên
- **Không** đọc toàn bộ file tree một cách mù quáng
- Chỉ đọc files liên quan trực tiếp đến task hiện tại

### Writing code

- Code **chưa xong** cho đến khi tests pass
- Chạy tests sau mọi thay đổi đáng kể
- Fix failures trước khi chuyển sang task tiếp theo
- Generated tools chỉ được lưu vào `dataviz/tools/generated/` — không bao giờ vào core tool files

### Documentation

- Cập nhật `ROADMAP.md` khi bắt đầu và kết thúc mỗi phase
- Ghi vào `docs/dev-log.md` các quyết định, blockers, thay đổi lớn
- Mọi function public đều phải có Google-style docstring

---

## Tracking Documents

### `ROADMAP.md`

Cập nhật status của từng phase task:
- `[ ]` — chưa bắt đầu
- `[x]` — hoàn thành

### `docs/dev-log.md`

Running log — mỗi entry có date và context:

```markdown
## 2024-01-15

### Decision: polars lazy cho large files
Dùng polars thay pandas chunked vì polars lazy scan hiệu quả hơn
cho files > 500MB. pandas chunked vẫn được giữ cho medium files vì
quen thuộc hơn với contributors.

### Blocker: WeasyPrint font issue trên Windows
WeasyPrint cần GTK trên Windows — đang nghiên cứu alternative.
Tạm thời PDF export chỉ test trên Linux/Mac.

### Change: Đổi pending_tools.json path
Chuyển từ `.dataviz/pending_tools.json` sang `~/.config/dataviz/pending_tools.json`
để pending tools không bị commit vào repo.
```

### `CHANGELOG.md`

Một section mỗi phase đã hoàn thành:

```markdown
## Phase 1 — Core Pipeline

### Added
- CLI entry point với Typer (`dataviz --help` works)
- Config system với global/local resolution per field
- File readers: CSV (auto-delimiter), XLSX (multi-sheet), Parquet (lazy)
- Cache system keyed by SHA256 file hash
- Session save/list/open

### Fixed
- Config resolution không merge đúng khi local config thiếu fields

### Changed
- Cache path đổi từ `.dataviz/cache.json` sang `.dataviz/cache/<hash>.json`
```