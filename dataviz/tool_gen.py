from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import get_global_config_dir


def get_pending_tools_path() -> Path:
    """Return the pending tool queue file path.

    Returns:
        The path to `pending_tools.json` under the global config directory.
    """

    return get_global_config_dir() / "pending_tools.json"


def load_pending_tools() -> dict[str, Any]:
    """Load the pending tool queue.

    Returns:
        The queue payload, or an empty queue if no file exists.
    """

    path = get_pending_tools_path()
    if not path.exists():
        return {"pending": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_pending_tools(payload: dict[str, Any]) -> Path:
    """Persist the pending tool queue.

    Args:
        payload: Queue payload to write.

    Returns:
        The pending tools file path.
    """

    path = get_pending_tools_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def list_pending_tools() -> list[dict[str, Any]]:
    """Return the queued tool requests.

    Returns:
        The list of pending tool request dictionaries.
    """

    return list(load_pending_tools().get("pending", []))


def append_pending_tool(request: dict[str, Any]) -> Path:
    """Append a request to the pending tool queue.

    Args:
        request: Tool request payload to append.

    Returns:
        The pending tools file path.
    """

    payload = load_pending_tools()
    pending = list(payload.get("pending", []))
    pending.append(request)
    payload["pending"] = pending
    return save_pending_tools(payload)


def discard_pending_tools() -> Path:
    """Remove the pending tool queue file if it exists.

    Returns:
        The pending tools file path.
    """

    path = get_pending_tools_path()
    if path.exists():
        path.unlink()
    return path


def run_pending_tools() -> list[dict[str, Any]]:
    """Return the pending tool queue without generating code.

    Returns:
        The list of pending tool requests currently queued.
    """

    return list_pending_tools()
