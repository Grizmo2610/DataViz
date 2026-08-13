from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def get_sessions_dir() -> Path:
    """Return the user-level sessions directory.

    Returns:
        The directory that stores saved analysis sessions.
    """

    return Path.home() / ".config" / "dataviz" / "sessions"


def get_session_path(session_name: str) -> Path:
    """Return the directory path for a named session.

    Args:
        session_name: Session identifier.

    Returns:
        The directory containing the session files.
    """

    return get_sessions_dir() / session_name


def save_session(session_name: str, metadata: dict[str, Any]) -> Path:
    """Save session metadata to disk.

    Args:
        session_name: Session identifier.
        metadata: Metadata payload to persist.

    Returns:
        The session directory path.
    """

    session_dir = get_session_path(session_name)
    session_dir.mkdir(parents=True, exist_ok=True)

    payload = dict(metadata)
    payload.setdefault("session_name", session_name)
    payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())

    metadata_path = session_dir / "metadata.json"
    metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return session_dir


def list_sessions() -> list[dict[str, Any]]:
    """List all saved sessions.

    Returns:
        A list of session metadata dictionaries sorted by name.
    """

    sessions_dir = get_sessions_dir()
    if not sessions_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    for metadata_path in sorted(sessions_dir.glob("*/metadata.json")):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        payload["session_dir"] = str(metadata_path.parent)
        results.append(payload)
    return results


def open_session(session_name: str) -> dict[str, Any]:
    """Load a saved session by name.

    Args:
        session_name: Session identifier.

    Returns:
        Session metadata loaded from metadata.json.
    """

    metadata_path = get_session_path(session_name) / "metadata.json"
    if not metadata_path.exists():
        return {}
    return json.loads(metadata_path.read_text(encoding="utf-8"))
