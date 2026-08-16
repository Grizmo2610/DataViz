# Configuration

DataViz uses an LLM provider to generate narrative text for reports. This step is **optional** — if skipped, text sections are still generated automatically from the data itself.

## Setting a Provider

```bash
# Claude (Anthropic)
dataviz config set --provider claude --key sk-ant-...

# OpenAI
dataviz config set --provider openai --key sk-...

# Gemini
dataviz config set --provider gemini --key AIza...

# Specify a particular model
dataviz config set --provider claude --key sk-ant-... --model claude-opus-4-6
```

## Viewing the Current Config

```bash
dataviz config show
```

## Updating a Provider

```bash
dataviz config update --provider claude --key sk-ant-NEW... --model claude-haiku-4-5-20251001
```

## Config File Locations

The global config is stored at:

| OS | Path |
|----|------|
| Linux / macOS | `~/.config/dataviz/config.json` |
| Windows | `C:\Users\<you>\.config\dataviz\config.json` |

You can also place a `.dataviz/config.json` file in your project directory to override the global config for that project.

## Per-run Overrides

You can override the provider or model for a single run without modifying the saved config:

```bash
# Use OpenAI instead of the default provider
dataviz sales.csv --provider openai --output html --no-tui

# Use a lighter model for a faster run
dataviz sales.csv --provider claude --model claude-haiku-4-5-20251001 --output html --no-tui
```
