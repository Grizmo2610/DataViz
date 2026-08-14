<!-- Improved compatibility of back to top link -->

<a id="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![project\_license][license-shield]][license-url]

<br />
<div align="center">
  <a href="https://github.com/Grizmo2610/DataViz">
    <img src="images/dataviz-logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">DataViz</h3>

  <p align="center">
    CLI tự động phân tích dữ liệu dạng bảng, chọn chart phù hợp, và xuất báo cáo đa định dạng
    <br />
    <a href="design/README.md"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/Grizmo2610/DataViz">View Demo</a>
    &middot;
    <a href="https://github.com/Grizmo2610/DataViz/issues/new?labels=bug&template=bug-report.md">Report Bug</a>
    &middot;
    <a href="https://github.com/Grizmo2610/DataViz/issues/new?labels=enhancement&template=feature-request.md">Request Feature</a>
  </p>
</div>

---

## About The Project

**DataViz** là một CLI tự động phân tích dữ liệu dạng bảng (CSV, Excel, Parquet), tự chọn loại chart phù hợp, và xuất báo cáo ra nhiều định dạng: HTML, PDF, Markdown, hoặc Jupyter Notebook.

Công cụ tích hợp LLM provider (Claude, OpenAI, Gemini) để tạo narrative thông minh cho báo cáo, hỗ trợ phân tích đơn file lẫn join nhiều file, và cung cấp hệ thống session & cache để tăng tốc các luồng làm việc lặp lại.

### Core Features

* **Tự động phân tích**: Detect schema, tính thống kê mô tả, phát hiện null, outlier, time series — không cần cấu hình thủ công.
* **Smart Chart Selection**: Tự chọn loại chart phù hợp và render bằng Altair/Vega theo từng kiểu dữ liệu.
* **Đa định dạng output**: HTML interactive, PDF (A4), Markdown, Jupyter Notebook.
* **LLM Narrative**: Tích hợp Claude (Anthropic), OpenAI, và Gemini để tạo phần phân tích ngôn ngữ tự nhiên.
* **Multi-file Join**: Tự suy ra join key hoặc chỉ định thủ công, hỗ trợ inner / left / outer join.
* **Session & Cache**: Lưu kết quả phân tích để dùng lại, cache file đã đọc để tăng tốc lần chạy sau.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Documentation

Explore the system design and architecture documents:
* 📐 [Design Overview](design/README.md)
* ⚙️ [Configuration Guide](docs/configuration.md)
* 🗺️ [Roadmap](ROADMAP.md)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Built With

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Altair-Vega-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Claude-Anthropic-blueviolet?style=for-the-badge" />
  <img src="https://img.shields.io/badge/OpenAI-GPT-412991?style=for-the-badge&logo=openai&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini-Google-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Jupyter-Notebook-F37626?style=for-the-badge&logo=jupyter&logoColor=white" />
  <img src="https://img.shields.io/badge/WeasyPrint-PDF-green?style=for-the-badge" />
</p>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Getting Started & Installation

### Prerequisites

| Yêu cầu | Phiên bản tối thiểu |
|---------|---------------------|
| Python  | 3.11 trở lên        |
| pip     | 23.0 trở lên        |
| OS      | Windows 10+, Linux (Ubuntu 20.04+), macOS 12+ |

### 1. Clone the Repository

```sh
git clone https://github.com/Grizmo2610/DataViz.git
```

### 2. Open the project folder

```sh
cd DataViz
```

### 3. Cài đặt DataViz

```bash
# Tạo virtual environment
python3 -m venv .venv

# Kích hoạt
source .venv/bin/activate   # Linux / macOS
.venv\Scripts\activate.bat  # Windows

# Cài đặt DataViz và tất cả dependencies
pip install -e .

# Kiểm tra
dataviz --version
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Usage

### Cấu hình provider AI

DataViz dùng một LLM provider để tạo narrative cho báo cáo. Bước này tuỳ chọn — nếu bỏ qua, các phần text vẫn được tạo tự động từ dữ liệu.

```bash
# Claude (Anthropic)
dataviz config set --provider claude --key sk-ant-...

