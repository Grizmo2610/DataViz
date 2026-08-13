from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BUILT_IN_DEFAULTS: dict[str, Any] = {
    "default_provider": "claude",
    "tool_gen_mode": "deferred",
    "lang": "auto",
    "output": "html",
    "out_dir": "./dataviz_output",
}


def get_global_config_dir() -> Path:
    """Return the user-level DataViz config directory.

    Returns:
        The directory that stores user-level configuration files.
    """

    return Path.home() / ".config" / "dataviz"


def get_global_config_path() -> Path:
    """Return the user-level configuration file path.

    Returns:
        The full path to the global config.json file.
    """

    return get_global_config_dir() / "config.json"


def get_local_config_path(base_dir: Path | None = None) -> Path:
    """Return the project-level configuration file path.

    Args:
        base_dir: Optional directory used as the project root.

    Returns:
        The full path to the local .dataviz/config.json file.
    """

    root = base_dir or Path.cwd()
    return root / ".dataviz" / "config.json"


def read_json_file(path: Path) -> dict[str, Any]:
    """Read a JSON file and return a dictionary.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON data, or an empty dictionary if the file is missing.
    """

    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def write_json_file(path: Path, data: dict[str, Any]) -> None:
    """Write JSON data to disk.

    Args:
        path: Destination file path.
        data: JSON-serializable dictionary to write.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_config(cli_overrides: dict[str, Any] | None = None, base_dir: Path | None = None) -> dict[str, Any]:
    """Load config from built-in defaults, global config, local config, and CLI overrides.

    Args:
        cli_overrides: Command-line values that should win over file-based config.
        base_dir: Optional project root for resolving the local config file.

    Returns:
        A merged configuration dictionary.
    """

    merged: dict[str, Any] = dict(BUILT_IN_DEFAULTS)
    merged.update(read_json_file(get_global_config_path()))
    merged.update(read_json_file(get_local_config_path(base_dir)))

    for key, value in (cli_overrides or {}).items():
        if value is not None:
            merged[key] = value

    return merged


def load_global_config() -> dict[str, Any]:
    """Load the user-level config file.

    Returns:
        The parsed global configuration dictionary.
    """

    return read_json_file(get_global_config_path())


def save_global_config(config: dict[str, Any]) -> Path:
    """Persist the user-level config file.

    Args:
        config: Configuration dictionary to write.

    Returns:
        The path that was written.
    """

    path = get_global_config_path()
    write_json_file(path, config)
    return path


def update_provider_config(
    provider: str,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Update the stored configuration for a provider.

    Args:
        provider: Provider name to update.
        api_key: Optional API key value.
        model: Optional model name.
        base_url: Optional provider base URL.

    Returns:
        The updated global configuration dictionary.
    """

    config = load_global_config()
    providers = dict(config.get("providers", {}))
    current = dict(providers.get(provider, {}))

    if api_key is not None:
        current["api_key"] = api_key
    if model is not None:
        current["model"] = model
    if base_url is not None:
        current["base_url"] = base_url

    providers[provider] = current
    config["providers"] = providers
    config["default_provider"] = provider
    save_global_config(config)
    return config


def mask_secret(value: str | None) -> str:
    """Mask a secret so only a small prefix remains visible.

    Args:
        value: Secret value to mask.

    Returns:
        A masked string suitable for display.
    """

    if not value:
        return "(not set)"
    if len(value) <= 8:
        return value[:2] + "****"
    return value[:8] + "****"


def format_config_summary(config: dict[str, Any]) -> str:
    """Format a compact human-readable config summary.

    Args:
        config: Merged configuration dictionary.

    Returns:
        A multi-line string suitable for terminal display.
    """

    provider_name = config.get("default_provider", "(not set)")
    provider_config = dict(config.get("providers", {}).get(provider_name, {}))
    lines = [
        f"Provider:  {provider_name}",
        f"Model:     {provider_config.get('model', '(not set)')}",
        f"API Key:   {mask_secret(provider_config.get('api_key'))}",
        f"Lang:      {config.get('lang', '(not set)')}",
        f"Output:    {config.get('output', '(not set)')}",
        f"Out Dir:   {config.get('out_dir', '(not set)')}",
        f"Tool Gen:  {config.get('tool_gen_mode', '(not set)')}",
    ]
    if provider_config.get("base_url"):
        lines.append(f"Base URL:  {provider_config['base_url']}")
    return "\n".join(lines)
