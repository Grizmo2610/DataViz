from __future__ import annotations

import unittest

from dataviz.cli import main


class CliTests(unittest.TestCase):
    """Verify the basic CLI entry points."""

    def test_help_exits_cleanly(self) -> None:
        """The help path should exit without error."""

        with self.assertRaises(SystemExit) as cm:
            main(["--help"])

        self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
