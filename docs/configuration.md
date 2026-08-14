# Configuration Guide

DataViz uses plain JSON configuration files.

## Where config lives

There are two config layers:

- Global config: `~/.config/dataviz/config.json`
- Local config: `.dataviz/config.json`

Config is merged in this order:

1. Built-in defaults
2. Global config
3. Local config
4. CLI flags

Later layers override earlier layers field by field.

## Supported providers

DataViz supports these provider names:

- `claude`
- `openai`
- `openai_compatible`
- `gemini`

## Common fields

These fields are supported at the top level:

- `default_provider`
- `tool_gen_mode`
- `lang`
- `output`
- `out_dir`

`tool_gen_mode` can be:

- `immediate`
- `deferred`

`lang` can be:

- `en`
- `vi`
- `auto`

`output` can be:

- `html`
- `md`
- `pdf`
- `notebook`

## Provider fields

Each provider entry may include:

- `api_key`
- `model`
- `base_url` for OpenAI-compatible endpoints

The CLI command for a provider always updates that provider and sets it as `default_provider`.

## Claude setup

Claude uses the `claude` provider name.

```powershell
python -m dataviz config set --provider claude --key sk-ant-...
python -m dataviz config update --provider claude --model claude-sonnet-4-6
```

Example config:

```json
{
  "default_provider": "claude",
  "providers": {
    "claude": {
      "api_key": "sk-ant-...",
      "model": "claude-sonnet-4-6"
    }
  }
}
```

Recommended when you want Anthropic Claude models.

## OpenAI setup

OpenAI uses the `openai` provider name.

```powershell
python -m dataviz config set --provider openai --key sk-...
python -m dataviz config update --provider openai --model gpt-4o
```

Example config:

```json
{
  "default_provider": "openai",
  "providers": {
    "openai": {
      "api_key": "sk-...",
      "model": "gpt-4o",
      "base_url": "https://api.openai.com/v1"
    }
  }
}
```

Use this for the official OpenAI API.

## OpenAI-compatible setup

Use `openai` when the endpoint behaves like the OpenAI chat API, but override `base_url`.

Examples:

- Groq
- Together
- Azure OpenAI
- Other OpenAI-compatible gateways

```powershell
python -m dataviz config set --provider openai --key gsk_...
python -m dataviz config update --provider openai --base-url https://api.groq.com/openai/v1
python -m dataviz config update --provider openai --model llama-3.1-70b-versatile
```

Example config:

```json
{
  "default_provider": "openai",
  "providers": {
    "openai": {
      "api_key": "gsk_...",
      "model": "llama-3.1-70b-versatile",
      "base_url": "https://api.groq.com/openai/v1"
    }
  }
}
```

Notes:

- Keep `base_url` pointed at the provider endpoint.
- Use the model name required by that provider.

## Gemini setup

Gemini uses the `gemini` provider name.

```powershell
python -m dataviz config set --provider gemini --key AIza...
python -m dataviz config update --provider gemini --model gemini-1.5-pro
```

Example config:

```json
{
  "default_provider": "gemini",
  "providers": {
    "gemini": {
      "api_key": "AIza...",
      "model": "gemini-1.5-pro"
    }
  }
}
```

## Local overrides

To override settings only for the current project, create `.dataviz/config.json`.

Example:

```json
{
  "default_provider": "openai",
  "output": "pdf",
  "lang": "vi",
  "tool_gen_mode": "immediate"
}
```

## Check your config

```powershell
python -m dataviz config show
```

`config show` masks API keys before printing them.

## Practical setup examples

Claude for a project:

```powershell
python -m dataviz config set --provider claude --key sk-ant-...
python -m dataviz config update --provider claude --model claude-sonnet-4-6
```

OpenAI for a project:

```powershell
python -m dataviz config set --provider openai --key sk-...
python -m dataviz config update --provider openai --model gpt-4o
```

Groq through OpenAI-compatible config:

```powershell
python -m dataviz config set --provider openai --key gsk_...
python -m dataviz config update --provider openai --base-url https://api.groq.com/openai/v1
python -m dataviz config update --provider openai --model llama-3.1-70b-versatile
```

Gemini for a project:

```powershell
python -m dataviz config set --provider gemini --key AIza...
python -m dataviz config update --provider gemini --model gemini-1.5-pro
```
