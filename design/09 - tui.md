# 09 — TUI Design (Textual)

## Tổng Quan

TUI được build bằng **Textual** — tự động launch sau khi analysis hoàn tất (trừ khi `--no-tui` hoặc output bị pipe).

---

## Screens

### 1. Dashboard Screen

**File:** `dataviz/tui/screens/dashboard.py`

Screen đầu tiên sau khi analysis xong. Hiển thị:

```
┌─────────────────────────────────────────────────────────────────┐
│  DataViz — sales.csv                              [q]uit [?]help│
├───────────┬─────────────────────────────────────────────────────┤
│           │  📊 Dataset Overview                                 │
│  [Tree]   │  ─────────────────────────────────────────────────  │
│           │  Rows:     10,000                                    │
│  EDA      │  Columns:  8                                         │
│  Charts   │  Format:   CSV  (delimiter: ,)                       │
│  Insights │  Nulls:    3 columns have missing values             │
│  Export   │                                                      │
│           │  📋 Schema                                           │
│           │  ─────────────────────────────────────────────────  │
│           │  revenue    float64    3 nulls   847 unique          │
│           │  category   object     0 nulls   5 unique            │
│           │  order_date datetime   0 nulls   365 unique          │
│           │  ...                                                  │
│           │                                                      │
│           │  [Agent Log]  Reader ✅  EDA ✅  Viz ✅  Report ✅   │
└───────────┴─────────────────────────────────────────────────────┘
 ↑↓ navigate   Enter select   e export   i interactive   q quit
```

**Components:**
- `Tree` — navigate sections (EDA / Charts / Insights / Export)
- `DataTable` — schema table, stats table
- `Log` panel — agent activity feed (real-time trong lúc analysis)

---

### 2. Chart Selector Screen

**File:** `dataviz/tui/screens/chart_selector.py`

```
┌─────────────────────────────────────────────────────────────────┐
│  Charts (7 total)                                 [←] back      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ▶  1. Revenue Distribution (histogram)                         │
│     2. Revenue by Category (bar)                                 │
│     3. Revenue Over Time (line)                                  │
│     4. Revenue vs Cost (scatter)                                 │
│     5. Correlation Heatmap                                       │
│     6. Outlier Analysis — Revenue (boxplot)                      │
│     7. Missing Values Heatmap                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
 ↑↓ navigate   Enter preview   Space select all   e export selected
```

**Controls:**
- Arrow keys: navigate
- Enter: mở Chart Preview Screen
- Space: toggle selection (cho export batch)
- `e`: export selected charts

---

### 3. Chart Preview Screen

**File:** `dataviz/tui/screens/chart_preview.py`

```
┌─────────────────────────────────────────────────────────────────┐
│  Revenue Distribution                             [←] back      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Plotly chart renders in browser]                               │
│  or                                                              │
│  [ASCII/Sixel art nếu terminal hỗ trợ]                          │
│                                                                  │
│  ℹ️  Opening chart in browser...                                  │
│                                                                  │
│  Type: histogram                                                 │
│  Column: revenue (float64)                                       │
│  Range: 0.0 – 95,000.0                                          │
│  Mean: 4,231.5   Std: 2,891.2                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
 o open-in-browser   ← back   → next chart
```

**Render strategy:**
1. Check nếu terminal hỗ trợ Sixel → render inline
2. Nếu không → mở browser với file HTML chart
3. Cho matplotlib charts → ASCII approximation inline

---

### 4. Insight Screen

**File:** `dataviz/tui/screens/insight.py`

