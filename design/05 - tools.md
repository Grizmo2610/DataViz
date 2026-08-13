# 05 — Tool System

## Nguyên Tắc Cốt Lõi

> Mọi side effect (file I/O, tính toán, vẽ chart) xảy ra **trong tool**.
> Agents chỉ thấy tool inputs và outputs dưới dạng dict/JSON.

---

## Tool Registry

**File:** `dataviz/tools/registry.json`

Agents đọc file này khi khởi động để biết những tool nào có thể gọi.

### Cấu trúc

```json
{
  "tools": [
    {
      "name": "read_sample",
      "module": "dataviz.tools.reader_tools",
      "description": "Read the first N rows of a file for schema inspection.",
      "agent": "reader",
      "args": ["file_path", "n_rows"],
      "generated": false
    },
    {
      "name": "plot_histogram",
      "module": "dataviz.tools.viz_tools",
      "description": "Plot distribution of a numeric column.",
      "agent": "viz",
      "args": ["col", "engine"],
      "generated": false
    }
  ]
}
```

### Fields mỗi tool entry

| Field | Type | Mô tả |
|---|---|---|
| `name` | string | Unique tool identifier — agents dùng tên này để gọi |
| `module` | string | Python module path chứa tool function |
| `description` | string | Mô tả cho human và LLM |
| `agent` | string | Agent sở hữu tool: `reader`, `eda`, `viz`, `report` |
| `args` | string[] | Danh sách argument names |
| `generated` | boolean | `true` nếu là generated tool (không edit thủ công) |

---

## Danh Sách Tool Đầy Đủ

### Reader Tools (`reader_tools.py`)

| Tool | Args | Mô tả |
|---|---|---|
| `read_sample` | `file_path`, `n_rows` | Đọc N rows đầu tiên |
| `detect_schema` | `df` | Infer column types, nulls, unique counts |
| `decide_read_more` | `schema_info` | AI quyết định có cần đọc thêm |
| `read_full_stats` | `file_path` | Chunked full-data stats |

### EDA Tools (`eda_tools.py`)

| Tool | Args | Mô tả |
|---|---|---|
| `compute_descriptive_stats` | `file_path` | mean, std, min, max, percentiles |
| `detect_nulls` | `file_path` | Null counts và % per column |
| `detect_outliers` | `df` | IQR / z-score based |
| `compute_correlation` | `file_path` | Pearson/Spearman correlation matrix |
| `detect_time_series` | `df` | Phát hiện date columns, trends |
| `detect_categorical_distributions` | `df` | Value counts for categorical cols |

### Viz Tools (`viz_tools.py`)

| Tool | Args | Mô tả |
|---|---|---|
| `auto_select_charts` | `schema`, `stats` | AI chọn chart phù hợp |
| `plot_histogram` | `col`, `engine` | Distribution of numeric column |
| `plot_bar` | `x`, `y`, `engine` | Categorical comparisons |
| `plot_line` | `x`, `y`, `engine` | Trend over time |
| `plot_scatter` | `x`, `y`, `hue`, `engine` | Correlation giữa 2 numerics |
| `plot_heatmap` | `corr_matrix`, `engine` | Correlation heatmap |
| `plot_boxplot` | `col`, `group_by`, `engine` | Outlier visualization |
| `plot_pie` | `col`, `engine` | Proportion of categories |
| `plot_missing_heatmap` | `df`, `engine` | Null value heatmap |
| `plot_pairplot` | `cols`, `engine` | Pairwise scatter matrix |
| `plot_violin` | `col`, `group_by`, `engine` | Distribution + density |

### Report Tools (`report_tools.py`)

| Tool | Args | Mô tả |
|---|---|---|
| `write_summary` | `schema`, `stats` | Dataset overview narrative |
| `write_insights` | `stats`, `charts` | Key findings: trends, anomalies |
| `write_recommendations` | `insights` | Optional next steps |
| `assemble_dashboard` | `sections`, `template`, `output_format` | Kết hợp thành output cuối |

---

## Tool Loader

**File:** `dataviz/tools/loader.py`