# OpenAI
dataviz config set --provider openai --key sk-...

# Gemini
dataviz config set --provider gemini --key AIza...

# Chỉ định model cụ thể
dataviz config set --provider claude --key sk-ant-... --model claude-opus-4-6

# Xem config hiện tại
dataviz config show
```

Config được lưu tại:
- **Linux/macOS:** `~/.config/dataviz/config.json`
- **Windows:** `C:\Users\<tên bạn>\.config\dataviz\config.json`

Bạn cũng có thể tạo file `.dataviz/config.json` ngay trong thư mục dự án để override config global.

---

### Phân tích một file

```bash
dataviz sales.csv --output html --no-tui
```

DataViz sẽ:
1. Đọc file và detect schema
2. Tính thống kê mô tả, phát hiện null, outlier, time series
3. Tự chọn loại chart phù hợp và render bằng Altair/Vega
4. Xuất báo cáo ra `./dataviz_output/report.html`

---

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

---

### Các tuỳ chọn phân tích khác

```bash
# Chỉ định thư mục output
dataviz sales.csv --output html --out-dir ./reports/q3 --no-tui

# Chọn sheet trong file Excel
dataviz data.xlsx --sheet "Sheet2" --output html --no-tui

# Phân tích tập trung vào chủ đề cụ thể
dataviz sales.csv --focus "revenue trends by region" --output html --no-tui

# Chọn ngôn ngữ báo cáo
dataviz sales.csv --lang en --output html --no-tui   # Tiếng Anh
dataviz sales.csv --lang vi --output html --no-tui   # Tiếng Việt
dataviz sales.csv --lang auto --output html --no-tui # Tự động detect (mặc định)

# Chế độ phân tích nhanh / sâu
dataviz sales.csv --fast --output html --no-tui  # Chỉ sample và stats cơ bản
dataviz sales.csv --deep --output html --no-tui  # Thêm correlation, outlier, time series
```

---

### Phân tích nhiều file (join)

```bash
# Join tự động (infer key) — nếu các file có chung cột tên giống nhau
dataviz orders.csv customers.csv --output html --no-tui

# Chỉ định join key
dataviz orders.csv customers.csv --join-on customer_id --output html --no-tui

# Chỉ định kiểu join
dataviz orders.csv customers.csv --join-on customer_id --join-type inner --output html --no-tui
dataviz orders.csv customers.csv --join-on customer_id --join-type left  --output html --no-tui
dataviz orders.csv customers.csv --join-on customer_id --join-type outer --output html --no-tui
```

> **Lưu ý:** Với file lớn (> 500.000 rows), DataViz sẽ cảnh báo về việc load toàn bộ dữ liệu vào RAM. Hãy đảm bảo máy có đủ bộ nhớ trước khi join.

---

### Override provider theo từng lần chạy

```bash
# Dùng OpenAI thay vì provider mặc định
dataviz sales.csv --provider openai --output html --no-tui

# Dùng model nhẹ hơn để chạy nhanh
dataviz sales.csv --provider claude --model claude-haiku-4-5-20251001 --output html --no-tui
```

---

### Sessions

```bash
# Chạy và lưu session với tên
dataviz sales.csv --session q3-review --output html --no-tui

# Xem danh sách sessions đã lưu
dataviz session list

# Mở lại một session
dataviz session open q3-review
```

---

### Cache

```bash
# Xoá toàn bộ cache
dataviz cache clear

# Bỏ qua cache cho lần chạy này
dataviz sales.csv --no-cache --output html --no-tui
```

---

### Tool generation

```bash
# Xem danh sách tool đang pending
dataviz tool-gen list

# Chạy tất cả tool pending
dataviz tool-gen run

