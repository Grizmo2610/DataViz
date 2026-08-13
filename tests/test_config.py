from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dataviz.config import BUILT_IN_DEFAULTS, format_config_summary, load_config, save_global_config


class ConfigTests(unittest.TestCase):
    """Verify config loading and formatting behavior."""

    def test_load_config_merges_global_local_and_cli(self) -> None:
        """CLI values should override local, which override global, which override defaults."""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            home.mkdir()
            global_dir = home / ".config" / "dataviz"
            global_dir.mkdir(parents=True)
            (global_dir / "config.json").write_text(
                json.dumps(
                    {
                        "output": "pdf",
                        "providers": {"claude": {"api_key": "global-key", "model": "claude-global"}},
                    }
                ),
                encoding="utf-8",
            )

            local_dir = root / "project"
            local_dir.mkdir()
            (local_dir / ".dataviz").mkdir()
            (local_dir / ".dataviz" / "config.json").write_text(
                json.dumps(
                    {
                        "lang": "vi",
                        "providers": {"claude": {"model": "claude-local"}},
                    }
                ),
                encoding="utf-8",
            )

            with patch("dataviz.config.Path.home", return_value=home):
                config = load_config({"output": "html"}, base_dir=local_dir)

        self.assertEqual(config["output"], "html")
        self.assertEqual(config["lang"], "vi")
        self.assertEqual(config["default_provider"], BUILT_IN_DEFAULTS["default_provider"])
        self.assertEqual(config["providers"]["claude"]["api_key"], "global-key")
        self.assertEqual(config["providers"]["claude"]["model"], "claude-local")

    def test_save_global_config_writes_file(self) -> None:
        """Saving global config should create the config file."""

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            with patch("dataviz.config.Path.home", return_value=home):
                path = save_global_config({"default_provider": "openai"})

            self.assertTrue(path.exists())
            self.assertIn("openai", path.read_text(encoding="utf-8"))

    def test_format_config_summary_masks_key(self) -> None:
        """Config summary should mask API keys before display."""

        summary = format_config_summary(
            {
                "default_provider": "claude",
                "lang": "auto",
                "output": "html",
                "out_dir": "./dataviz_output",
                "tool_gen_mode": "deferred",
                "providers": {"claude": {"api_key": "sk-ant-1234567890", "model": "claude-sonnet-4-6"}},
            }
        )

        self.assertIn("sk-ant-1", summary)
        self.assertIn("****", summary)


if __name__ == "__main__":
    unittest.main()
