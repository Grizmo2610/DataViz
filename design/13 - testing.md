# 13 — Testing Strategy

## Framework

| Tool | Mục đích |
|---|---|
| `pytest` | Test runner chính |
| `pytest-mock` | Mock LLM calls và external APIs |
| `pytest-cov` | Coverage reporting |
| `pytest-asyncio` | Async tests (Textual TUI) |

---

## Test Categories

| Category | Location | Mô tả |
|---|---|---|
| Unit tests | `tests/unit/` | Individual functions, tools, agents |
| Integration tests | `tests/integration/` | Full pipeline với mocked LLM |
| Sample tests | `tests/samples/` | User-runnable, real fixture files |

---

## Test Fixtures (Sample Data)

```
tests/fixtures/
├── small_sales.csv          # < 100 rows, simple types (numeric, categorical, date)
├── medium_timeseries.csv    # 50k rows, date column, seasonal pattern
├── wide_data.xlsx           # 80+ columns, multi-sheet
├── nulls_heavy.csv          # > 20% nulls in several columns
├── multi_file_a.csv         # Join testing — orders (customer_id FK)
└── multi_file_b.csv         # Join testing — customers (customer_id PK)
```

### `small_sales.csv` schema

```
order_id    int64     0 nulls
customer_id int64     0 nulls
category    object    0 nulls     (5 unique: Electronics, Clothing, ...)
revenue     float64   3 nulls
cost        float64   0 nulls
units       int64     0 nulls
order_date  datetime  0 nulls
region      object    2 nulls     (4 unique: North, South, East, West)
```

---

## Unit Tests

### `test_config.py`

```python
def test_global_config_loaded():
    """Global config values are returned when no local config exists."""

def test_local_overrides_global():
    """Local config field takes precedence over global for same field."""

def test_cli_overrides_local():
    """CLI flag takes highest precedence."""

def test_missing_local_falls_back_to_global():
    """Fields absent in local config fall back to global, not default."""

def test_built_in_defaults_used_when_no_configs():
    """Built-in defaults returned when no config files exist."""

def test_api_key_masked_in_show():
    """config show returns masked API key."""

def test_write_config_creates_file(tmp_path):
    """config set creates global config file if it doesn't exist."""
```

### `test_readers.py`

```python
def test_csv_auto_detect_comma_delimiter():
def test_csv_auto_detect_semicolon_delimiter():
def test_csv_auto_detect_tab_delimiter():
def test_xlsx_reads_first_sheet_by_default():
def test_xlsx_reads_named_sheet():
def test_xlsx_raises_on_missing_sheet():
def test_parquet_lazy_read_returns_polars_lazyframe():
def test_reader_scale_strategy_small():    # < 50MB → "full"
def test_reader_scale_strategy_medium():   # 50–500MB → "chunked"
def test_reader_scale_strategy_large():    # > 500MB → "lazy"
def test_reader_raises_on_unsupported_format():
def test_reader_raises_on_missing_file():
```

### `test_eda_tools.py`

```python
def test_descriptive_stats_numeric_column(small_sales_df):
def test_descriptive_stats_excludes_non_numeric(small_sales_df):
def test_null_detection_counts_correctly(nulls_heavy_df):
def test_null_detection_zero_nulls(small_sales_df):
def test_outlier_detection_iqr(small_sales_df):
def test_outlier_detection_zscore(small_sales_df):
def test_correlation_returns_matrix(small_sales_df):
def test_time_series_detects_date_column(timeseries_df):
def test_time_series_no_date_column_returns_none(small_sales_df):
def test_categorical_distribution_counts(small_sales_df):
```

### `test_registry.py`

```python
def test_registry_loads_all_builtin_tools():
def test_registry_get_existing_tool():
def test_registry_get_missing_tool_raises():
def test_registry_list_for_reader_agent():
def test_registry_list_for_viz_agent():
def test_registry_register_generated_tool():
def test_registry_generated_tool_callable():
```

### `test_tool_gen.py`

```python
def test_immediate_mode_generates_and_executes(mock_llm):
def test_deferred_mode_appends_to_pending(tmp_path):
def test_pending_tools_json_format(tmp_path):
def test_tool_gen_run_generates_file(tmp_path, mock_llm):
def test_tool_gen_discard_clears_pending(tmp_path):
def test_generated_tool_registered_in_registry(tmp_path, mock_llm):
```

### `test_cache.py`

```python
def test_compute_file_hash_stable():          # Same file → same hash
def test_compute_file_hash_changes_on_edit(): # Modified file → different hash
def test_cache_write_and_read(tmp_path):
def test_cache_miss_returns_none(tmp_path):
def test_cache_invalidated_on_hash_change(tmp_path):
def test_no_cache_flag_skips_read(tmp_path):
```

---

## Integration Tests

### `test_pipeline_mock.py`

