# DataViz

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

<div align="center">
  <a href="https://github.com/Grizmo2610/DataViz">
    <img src="images/dataviz-logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">DataViz</h3>

  <p align="center">
    A CLI that automatically analyzes tabular data, selects appropriate charts, and exports multi-format reports.
    <br />
    <a href="design/README.md"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/Grizmo2610/DataViz">View Demo</a>
    ·
    <a href="https://github.com/Grizmo2610/DataViz/issues/new?labels=bug&template=bug-report.md">Report Bug</a>
    ·
    <a href="https://github.com/Grizmo2610/DataViz/issues/new?labels=enhancement&template=feature-request.md">Request Feature</a>
  </p>
</div>

---

## About

**DataViz** is a CLI tool that automatically analyzes tabular data (CSV, Excel, Parquet), picks the right chart type, and exports reports in multiple formats: HTML, PDF, Markdown, or Jupyter Notebook.

It integrates with LLM providers (Claude, OpenAI, Gemini) to generate intelligent narrative for each report, supports single-file analysis and multi-file joins, and provides a session & cache system to speed up repeated workflows.

### Core Features

- **Auto-analysis** — Detects schema, computes descriptive statistics, identifies nulls, outliers, and time series — no manual configuration required.
- **Smart Chart Selection** — Automatically chooses and renders the most suitable chart type using Altair/Vega.
- **Multi-format Output** — Interactive HTML, printable PDF (A4), plain Markdown, or Jupyter Notebook.
- **LLM Narrative** — Integrates Claude (Anthropic), OpenAI, and Gemini to generate natural-language analysis sections.
- **Multi-file Join** — Infers join keys automatically or accepts manual specification; supports inner, left, and outer joins.
- **MCP Server & Skill** — Exposes analysis, charts, and report export as MCP tools (`dataviz-mcp`), with a ready-made skill for AI assistants. No LLM API key needed.
- **Session & Cache** — Persists analysis results for reuse; caches parsed files to speed up subsequent runs.

---

## Documentation

| Doc | Description |
|-----|-------------|
| [Installation & Quickstart](docs/getting-started.md) | Prerequisites, install steps, and your first run |
| [Configuration](docs/configuration.md) | Setting up LLM providers and config files |
| [Usage Guide](docs/usage.md) | Full command reference with examples |
| [MCP Server & Skill](docs/mcp.md) | Use DataViz from AI assistants through MCP tools and a skill |
| [Troubleshooting](docs/troubleshooting.md) | Common errors and fixes |
| [Design Overview](design/README.md) | Architecture and system design |
| [Roadmap](ROADMAP.md) | Planned features |

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

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/Grizmo2610/DataViz.git
cd DataViz
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Configure an LLM provider (optional)
dataviz config set --provider claude --key sk-ant-...

# Analyze a file and export an HTML report
dataviz sales.csv --output html --no-tui
```

See [docs/getting-started.md](docs/getting-started.md) for the full installation guide and [docs/usage.md](docs/usage.md) for all available options.

---

## Output Structure

```
dataviz_output/
├── report.html      # Interactive HTML report with charts
├── report.pdf       # PDF report  (--output pdf)
├── report.md        # Markdown report  (--output md)
└── report.ipynb     # Jupyter Notebook  (--output notebook)
```

---

## Roadmap

- [x] CLI architecture and system design
- [x] Auto-analysis: schema detection, descriptive stats, null/outlier/time-series detection
- [x] Smart chart selection with Altair/Vega
- [x] LLM integration (Claude, OpenAI, Gemini) for narrative generation
- [x] Multi-file join (inner / left / outer)
- [x] Session & cache management
- [ ] User authentication & usage tracking
- [ ] Offline dashboard template (`--template offline`)
- [ ] Production cloud deployment
- [ ] Additional input formats (JSON, SQL, Google Sheets)

See [open issues](https://github.com/Grizmo2610/DataViz/issues) for the full list.

---

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<a href="https://github.com/Grizmo2610/DataViz/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Grizmo2610/DataViz" />
</a>

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

## Contact

**Grizmo2610** — [hoangtuantu893@gmail.com](mailto:hoangtuantu893@gmail.com)

Project Link: [https://github.com/Grizmo2610/DataViz](https://github.com/Grizmo2610/DataViz)

---

## Acknowledgments

- [Altair & Vega](https://altair-viz.github.io/) visualization ecosystem
- [Anthropic Claude](https://www.anthropic.com/), [OpenAI](https://openai.com/), [Google Gemini](https://deepmind.google/technologies/gemini/) APIs
- [WeasyPrint](https://weasyprint.org/), [Jupyter](https://jupyter.org/), [Pandoc](https://pandoc.org/) communities

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