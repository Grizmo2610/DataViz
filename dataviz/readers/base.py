from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseReader(ABC):
    """Abstract base class for data readers."""

    @abstractmethod
    def read_sample(self, file_path: str | Path, n_rows: int = 20) -> Any:
        """Read a sample from the input file.

        Args:
            file_path: Source file path.
            n_rows: Number of rows to read.

        Returns:
            A sample payload.
        """

    @abstractmethod
    def read_full_stats(self, file_path: str | Path) -> Any:
        """Read full-dataset statistics.

        Args:
            file_path: Source file path.

        Returns:
            A statistics payload.
        """
