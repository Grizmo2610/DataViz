from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dataviz.session import list_sessions, open_session, save_session


class SessionTests(unittest.TestCase):
    """Verify session persistence helpers."""

    def test_save_and_open_session(self) -> None:
        """Session metadata should round-trip through disk."""

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            with patch("dataviz.session.Path.home", return_value=home):
                session_dir = save_session("q3-analysis", {"output_format": "html"})
                loaded = open_session("q3-analysis")
                self.assertTrue(session_dir.exists())
                self.assertEqual(loaded["session_name"], "q3-analysis")
                self.assertEqual(loaded["output_format"], "html")

    def test_list_sessions_returns_saved_sessions(self) -> None:
        """Saved sessions should appear in the list output."""

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            with patch("dataviz.session.Path.home", return_value=home):
                save_session("q3-analysis", {"output_format": "html"})
                sessions = list_sessions()
                self.assertEqual(len(sessions), 1)
                self.assertEqual(sessions[0]["session_name"], "q3-analysis")


if __name__ == "__main__":
    unittest.main()
