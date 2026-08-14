# DataViz

CLI tự động phân tích dữ liệu dạng bảng (CSV, Excel, Parquet), chọn chart phù hợp, và xuất báo cáo ra HTML / PDF / Markdown / Jupyter Notebook.

---

## Yêu cầu hệ thống

| Yêu cầu | Phiên bản tối thiểu |
|---------|---------------------|
| Python  | 3.11 trở lên        |
| pip     | 23.0 trở lên        |
| OS      | Windows 10+, Linux (Ubuntu 20.04+), macOS 12+ |

---

## Cài đặt

### Linux / macOS

```bash
# 1. Clone hoặc giải nén source code
git clone https://github.com/your-org/dataviz.git
cd dataviz

# 2. Tạo virtual environment
python3 -m venv .venv

# 3. Kích hoạt
source .venv/bin/activate # Linux
.venv\Scripts\activate.bat # Window

# 4. Cài đặt DataViz và tất cả dependencies
pip install -e .

# 5. Kiểm tra
dataviz --version
```

---

## Cấu hình provider AI

DataViz dùng một LLM provider để tạo narrative cho báo cáo. Bước này tuỳ chọn — nếu bỏ qua, các phần text vẫn được tạo tự động từ dữ liệu.

### Cấu hình Claude (Anthropic)

```bash
dataviz config set --provider claude --key sk-ant-...
```

### Cấu hình OpenAI

```bash
dataviz config set --provider openai --key sk-...
```

### Cấu hình Gemini

```bash
dataviz config set --provider gemini --key AIza...
```

### Chỉ định model cụ thể

```bash
dataviz config set --provider claude --key sk-ant-... --model claude-opus-4-6
dataviz config set --provider openai --key sk-...    --model gpt-4o-mini
```

### Xem config hiện tại

```bash
dataviz config show
```

Output ví dụ:
```
Provider:  claude
Model:     claude-sonnet-4-6
API Key:   sk-ant-**
Lang:      auto
Output:    html
Out Dir:   ./dataviz_output
Tool Gen:  deferred
```

Config được lưu tại:
- **Linux/macOS:** `~/.config/dataviz/config.json`
- **Windows:** `C:\Users\<tên bạn>\.config\dataviz\config.json`

Bạn cũng có thể tạo file `.dataviz/config.json` ngay trong thư mục dự án để override config global (hữu ích khi làm việc với nhiều project khác nhau).

---

## Hướng dẫn sử dụng

### Phân tích một file

```bash
dataviz sales.csv --output html --no-tui
```

DataViz sẽ:
1. Đọc file và detect schema
2. Tính thống kê mô tả, phát hiện null, outlier, time series
3. Tự chọn loại chart phù hợp và render bằng Altair/Vega
4. Xuất báo cáo ra `./dataviz_output/report.html`

### Chọn định dạng output

```bash
# HTML (mặc định) — interactive, có thể zoom/tooltip trên chart
dataviz sales.csv --output html --no-tui

# PDF — A4, phù hợp để in hoặc gửi email
dataviz sales.csv --output pdf --no-tui

# Markdown — plain text, embed vào wiki hoặc Git repo
dataviz sales.csv --output md --no-tui

# Jupyter Notebook — mở trong JupyterLab để tiếp tục phân tích
dataviz sales.csv --output notebook --no-tui
```

### Chỉ định thư mục output

```bash
dataviz sales.csv --output html --out-dir ./reports/q3 --no-tui
```

### Chọn sheet trong file Excel

```bash
dataviz data.xlsx --sheet "Sheet2" --output html --no-tui
```

### Phân tích tập trung vào chủ đề cụ thể

```bash
dataviz sales.csv --focus "revenue trends by region" --output html --no-tui
```

### Chọn ngôn ngữ báo cáo

```bash
# Tiếng Anh
dataviz sales.csv --lang en --output html --no-tui

# Tiếng Việt
dataviz sales.csv --lang vi --output html --no-tui

# Tự động detect từ locale hệ thống (mặc định)
dataviz sales.csv --lang auto --output html --no-tui
```

### Chế độ phân tích

```bash
# Nhanh — chỉ sample và stats cơ bản
dataviz sales.csv --fast --output html --no-tui

# Sâu — thêm correlation, outlier detection, time series
dataviz sales.csv --deep --output html --no-tui
```

---

## Phân tích nhiều file (join)

### Join tự động (infer key)

Nếu các file có chung cột tên giống nhau, DataViz tự suy ra join key:

```bash
dataviz orders.csv customers.csv --output html --no-tui
```

### Chỉ định join key

```bash
dataviz orders.csv customers.csv --join-on customer_id --output html --no-tui
```

### Chỉ định kiểu join

```bash
# Inner join (mặc định) — chỉ giữ rows khớp cả hai file
dataviz orders.csv customers.csv --join-on customer_id --join-type inner --output html --no-tui

# Left join — giữ tất cả rows của file đầu tiên
dataviz orders.csv customers.csv --join-on customer_id --join-type left --output html --no-tui

# Outer join — giữ tất cả rows của cả hai file
dataviz orders.csv customers.csv --join-on customer_id --join-type outer --output html --no-tui
```