```python
import importlib
import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent / "registry.json"

class ToolRegistry:
    """Dynamic tool loader from registry.json.

    Loads tool functions at startup. Supports generated tools.
    """

    def __init__(self):
        self._tools: dict[str, callable] = {}
        self._registry: list[dict] = []
        self._load_all()

    def _load_all(self) -> None:
        """Load all tools from registry.json into memory."""
        data = json.loads(REGISTRY_PATH.read_text())
        for entry in data["tools"]:
            module = importlib.import_module(entry["module"])
            fn = getattr(module, entry["name"])
            self._tools[entry["name"]] = fn
            self._registry.append(entry)

    def get(self, name: str) -> callable:
        """Return callable for a tool by name.

        Args:
            name: Tool name as registered in registry.json.

        Returns:
            Callable tool function.

        Raises:
            ToolNotFoundError: If name not in registry.
        """
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found in registry.")
        return self._tools[name]

    def list_for_agent(self, agent: str) -> list[dict]:
        """Return all tool entries for a given agent.

        Args:
            agent: Agent name: reader, eda, viz, or report.

        Returns:
            List of tool entry dicts from registry.json.
        """
        return [t for t in self._registry if t["agent"] == agent]

    def register_generated(self, entry: dict, fn: callable) -> None:
        """Add a dynamically generated tool to the registry at runtime.

        Args:
            entry: Tool entry dict (same format as registry.json).
            fn: The callable function for the tool.
        """
        self._tools[entry["name"]] = fn
        self._registry.append(entry)
```

---

## Dynamic Tool Generation

Khi agent gặp task mà **không có tool nào trong registry** có thể xử lý:

### Bước 1 — Phát hiện tool thiếu

LLM xác định không tool nào trong danh sách phù hợp với task hiện tại.

### Bước 2 — Kiểm tra `tool_gen_mode`

```json
{ "tool_gen_mode": "immediate" }
```

### Bước 3a — Immediate Mode

```
Agent generate Python tool code (LLM)
    │
    ▼
Tool được lưu vào dataviz/tools/generated/<name>.py
    │
    ▼
Tool entry được thêm vào registry.json với "generated": true
    │
    ▼
Tool được load dynamically và execute ngay
    │
    ▼
Kết quả trả về agent như tool thông thường
```

### Bước 3b — Deferred Mode

```
Tool request được append vào ~/.config/dataviz/pending_tools.json
    │
    ▼
Agent ghi chú gap trong context, tiếp tục pipeline không có kết quả này
    │
    ▼
User sau đó chạy: dataviz tool-gen run
```

---

## Generated Tool File Format

**Location:** `dataviz/tools/generated/<tool_id>_<name>.py`

```python
# dataviz/tools/generated/ptool_001_waterfall_chart.py
# AUTO-GENERATED — do not edit manually
# Generated: 2024-01-15T10:30:00
# Request ID: ptool_001

def ptool_001_waterfall_chart(
    categories: list[str],
    values: list[float],
    engine: str = "plotly",
) -> dict:
    """Plot a waterfall chart for cumulative revenue changes.

    Args:
        categories: List of category labels for each bar.
        values: Numeric values (positive = increase, negative = decrease).
        engine: Chart engine to use: "plotly" or "matplotlib".

    Returns:
        Dict with chart_id, output_path, and optional base64.
    """
    import plotly.graph_objects as go

    fig = go.Figure(go.Waterfall(
        name="revenue",
        orientation="v",
        x=categories,
        y=values,
    ))
    ...
    return {
        "chart_id": "waterfall_revenue",
        "chart_type": "waterfall",
        "output_path": "...",
    }
```

---

## `pending_tools.json` Format

```json
{
  "pending": [
    {
      "id": "ptool_001",
      "requested_at": "2024-01-15T10:30:00",
      "agent": "viz",
      "description": "Plot a waterfall chart for cumulative revenue changes",
      "args": ["categories", "values"],
      "status": "pending"
    },
    {
      "id": "ptool_002",
      "requested_at": "2024-01-15T10:45:00",
      "agent": "eda",
      "description": "Detect seasonality using FFT on time series",
      "args": ["date_col", "value_col"],
      "status": "pending"
    }
  ]
}
```

### Status values

| Status | Nghĩa |
|---|---|
| `pending` | Chưa được generate |
| `generated` | Đã generate, chưa verify |
| `active` | Đã active trong registry |
| `discarded` | User discard |

---

## `dataviz tool-gen` Subcommands

```bash
dataviz tool-gen list          # Hiển thị tất cả pending requests
dataviz tool-gen run           # Generate tất cả pending tools
dataviz tool-gen run --name ptool_001   # Generate một tool cụ thể
dataviz tool-gen discard       # Xoá tất cả pending requests
dataviz tool-gen discard --name ptool_002  # Xoá một request cụ thể
```

Output của `tool-gen list`:

```
ID          Agent   Status    Description
──────────────────────────────────────────────────────────────
ptool_001   viz     pending   Plot a waterfall chart for ...
ptool_002   eda     pending   Detect seasonality using FFT ...
```