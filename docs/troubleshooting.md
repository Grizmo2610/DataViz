# Troubleshooting

## `dataviz: command not found` after installation

The virtual environment is not activated. Run the activation command for your OS:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate.bat
```

Then retry your command.

---

## `ModuleNotFoundError: No module named 'altair'`

A dependency is missing. Run the following from the project root:

```bash
pip install -e .
```

---

## WeasyPrint errors when exporting PDF on Windows

WeasyPrint on Windows requires the GTK runtime. Download and install it from [gtk.org](https://www.gtk.org/docs/installations/windows/), then restart your terminal and try again.

---

## Charts are blank in the HTML report

The HTML report loads Vega-Embed from a CDN and requires an internet connection when opened in the browser. An offline template is planned — follow the [roadmap](../ROADMAP.md) for updates. In the meantime, open the file with an active internet connection.

---

## `ResourceWarning` when joining large files

This is a warning, not a failure — the pipeline continues normally. It appears when a file exceeds 500,000 rows. If you run out of RAM, filter or sample the data before joining.
