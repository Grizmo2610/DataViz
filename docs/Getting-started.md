# Getting Started

This guide covers everything you need to install DataViz and run your first analysis.

## Prerequisites

| Requirement | Minimum version |
|-------------|----------------|
| Python | 3.11+ |
| pip | 23.0+ |
| OS | Windows 10+, Ubuntu 20.04+, macOS 12+ |

## Installation

### 1. Clone the repository

```sh
git clone https://github.com/Grizmo2610/DataViz.git
cd DataViz
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate.bat
```

### 3. Install DataViz

```bash
pip install -e .
```

### 4. Verify the installation

```bash
dataviz --version
```

## Your First Analysis

Once installed, point DataViz at any CSV, Excel, or Parquet file:

```bash
dataviz sales.csv --output html --no-tui
```

DataViz will:

1. Read the file and detect its schema
2. Compute descriptive statistics, detect nulls, outliers, and time series
3. Automatically select chart types and render them with Altair/Vega
4. Export a report to `./dataviz_output/report.html`

Open `report.html` in any browser — charts are interactive (zoom, tooltip, hover).

## Next Steps

- [Configure an LLM provider](configuration.md) to add AI-generated narrative to your reports
- [Explore all CLI options](usage.md) for output formats, multi-file joins, sessions, and more
- [Troubleshooting](troubleshooting.md) if something goes wrong