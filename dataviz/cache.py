from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


def get_cache_dir(base_dir: Path | None = None) -> Path:
    """Return the project cache directory.

    Args:
        base_dir: Optional project root to resolve from.

    Returns:
        The `.dataviz/cache` directory path.
    """

    root = base_dir or Path.cwd()
    return root / ".dataviz" / "cache"


def compute_file_hash(file_path: str | Path) -> str:
    """Compute a SHA256 hash for a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        A hexadecimal SHA256 digest.
    """

    sha256 = hashlib.sha256()
    with Path(file_path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_cache_path(file_hash: str, base_dir: Path | None = None) -> Path:
    """Return the cache file path for a given hash.

    Args:
        file_hash: SHA256 digest for the source file.
        base_dir: Optional project root to resolve from.

    Returns:
        The JSON cache file path.
    """

    return get_cache_dir(base_dir) / f"{file_hash}.json"


def read_cache(file_hash: str, base_dir: Path | None = None) -> dict[str, Any]:
    """Read a cached analysis payload.

    Args:
        file_hash: SHA256 digest for the source file.
        base_dir: Optional project root to resolve from.

    Returns:
        Cached JSON payload, or an empty dictionary if missing.
    """

    path = get_cache_path(file_hash, base_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_cache(file_hash: str, payload: dict[str, Any], base_dir: Path | None = None) -> Path:
    """Write a cached analysis payload.

    Args:
        file_hash: SHA256 digest for the source file.
        payload: JSON-serializable analysis data.
        base_dir: Optional project root to resolve from.

    Returns:
        The cache file path that was written.
    """

    path = get_cache_path(file_hash, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def clear_cache(base_dir: Path | None = None) -> Path:
    """Remove the entire project cache directory.

    Args:
        base_dir: Optional project root to resolve from.

    Returns:
        The cache directory that was removed or targeted.
    """

    cache_dir = get_cache_dir(base_dir)
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    return cache_dir
