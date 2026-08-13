# 04 — Agent Architecture

## Tổng Quan

Toàn bộ agent viết từ đầu — **không dùng LangChain, LlamaIndex, hay bất kỳ agent framework nào**.

```
CLI Entry
    │
    ▼
Orchestrator Agent
    ├── Reader Agent       (file I/O, sampling, schema extraction)
    ├── EDA Agent          (statistical analysis, full-data pass)
    ├── Viz Agent          (chart selection, chart generation)
    └── Report Agent       (narrative, insight text, final assembly)
```

---

## Agent Loop (Cơ Chế Chung)

Mọi agent đều chạy theo vòng lặp này:

```
receive context (schema, stats, partial results, ...)
    │
    ▼
[LLM call] decide next tool call
    │        → tool_name + args
    ▼
execute tool → get result (dict/JSON)
    │
    ▼
update shared context with result
    │
    ▼
[LLM call] decide: call another tool OR return final output?
    │
    ├── another tool → lặp lại
    └── done → trả kết quả về Orchestrator
```

### Quy tắc Agent

Agents **chỉ** được phép:
1. Nhận context đầu vào
2. Quyết định gọi tool nào với args gì (LLM decision)
3. Nhận kết quả tool
4. Quyết định bước tiếp theo

Agents **không bao giờ**:
- Viết chart code inline
- Trực tiếp gọi pandas/plotly/matplotlib
- Tự build HTML/Markdown strings
- Đọc file trực tiếp — luôn qua reader tool

---

## Orchestrator Agent

**File:** `dataviz/agents/orchestrator.py`

### Trách nhiệm
- Nhận CLI args và user intent (`--focus`, `--deep`, v.v.)
- Quyết định thứ tự và agent nào cần invoke
- Quản lý shared context giữa các agent
- Xử lý retry độc lập cho từng agent
- Truyền tool call results giữa các agent

### Shared Context Object

```python
@dataclass
class PipelineContext:
    """Shared state passed between all agents.

    Attributes:
        file_paths: Input file path(s).
        output_format: Target output format.
        mode: Analysis mode (fast / default / deep).
        focus: Optional user focus hint.
        lang: Report language.
        schema: Detected column schema from Reader Agent.
        sample_df: Sampled DataFrame for chart generation.
        full_stats: Aggregated stats from full-data pass.
        charts: List of generated chart paths/objects.
        insights: Narrative text sections from Report Agent.
        final_output_path: Path to the assembled final file.
    """
    file_paths: list[str]
    output_format: str
    mode: str = "default"
    focus: str | None = None
    lang: str = "auto"
    schema: dict | None = None
    sample_df: Any | None = None
    full_stats: dict | None = None
    charts: list[dict] = field(default_factory=list)
    insights: dict | None = None
    final_output_path: str | None = None
```

### Retry Logic

```python
def run_agent_with_retry(
    agent: BaseAgent,
    context: PipelineContext,
    max_retries: int = 3,
) -> AgentResult:
    """Run an agent with automatic retry on failure.

    Args:
        agent: Agent instance to run.
        context: Current pipeline context.
        max_retries: Maximum number of retry attempts.

    Returns:
        AgentResult with output and updated context.

    Raises:
        AgentMaxRetriesError: If all retries exhausted.
    """
    for attempt in range(max_retries):
        try:
            return agent.run(context)
        except AgentError as e:
            if attempt == max_retries - 1:
                raise AgentMaxRetriesError(agent.name, max_retries) from e
            log.warning(f"{agent.name} failed (attempt {attempt+1}), retrying...")
```

---

## Reader Agent

**File:** `dataviz/agents/reader.py`

### Tools được gọi (theo thứ tự)

| Tool | Mô tả |
|---|---|
| `read_sample(file, n_rows)` | Đọc N rows đầu tiên |
| `detect_schema(df)` | Infer column types, nulls, unique counts |
| `decide_read_more(schema_info)` | AI quyết định có cần đọc thêm không |
| `read_full_stats(file)` | Chunked full-data statistics |

### Luồng chi tiết

```
read_sample(20 rows)
    │
    ▼
detect_schema()
    │
    ▼
[AI] đủ để hiểu data chưa?
    ├── Đủ → gọi read_full_stats()
    └── Chưa → read_sample(thêm đến tổng 100 rows) → detect_schema() lại
                    │
                    ▼
              read_full_stats()
```

### Output

```python
{
    "schema": {
        "columns": [
            {
                "name": "revenue",
                "dtype": "float64",
                "null_count": 3,
                "null_pct": 0.3,
                "unique_count": 847,
                "sample_values": [1200.0, 3500.0, 890.5]
            },
            ...
        ],
        "row_count_estimate": 10000,
        "file_format": "csv",
        "delimiter": ","
    },
    "full_stats": {
        "revenue": { "min": 0.0, "max": 95000.0, "mean": 4231.5, "std": 2891.2 },
        ...
    }
}
```

---

## EDA Agent

**File:** `dataviz/agents/eda.py`

### Tools được gọi

| Tool | Mô tả |
|---|---|
| `compute_descriptive_stats(file)` | mean, std, min, max, percentiles |
| `detect_nulls(file)` | Null counts và percentage per column |
| `detect_outliers(df)` | IQR / z-score based outlier detection |
| `compute_correlation(file)` | Pearson/Spearman correlation matrix |
| `detect_time_series(df)` | Phát hiện date columns, tính trends |
| `detect_categorical_distributions(df)` | Value counts cho categorical columns |

