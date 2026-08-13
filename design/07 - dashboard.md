# 07 — Dashboard Assembly & Template System

## Nguyên Tắc

Agents **không bao giờ** tự assembly dashboard. Toàn bộ assembly được xử lý bởi tool `assemble_dashboard()`.

---

## Dashboard Templates

Templates định nghĩa **layout và thứ tự sections** của report cuối.

### Template Resolution Order

```
.dataviz/templates/dashboard/<name>.json   (local — ưu tiên cao nhất)
    ↓
~/.config/dataviz/templates/dashboard/<name>.json  (global)
    ↓
dataviz/templates/dashboard/default.json   (built-in default)
```

### Cú pháp

```bash
dataviz data.csv --template my_report    # Dùng template tên "my_report"
dataviz data.csv                          # Dùng built-in default
```

---

## Default Template

**File:** `dataviz/templates/dashboard/default.json`

```json
{
  "name": "default",
  "sections": [
    { "id": "summary",         "title": "Dataset Overview",    "type": "text" },
    { "id": "schema",          "title": "Schema & Types",      "type": "table" },
    { "id": "stats",           "title": "Descriptive Stats",   "type": "table" },
    { "id": "nulls",           "title": "Missing Values",      "type": "chart" },
    { "id": "charts",          "title": "Charts",              "type": "chart_grid" },
    { "id": "insights",        "title": "Key Insights",        "type": "text" },
    { "id": "recommendations", "title": "Recommendations",     "type": "text" }
  ],
  "layout": "single_column",
  "theme": "light"
}
```

### Section types

| Type | Render |
|---|---|
| `text` | Markdown prose → HTML paragraph / PDF paragraph |
| `table` | Dict → HTML table / PDF table |
| `chart` | Chart file → HTML embed / PDF image |
| `chart_grid` | List of charts → responsive grid layout |

### Layout options

| Layout | Mô tả |
|---|---|
| `single_column` | Mặc định — tất cả sections xếp dọc |
| `two_column` | Charts chia 2 cột (chỉ HTML) |

### Theme options

| Theme | Mô tả |
|---|---|
| `light` | Nền trắng, màu sáng |
| `dark` | Nền tối, màu tối |

---

## Custom Template Example

**File:** `.dataviz/templates/dashboard/executive.json`

```json
{
  "name": "executive",
  "sections": [
    { "id": "summary",     "title": "Executive Summary",   "type": "text" },
    { "id": "charts",      "title": "Key Visualizations",  "type": "chart_grid" },
    { "id": "insights",    "title": "Findings",            "type": "text" }
  ],
  "layout": "two_column",
  "theme": "light"
}
```

Template này bỏ qua schema detail và stats — phù hợp cho audience không kỹ thuật.

---

## `assemble_dashboard` Tool — Chi Tiết

**File:** `dataviz/tools/report_tools.py`

```python
def assemble_dashboard(
    sections: dict,
    template_name: str,
    output_format: str,
    out_dir: str,
    lang: str = "en",
) -> dict:
    """Assemble all agent outputs into a final dashboard file.

    Does NOT generate any content — only assembles pre-generated sections.

    Args:
        sections: Dict mapping section_id to content (text, table dict, chart paths).
            Example: {
                "summary": "This dataset contains 10,000 rows...",
                "schema": {"columns": [...]},
                "charts": ["/tmp/histogram_revenue.html", ...],
            }
        template_name: Name of the dashboard template to use.
        output_format: Target format: "html", "md", "pdf", "notebook".
        out_dir: Directory to write the output file.
        lang: Report language for section headings.

    Returns:
        Dict with:
            - output_path (str): Absolute path to the final output file.
            - sections_rendered (int): Number of sections successfully rendered.
    """
    template = _load_template(template_name)
    exporter = _get_exporter(output_format)

    rendered_sections = []
    for section_def in template["sections"]:
        sid = section_def["id"]
        if sid not in sections:
            continue   # Section không có data → bỏ qua
        content = sections[sid]
        rendered = exporter.render_section(section_def, content)
        rendered_sections.append(rendered)

    output_path = exporter.write(
        rendered_sections,
        out_dir=out_dir,
        theme=template.get("theme", "light"),
        layout=template.get("layout", "single_column"),
    )

    return {
        "output_path": str(output_path),
        "sections_rendered": len(rendered_sections),
    }
```

---

## Exporters

### HTML Exporter

**File:** `dataviz/exporters/html_exporter.py`

- Self-contained HTML (tất cả CSS, JS, và charts nhúng trong 1 file)
- Plotly charts render inline qua `plotly.to_html(full_html=False, include_plotlyjs='cdn')`
- Responsive CSS cho mobile

Output mẫu structure:

```html
<!DOCTYPE html>
<html>
<head>
  <title>DataViz Report — data.csv</title>
  <style>/* inline CSS */</style>
  <script src="https://cdn.plot.ly/plotly-2.x.x.min.js"></script>
</head>
<body>
  <section id="summary"> ... </section>
  <section id="schema"> <table>...</table> </section>
  <section id="charts"> <div class="chart-grid">...</div> </section>
  ...
</body>
</html>
```

### Markdown Exporter

**File:** `dataviz/exporters/md_exporter.py`

- Charts được convert sang PNG (matplotlib) rồi base64 encode
- Embed inline: `![chart](data:image/png;base64,...)`
- Tables dùng Markdown pipe syntax

### PDF Exporter

**File:** `dataviz/exporters/pdf_exporter.py`

- Generate HTML trước
- WeasyPrint convert HTML → PDF
- Font support: cần đảm bảo Vietnamese fonts khi `lang=vi`

### Notebook Exporter

**File:** `dataviz/exporters/notebook_exporter.py`

- `nbformat` tạo `.ipynb`
- Mỗi section = 1 Markdown cell + (nếu có) 1 Code cell với Plotly figure
- Include data loading code cell đầu tiên

---

## Luồng Assembly Đầy Đủ

```
Report Agent nhận:
  { schema, full_stats, charts, narrative }
       │
       ▼
write_summary(schema, full_stats)
       │ → "This dataset has 10,000 rows across 8 columns..."
       ▼
write_insights(full_stats, charts)
       │ → "Revenue shows strong upward trend in Q3..."
       ▼
write_recommendations(insights)
       │ → "Consider investigating outliers in the 'returns' column..."
       ▼
assemble_dashboard(
  sections={
    "summary": "...",
    "schema": schema_dict,
    "stats": stats_dict,
    "nulls": nulls_chart_path,
    "charts": [chart1_path, chart2_path, ...],
    "insights": "...",
    "recommendations": "...",
  },
  template_name="default",
  output_format="html",
  out_dir="./dataviz_output",
)
       │
       ▼
→ "./dataviz_output/report.html"  ← trả về Orchestrator
```