# Bỏ tất cả tool pending
dataviz tool-gen discard
```

---

### Tham chiếu lệnh đầy đủ

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

### Cấu trúc output

Sau khi chạy, thư mục output (mặc định `./dataviz_output`) chứa:

```
dataviz_output/
├── report.html      # Báo cáo HTML với charts interactive
├── report.pdf       # Báo cáo PDF (nếu dùng --output pdf)
├── report.md        # Báo cáo Markdown (nếu dùng --output md)
└── report.ipynb     # Jupyter Notebook (nếu dùng --output notebook)
```

---

### Gỡ lỗi thường gặp

**`dataviz: command not found` sau khi cài**
→ Venv chưa được kích hoạt. Chạy lại lệnh activate tương ứng với OS của bạn (xem phần Getting Started).

**`ModuleNotFoundError: No module named 'altair'`**
→ Cài thiếu dependency. Chạy `pip install -e .` trong thư mục gốc của project.

**`WeasyPrint` báo lỗi khi xuất PDF trên Windows**
→ WeasyPrint trên Windows cần GTK runtime. Tải và cài từ [gtk.org](https://www.gtk.org/docs/installations/windows/), sau đó restart terminal.

**Chart trống trong file HTML**
→ File HTML dùng Vega-Embed qua CDN. Cần kết nối internet khi mở file. Để dùng offline, thêm flag `--template offline` (tính năng đang phát triển).

**Lỗi `ResourceWarning` khi join file lớn**
→ DataViz cảnh báo khi file > 500.000 rows. Không phải lỗi — pipeline vẫn tiếp tục. Nếu hết RAM, hãy lọc bớt dữ liệu trước khi join.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Roadmap

* [x] Kiến trúc CLI và thiết kế hệ thống
* [x] Phân tích tự động: schema detection, thống kê mô tả, null/outlier/time series
* [x] Smart chart selection với Altair/Vega
* [x] Tích hợp LLM (Claude, OpenAI, Gemini) để tạo narrative
* [x] Multi-file join (inner / left / outer)
* [x] Session & cache management
* [ ] User authentication & usage tracking
* [ ] Template dashboard offline (`--template offline`)
* [ ] Production cloud deployment
* [ ] Hỗ trợ thêm định dạng đầu vào (JSON, SQL, Google Sheets)

See the [open issues](https://github.com/Grizmo2610/DataViz/issues) for a full list of proposed features and known issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

### Top Contributors:

<a href="https://github.com/Grizmo2610/DataViz/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Grizmo2610/DataViz" />
</a>

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Contact

Grizmo2610 - [hoangtuantu893@gmail.com](mailto:hoangtuantu893@gmail.com)

Project Link: [https://github.com/Grizmo2610/DataViz](https://github.com/Grizmo2610/DataViz)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Acknowledgments

* Altair & Vega visualization ecosystem
* Anthropic Claude, OpenAI, Google Gemini APIs
* WeasyPrint, Jupyter, Pandoc communities

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

[contributors-shield]: https://img.shields.io/github/contributors/Grizmo2610/DataViz.svg?style=for-the-badge
[contributors-url]: https://github.com/Grizmo2610/DataViz/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Grizmo2610/DataViz.svg?style=for-the-badge
[forks-url]: https://github.com/Grizmo2610/DataViz/network/members
[stars-shield]: https://img.shields.io/github/stars/Grizmo2610/DataViz.svg?style=for-the-badge
[stars-url]: https://github.com/Grizmo2610/DataViz/stargazers
[issues-shield]: https://img.shields.io/github/issues/Grizmo2610/DataViz.svg?style=for-the-badge
[issues-url]: https://github.com/Grizmo2610/DataViz/issues
[license-shield]: https://img.shields.io/github/license/Grizmo2610/DataViz.svg?style=for-the-badge
[license-url]: https://github.com/Grizmo2610/DataViz/blob/main/LICENSE