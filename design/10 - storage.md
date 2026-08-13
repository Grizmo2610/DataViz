# 10 — Storage Layout

## Global Storage (User-level)

```
~/.config/dataviz/
├── config.json                    # API keys, provider defaults
├── pending_tools.json             # Queued tool generation requests (deferred mode)
├── sessions/
│   └── <session_name>/
│       ├── report.html            # (hoặc .md, .pdf, .ipynb)
│       ├── metadata.json
│       └── charts/
│           ├── histogram_revenue.png
│           └── ...
└── templates/
    └── dashboard/
        └── <custom_template>.json
```

---

## Local Storage (Project-level)

```
.dataviz/
├── config.json                    # Local overrides (provider, model, lang, ...)
├── cache/
│   └── <file_hash>.json          # Cached analysis keyed by SHA256 hash của file
└── templates/
    └── dashboard/
        └── <custom_template>.json
```

---

## Cache System

**File:** `dataviz/cache.py`

### Cache key

Cache được keyed bằng **SHA256 hash của file content** — đảm bảo cache invalid khi file thay đổi:

```python
import hashlib

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file for use as cache key.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hex digest string (64 chars).
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
```

### Cache file format

**Path:** `.dataviz/cache/<hash>.json`

```json
{
  "file_path": "sales.csv",
  "file_hash": "a3f4b2c1...",
  "created_at": "2024-01-15T10:30:00",
  "dataviz_version": "0.1.0",
  "schema": { ... },
  "full_stats": { ... },
  "eda": { ... }
}
```

### Cache behavior

| Scenario | Hành vi |
|---|---|
| File không đổi, cache tồn tại | Skip Reader + EDA, dùng cached data |
| File thay đổi (hash khác) | Xoá cache cũ, chạy lại từ đầu |
| `--no-cache` flag | Bỏ qua cache hoàn toàn, không ghi cache mới |
| Cache corrupt | Xoá và chạy lại, log warning |

**Lưu ý:** Viz Agent và Report Agent **không cache** — chart generation và narrative phụ thuộc vào flags (`--focus`, `--lang`) và có thể thay đổi.

---

## Session System

**File:** `dataviz/session.py`

### Session metadata format

**Path:** `~/.config/dataviz/sessions/<name>/metadata.json`

```json
{
  "session_name": "q3-analysis",
  "created_at": "2024-01-15T10:30:00",
  "dataviz_version": "0.1.0",
  "source_files": ["sales.csv"],
  "output_format": "html",
  "flags": {
    "mode": "deep",
    "lang": "vi",
    "focus": "revenue trends by region"
  },
  "provider": "claude",
  "model": "claude-sonnet-4-6",
  "report_path": "~/.config/dataviz/sessions/q3-analysis/report.html",
  "chart_count": 8
}
```

### Session commands

```bash
# Lưu session (kết hợp với main command)
dataviz data.csv --session q3-analysis

# Liệt kê sessions
dataviz session list
```

Output của `session list`:

```
Name            Date              Format   Charts   Files
───────────────────────────────────────────────────────────
q3-analysis     2024-01-15 10:30  html     8        sales.csv
jan-report      2024-01-10 15:20  pdf      5        data.xlsx
quick-check     2024-01-08 09:00  html     3        test.csv
```

```bash
# Mở lại session (mở file trong browser / viewer)
dataviz session open q3-analysis
```

---

## `.gitignore` Recommendations

File `.gitignore` nên bao gồm:

```gitignore
# DataViz local cache và output
.dataviz/cache/
.dataviz/output/

# Generated tools (không commit vào repo)
dataviz/tools/generated/*.py
!dataviz/tools/generated/.gitkeep

# Build artifacts
dist/
build/
*.egg-info/

# Python
__pycache__/
*.pyc
.venv/
venv/

# Environment
.env
```

**Lưu ý:** `.dataviz/config.json` **không nên** gitignore — thường chứa provider choice và lang setting, không chứa API key (key ở global config).

---

## Storage Size Management

### Cache size

Cache files nhỏ (chỉ chứa schema + stats dưới dạng JSON). File lớn nhất ước tính ~1MB cho dataset có 100+ columns.

Không có auto-cleanup — user dùng:

```bash
dataviz cache clear         # Xoá toàn bộ .dataviz/cache/
```

### Session size

Sessions lưu cả report file (HTML có thể lớn nếu có nhiều Plotly charts):

- HTML: 1–10 MB (tùy số charts)
- PDF: 0.5–5 MB
- Notebook: 0.5–3 MB

Không có auto-cleanup cho sessions.

### Generated tools

`dataviz/tools/generated/` chứa Python files nhỏ (~50–200 lines mỗi file). Có thể discard qua:

```bash
dataviz tool-gen discard    # Xoá pending_tools.json (không xoá files đã generate)
```

Để xoá generated tool files: xoá thủ công từ `dataviz/tools/generated/` và xoá entry khỏi `registry.json`.