```
┌─────────────────────────────────────────────────────────────────┐
│  Key Insights                                     [←] back      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📈 Trends                                                       │
│  Revenue shows a strong upward trend in Q3 2023, increasing     │
│  by 34% compared to Q2. The growth is primarily driven by the   │
│  Electronics category.                                           │
│                                                                  │
│  ⚠️  Anomalies                                                    │
│  12 outliers detected in the revenue column using IQR method.   │
│  Values range from 87,000 to 95,000 — significantly above the   │
│  75th percentile (6,200).                                        │
│                                                                  │
│  📊 Distributions                                                │
│  The 'category' column has 5 unique values with Electronics      │
│  dominating at 34% of total orders.                              │
│                                                                  │
│  💡 Recommendations                                              │
│  1. Investigate outlier orders for potential data entry errors.  │
│  2. Examine Q3 drivers more closely — segment by sales rep.     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
 ↑↓ scroll   ← back   e export as text
```

---

### 5. Export Screen

**File:** `dataviz/tui/screens/export.py`

```
┌─────────────────────────────────────────────────────────────────┐
│  Export Report                                    [←] back      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Format:     ◉ HTML   ○ PDF   ○ Markdown   ○ Notebook          │
│                                                                  │
│  Output dir: [ ./dataviz_output                              ]   │
│                                                                  │
│  Session:    [ (optional name to save session)               ]   │
│                                                                  │
│  ┌──────────────┐                                                │
│  │  Export Now  │                                                │
│  └──────────────┘                                                │
│                                                                  │
│  Last export: ./dataviz_output/report.html (2 min ago)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### Progress Bar + Spinner

**File:** `dataviz/tui/components/progress.py`

Hiển thị trong lúc analysis đang chạy (trước khi TUI screens hiển thị):

```
Analyzing sales.csv...

  Reader Agent    ████████████████████ 100%  ✅
  EDA Agent       ████████████░░░░░░░░  60%  ⏳
  Viz Agent       ░░░░░░░░░░░░░░░░░░░░   0%  ⏸
  Report Agent    ░░░░░░░░░░░░░░░░░░░░   0%  ⏸

  Computing correlation matrix...
```

### Log Panel

**File:** `dataviz/tui/components/log_panel.py`

Real-time feed của agent activity:

```
[10:23:01] Reader   → read_sample(n_rows=20)
[10:23:01] Reader   ← 20 rows, 8 columns detected
[10:23:02] Reader   → detect_schema()
[10:23:02] Reader   ← schema: 3 numeric, 2 categorical, 1 datetime, 2 text
[10:23:02] Reader   → read_full_stats()
[10:23:05] Reader   ✅ Done
[10:23:05] EDA      → compute_descriptive_stats()
...
```

### Footer

Luôn hiển thị ở dưới cùng với keyboard shortcuts phù hợp với screen hiện tại:

```
↑↓ navigate  Enter select  e export  i interactive  q quit  ? help
```

---

## Keyboard Shortcuts (Toàn Cục)

| Key | Action |
|---|---|
| `q` | Quit TUI |
| `?` | Show help |
| `←` / `Escape` | Back |
| `↑` / `↓` | Navigate list |
| `Enter` | Select / Open |
| `e` | Export |
| `i` | Interactive Q&A mode |
| `o` | Open in browser (chart preview) |
| `Space` | Toggle selection |

---

## TUI Launch Logic

```python
# cli.py — sau khi pipeline hoàn tất

import sys

def should_launch_tui(no_tui: bool) -> bool:
    """Determine whether to launch the TUI.

    Args:
        no_tui: --no-tui flag value.

    Returns:
        True if TUI should launch.
    """
    if no_tui:
        return False
    if not sys.stdout.isatty():   # Output bị pipe
        return False
    return True
```

---

## TUI Testing

Textual cung cấp test client cho automated testing:

```python
# tests/unit/test_tui_dashboard.py

from textual.testing import AppTest
from dataviz.tui.app import DatavizApp

async def test_dashboard_renders():
    """Verify dashboard screen renders key sections."""
    app = DatavizApp(mock_context=MOCK_CONTEXT)
    async with AppTest(app) as pilot:
        assert pilot.app.query_one("#summary-section")
        assert pilot.app.query_one("#schema-table")
```