> **Lưu ý:** Với file lớn (> 500.000 rows), DataViz sẽ cảnh báo về việc load toàn bộ dữ liệu vào RAM. Hãy đảm bảo máy có đủ bộ nhớ trước khi join.

---

## Override provider theo từng lần chạy

Không cần đổi config global, có thể override trực tiếp trên command line:

```bash
# Dùng OpenAI thay vì provider mặc định
dataviz sales.csv --provider openai --output html --no-tui

# Dùng model nhẹ hơn để chạy nhanh
dataviz sales.csv --provider claude --model claude-haiku-4-5-20251001 --output html --no-tui
```

---

## Sessions

Session lưu lại kết quả phân tích để dùng lại sau.

```bash
# Chạy và lưu session với tên
dataviz sales.csv --session q3-review --output html --no-tui

# Xem danh sách sessions đã lưu
dataviz session list

# Mở lại một session
dataviz session open q3-review
```

---

## Cache

DataViz cache kết quả đọc file để tăng tốc các lần chạy sau với cùng file.

```bash
# Xoá toàn bộ cache
dataviz cache clear

# Bỏ qua cache cho lần chạy này
dataviz sales.csv --no-cache --output html --no-tui
```

---

## Tool generation

DataViz có hệ thống tự sinh tool (dùng LLM để tạo tool mới theo yêu cầu). Các tool pending chưa chạy được quản lý qua subcommand này.

```bash
# Xem danh sách tool đang pending
dataviz tool-gen list

# Chạy tất cả tool pending
dataviz tool-gen run

# Bỏ tất cả tool pending
dataviz tool-gen discard
```

---

## Tham chiếu lệnh đầy đủ

```
dataviz [files...] [options]
dataviz config set   --provider NAME --key KEY [--model MODEL] [--base-url URL]
dataviz config update --provider NAME [--key KEY] [--model MODEL] [--base-url URL]
dataviz config show
dataviz session list
dataviz session open NAME
dataviz cache clear
dataviz tool-gen list
dataviz tool-gen run
dataviz tool-gen discard
dataviz --version
```

### Tất cả options cho lệnh phân tích

| Flag | Mặc định | Mô tả |
|------|----------|-------|
| `--output` | `html` | Định dạng output: `html`, `pdf`, `md`, `notebook` |
| `--out-dir` | `./dataviz_output` | Thư mục chứa báo cáo |
| `--lang` | `auto` | Ngôn ngữ báo cáo: `en`, `vi`, `auto` |
| `--fast` | tắt | Chế độ phân tích nhanh |
| `--deep` | tắt | Chế độ phân tích sâu |
| `--focus` | — | Gợi ý chủ đề phân tích cho LLM |
| `--sheet` | — | Tên sheet cho file Excel |
| `--join-on` | — | Tên cột để join nhiều file |
| `--join-type` | `inner` | Kiểu join: `inner`, `left`, `outer` |
| `--provider` | từ config | Override provider cho lần chạy này |
| `--model` | từ config | Override model cho lần chạy này |
| `--no-cache` | tắt | Bỏ qua cache |
| `--session NAME` | — | Lưu kết quả vào session có tên |
| `--no-tui` | tắt | Chạy ở chế độ CLI thuần, không mở TUI |
| `--template` | `default` | Tên template dashboard |
| `--version` | — | In phiên bản và thoát |

---

## Gỡ lỗi thường gặp

**`dataviz: command not found` sau khi cài**
→ Venv chưa được kích hoạt. Chạy lại lệnh activate tương ứng với OS của bạn (xem phần Cài đặt).

**`ModuleNotFoundError: No module named 'altair'`**
→ Cài thiếu dependency. Chạy `pip install -e .` trong thư mục gốc của project.

**`WeasyPrint` báo lỗi khi xuất PDF trên Windows**
→ WeasyPrint trên Windows cần GTK runtime. Tải và cài từ [gtk.org](https://www.gtk.org/docs/installations/windows/), sau đó restart terminal.

**Chart trống trong file HTML**
→ File HTML dùng Vega-Embed qua CDN. Cần kết nối internet khi mở file. Để dùng offline, thêm flag `--template offline` (tính năng đang phát triển).

**Lỗi `ResourceWarning` khi join file lớn**
→ DataViz cảnh báo khi file > 500.000 rows. Không phải lỗi — pipeline vẫn tiếp tục. Nếu hết RAM, hãy lọc bớt dữ liệu trước khi join.

---

## Cấu trúc output

Sau khi chạy, thư mục output (mặc định `./dataviz_output`) chứa:

```
dataviz_output/
├── report.html      # Báo cáo HTML với charts interactive
├── report.pdf       # Báo cáo PDF (nếu dùng --output pdf)
├── report.md        # Báo cáo Markdown (nếu dùng --output md)
└── report.ipynb     # Jupyter Notebook (nếu dùng --output notebook)
```

---

## Tài liệu thêm

- [Design overview](design/README.md)
- [Configuration guide](docs/configuration.md)
- [Roadmap](ROADMAP.md)