# 02 — Config System

## Tổng Quan

Toàn bộ config dùng **plain JSON** (`.json`). Không TOML, không YAML, không JSONC.

---

## Resolution Order

Mỗi field được resolve **độc lập** theo thứ tự ưu tiên:

```
CLI flag
    ↓
.dataviz/config.json          (local — project-level)
    ↓
~/.config/dataviz/config.json (global — user-level)
    ↓
built-in default
```

**Ví dụ:** nếu global config có `"output": "html"` nhưng local config có `"output": "pdf"`, thì field `output` = `"pdf"`. Các field khác không có trong local config vẫn lấy từ global.

---

## Global Config

**Path:** `~/.config/dataviz/config.json`

```json
{
  "default_provider": "claude",
  "tool_gen_mode": "deferred",
  "lang": "auto",
  "output": "html",
  "out_dir": "./dataviz_output",
  "providers": {
    "claude": {
      "api_key": "sk-ant-...",
      "model": "claude-sonnet-4-6"
    },
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4o",
      "base_url": "https://api.openai.com/v1"
    },
    "gemini": {
      "api_key": "AIza...",
      "model": "gemini-1.5-pro"
    }
  }
}
```

### Giải thích các field

| Field | Type | Default | Mô tả |
|---|---|---|---|
| `default_provider` | string | `"claude"` | Provider LLM mặc định |
| `tool_gen_mode` | string | `"deferred"` | Chế độ sinh tool động: `immediate` hoặc `deferred` |
| `lang` | string | `"auto"` | Ngôn ngữ report: `en`, `vi`, `auto` |
| `output` | string | `"html"` | Định dạng output: `html`, `md`, `pdf`, `notebook` |
| `out_dir` | string | `"./dataviz_output"` | Thư mục xuất output |
| `providers` | object | — | Cấu hình từng provider |

### Provider fields

| Field | Bắt buộc | Mô tả |
|---|---|---|
| `api_key` | ✅ | API key của provider |
| `model` | ✅ | Model mặc định của provider |
| `base_url` | ❌ (chỉ openai) | Endpoint tuỳ chỉnh (Azure, Groq, v.v.) |

---

## Local Config

**Path:** `.dataviz/config.json` (nằm trong project folder)

Chỉ cần chứa các field muốn override — không cần đầy đủ:

```json
{
  "default_provider": "openai",
  "lang": "vi",
  "tool_gen_mode": "immediate"
}
```

---

## Các File JSON Liên Quan

| File | Location | Mục đích |
|---|---|---|
| `config.json` | global + local | Provider keys, defaults |
| `registry.json` | `dataviz/tools/` | Danh sách tất cả tools (built-in + generated) |
| `pending_tools.json` | `~/.config/dataviz/` | Queue tool generation requests (deferred mode) |
| `<hash>.json` | `.dataviz/cache/` | Kết quả phân tích cache theo file hash |
| `metadata.json` | sessions folder | Metadata của mỗi session đã lưu |

---

## CLI Subcommands Config

### Set provider và key

```bash
dataviz config set --provider claude --key sk-ant-...
dataviz config set --provider openai --key sk-...
dataviz config set --provider gemini --key AIza...
```

### Update model

```bash
dataviz config update --provider openai --model gpt-4o
dataviz config update --provider claude --model claude-sonnet-4-6
```

### Xem config hiện tại (keys bị mask)

```bash
dataviz config show
```

Output mẫu:
```
Provider:  claude
Model:     claude-sonnet-4-6
API Key:   sk-ant-...****
Lang:      auto
Output:    html
Out Dir:   ./dataviz_output
Tool Gen:  deferred
```

---

## Config Loading Logic (Python)

```python
# config.py — pseudocode

BUILT_IN_DEFAULTS = {
    "default_provider": "claude",
    "tool_gen_mode": "deferred",
    "lang": "auto",
    "output": "html",
    "out_dir": "./dataviz_output",
}

def load_config(cli_overrides: dict) -> dict:
    """Load and merge config from all sources.

    Resolution order (highest to lowest priority):
        CLI flags → local .dataviz/config.json
        → global ~/.config/dataviz/config.json
        → BUILT_IN_DEFAULTS

    Args:
        cli_overrides: Dict of flags passed via CLI (None values excluded).

    Returns:
        Merged config dict with all fields resolved.
    """
    global_cfg = _read_json(GLOBAL_CONFIG_PATH) or {}
    local_cfg  = _read_json(LOCAL_CONFIG_PATH)  or {}

    merged = {**BUILT_IN_DEFAULTS, **global_cfg, **local_cfg}

    # CLI flags override everything (skip None values)
    for key, val in cli_overrides.items():
        if val is not None:
            merged[key] = val

    return merged
```

---

## `tool_gen_mode` — Chi Tiết

| Giá trị | Hành vi |
|---|---|
| `"immediate"` | Agent gặp task không có tool → sinh tool code ngay → load → execute → tiếp tục |
| `"deferred"` | Agent gặp task không có tool → ghi vào `pending_tools.json` → bỏ qua bước đó → tiếp tục |

Xem chi tiết tại [`05-tools.md`](./05-tools.md#dynamic-tool-generation).

---

## `lang` — Ngôn Ngữ Report

| Giá trị | Hành vi |
|---|---|
| `"auto"` | Detect ngôn ngữ từ locale hệ thống. Nếu không detect được → fallback `"en"` |
| `"en"` | Report viết bằng tiếng Anh |
| `"vi"` | Report viết bằng tiếng Việt |

Field này chỉ ảnh hưởng đến **nội dung report** (summary, insights, recommendations). Tên chart, label, v.v. vẫn giữ nguyên từ dữ liệu gốc.