### Outlier Detection — Cơ Chế

```
Numeric columns:
    IQR method: outlier nếu value < Q1 - 1.5*IQR hoặc > Q3 + 1.5*IQR
    Z-score method: outlier nếu |z| > 3

Kết quả: per column → outlier count, outlier pct, example values
```

### Output

```python
{
    "descriptive_stats": {
        "revenue": {
            "mean": 4231.5, "std": 2891.2,
            "min": 0.0, "25%": 1800.0, "50%": 3900.0, "75%": 6200.0, "max": 95000.0
        }
    },
    "nulls": {
        "revenue": { "count": 3, "pct": 0.03 },
        "category": { "count": 0, "pct": 0.0 }
    },
    "outliers": {
        "revenue": { "count": 12, "pct": 0.12, "method": "IQR" }
    },
    "correlation": {
        "matrix": { "revenue": { "cost": 0.82, "units": 0.67 } },
        "method": "pearson"
    },
    "time_series": {
        "date_column": "order_date",
        "trend": "increasing",
        "seasonality_detected": True
    },
    "categorical": {
        "category": { "Electronics": 342, "Clothing": 218, "Food": 189 }
    }
}
```

---

## Viz Agent

**File:** `dataviz/agents/viz.py`

### Tools được gọi

| Tool | Input | Mô tả |
|---|---|---|
| `auto_select_charts(schema, stats)` | schema, eda output | AI chọn chart phù hợp |
| `plot_histogram(col)` | tên cột | Distribution của numeric column |
| `plot_bar(x, y)` | x col, y col | Categorical comparisons |
| `plot_line(x, y)` | x col, y col | Trend over time |
| `plot_scatter(x, y, hue)` | 2–3 cols | Correlation giữa hai numerics |
| `plot_heatmap(corr_matrix)` | correlation data | Correlation heatmap |
| `plot_boxplot(col, group_by)` | col, optional group | Outlier visualization |
| `plot_pie(col)` | tên cột | Proportion of categories |
| `plot_missing_heatmap(df)` | dataframe | Null value heatmap |
| `plot_pairplot(cols)` | list of cols | Pairwise scatter matrix |
| `plot_violin(col, group_by)` | col, optional group | Distribution + density |

### `auto_select_charts` — Logic AI

AI nhận schema + EDA output và quyết định:

```
Nếu có date column → plot_line (time series)
Nếu có correlation cao (>0.7) → plot_scatter + plot_heatmap
Nếu có numeric cols → plot_histogram (mỗi col)
Nếu có categorical cols (< 10 unique values) → plot_bar + plot_pie
Nếu có outliers → plot_boxplot
Nếu có nhiều nulls (> 5% any col) → plot_missing_heatmap
Nếu mode == deep → thêm plot_pairplot, plot_violin
```

### Chart count theo mode

| Mode | Charts |
|---|---|
| `--fast` | 3–5 |
| default | 6–10 |
| `--deep` | 10–20+ |

### Chart Output Format

Mỗi chart tool trả về:

```python
{
    "chart_id": "histogram_revenue",
    "chart_type": "histogram",
    "title": "Distribution of Revenue",
    "engine": "plotly",   # hoặc "matplotlib"
    "output_path": "/tmp/dataviz/histogram_revenue.html",  # plotly
    # hoặc
    "output_path": "/tmp/dataviz/histogram_revenue.png",   # matplotlib
    "base64": "iVBORw0KGgo..."  # chỉ cho matplotlib/md output
}
```

---

## Report Agent

**File:** `dataviz/agents/report.py`

### Tools được gọi

| Tool | Mô tả |
|---|---|
| `write_summary(schema, stats)` | Dataset overview narrative |
| `write_insights(stats, charts)` | Key findings: trends, anomalies, distributions |
| `write_recommendations(insights)` | Optional next steps |
| `assemble_dashboard(sections, template, output_format)` | Kết hợp tất cả thành output cuối |

### `assemble_dashboard` — Luồng

```
Report Agent gọi assemble_dashboard(sections, template, output_format)
    │
    ▼
Tool đọc template JSON
    │
    ▼
Tool duyệt qua từng section trong template theo thứ tự
    │
    ├── Tìm content tương ứng từ agent results
    ├── Render section dùng output_format engine
    └── Kết hợp tất cả sections
    │
    ▼
Tool ghi output file và trả về file path
```

---

## Abstract Base Classes

### BaseAgent

```python
# agents/base.py

from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Abstract base class for all agents.

    Subclasses must implement the run() method.
    Agents only call tools — never perform side effects directly.
    """

    def __init__(self, provider: BaseProvider, tool_registry: ToolRegistry):
        self.provider = provider
        self.tool_registry = tool_registry
        self.name = self.__class__.__name__

    @abstractmethod
    def run(self, context: PipelineContext) -> AgentResult:
        """Execute the agent's task using tools.

        Args:
            context: Current pipeline context with shared state.

        Returns:
            AgentResult containing output data and updated context fields.
        """
        ...

    def _call_tool(self, tool_name: str, args: dict) -> dict:
        """Look up and execute a tool from the registry.

        Args:
            tool_name: Name of the tool as registered in registry.json.
            args: Arguments to pass to the tool function.

        Returns:
            Tool result as a dict.

        Raises:
            ToolNotFoundError: If tool_name is not in registry.
            ToolExecutionError: If the tool raises an exception.
        """
        tool = self.tool_registry.get(tool_name)
        return tool(**args)
```