```python
# Full pipeline với mocked LLM — không gọi real API

@pytest.fixture
def mock_provider(mocker):
    """Mock LLM provider that returns pre-defined tool calls."""
    provider = mocker.MagicMock(spec=BaseProvider)
    provider.chat.return_value = {
        "content": "",
        "tool_calls": [
            {"name": "read_sample", "arguments": {"file_path": "...", "n_rows": 20}},
        ],
        "finish_reason": "tool_calls",
    }
    return provider

def test_full_pipeline_csv_to_html(tmp_path, mock_provider):
    """Full pipeline produces valid HTML output from CSV."""
    context = PipelineContext(
        file_paths=["tests/fixtures/small_sales.csv"],
        output_format="html",
        out_dir=str(tmp_path),
    )
    orchestrator = Orchestrator(provider=mock_provider)
    result = orchestrator.run(context)
    assert result.final_output_path.endswith(".html")
    assert Path(result.final_output_path).exists()

def test_pipeline_reader_agent_calls_correct_tools(mock_provider):
    """Reader agent calls read_sample before detect_schema."""

def test_pipeline_viz_agent_respects_fast_mode(mock_provider, tmp_path):
    """Fast mode produces at most 5 charts."""

def test_pipeline_retry_on_agent_failure(mocker, tmp_path):
    """Orchestrator retries failed agent up to max_retries times."""
```

### `test_multi_file.py`

```python
def test_two_files_inner_join(tmp_path):
def test_two_files_left_join(tmp_path):
def test_explicit_join_key(tmp_path):
def test_auto_join_key_inference(tmp_path, mock_provider):
def test_missing_join_key_raises_clear_error(tmp_path):
```

---

## Sample Tests (User-runnable)

```python
# tests/samples/test_basic_run.py

from typer.testing import CliRunner
from dataviz.cli import app

runner = CliRunner()

def test_basic_csv_to_html(tmp_path):
    """Run full pipeline on small CSV and verify HTML output is created."""
    result = runner.invoke(app, [
        "tests/fixtures/small_sales.csv",
        "--output", "html",
        "--out-dir", str(tmp_path),
        "--fast",
        "--no-tui",
    ])
    assert result.exit_code == 0
    assert (tmp_path / "report.html").exists()

def test_basic_csv_to_pdf(tmp_path):
    """Full pipeline produces valid PDF output."""
    result = runner.invoke(app, [
        "tests/fixtures/small_sales.csv",
        "--output", "pdf",
        "--out-dir", str(tmp_path),
        "--fast",
        "--no-tui",
    ])
    assert result.exit_code == 0
    assert (tmp_path / "report.pdf").exists()

def test_config_show_runs():
    """config show command runs without error."""
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0

def test_help_runs():
    """--help flag runs without error."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "dataviz" in result.output
```

---

## Running Tests

### Windows

```bat
:: Run all tests
python -m pytest tests/ -v --cov=dataviz --cov-report=term-missing

:: Run only unit tests
python -m pytest tests/unit/ -v

:: Run sample tests
python -m pytest tests/samples/ -v

:: Run with specific test
python -m pytest tests/unit/test_config.py::test_local_overrides_global -v

:: Coverage HTML report
python -m pytest tests/ --cov=dataviz --cov-report=html
```

### Linux / macOS

```bash
python -m pytest tests/ -v --cov=dataviz --cov-report=term-missing
```

---

## Coverage Target

| Module | Target |
|---|---|
| `config.py` | ≥ 90% |
| `readers/` | ≥ 90% |
| `tools/reader_tools.py` | ≥ 85% |
| `tools/eda_tools.py` | ≥ 85% |
| `tools/viz_tools.py` | ≥ 80% |
| `agents/` | ≥ 80% |
| `exporters/` | ≥ 75% |
| `tools/generated/` | Excluded |
| **Overall** | **≥ 80%** |

---

## `conftest.py`

```python
# tests/conftest.py

import pytest
import pandas as pd

@pytest.fixture
def small_sales_df():
    """Load small_sales.csv as DataFrame."""
    return pd.read_csv("tests/fixtures/small_sales.csv")

@pytest.fixture
def nulls_heavy_df():
    """Load nulls_heavy.csv as DataFrame."""
    return pd.read_csv("tests/fixtures/nulls_heavy.csv")

@pytest.fixture
def timeseries_df():
    """Load medium_timeseries.csv as DataFrame (first 1000 rows for speed)."""
    return pd.read_csv("tests/fixtures/medium_timeseries.csv", nrows=1000)

@pytest.fixture
def mock_registry(tmp_path, monkeypatch):
    """Provide a temporary registry.json for tool tests."""
    registry_data = {"tools": [...]}
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(json.dumps(registry_data))
    monkeypatch.setattr("dataviz.tools.loader.REGISTRY_PATH", registry_path)
    return registry_path
```