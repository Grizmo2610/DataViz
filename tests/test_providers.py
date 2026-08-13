from __future__ import annotations

import unittest

from dataviz.providers import ClaudeProvider, GeminiProvider, OpenAIProvider, get_provider


class ProviderTests(unittest.TestCase):
    """Verify provider factory and formatting behavior."""

    def test_get_provider_returns_openai_provider(self) -> None:
        """The provider factory should create an OpenAI provider when configured."""

        provider = get_provider(
            {
                "default_provider": "openai",
                "providers": {"openai": {"api_key": "k", "model": "m", "base_url": "https://example.com"}},
            }
        )
        self.assertIsInstance(provider, OpenAIProvider)

    def test_get_provider_returns_claude_provider(self) -> None:
        """The provider factory should create a Claude provider by default."""

        provider = get_provider({"providers": {"claude": {"api_key": "k", "model": "m"}}})
        self.assertIsInstance(provider, ClaudeProvider)

    def test_get_provider_returns_gemini_provider(self) -> None:
        """The provider factory should create a Gemini provider when configured."""

        provider = get_provider({"default_provider": "gemini", "providers": {"gemini": {"api_key": "k", "model": "m"}}})
        self.assertIsInstance(provider, GeminiProvider)


if __name__ == "__main__":
    unittest.main()
