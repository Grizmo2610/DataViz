from .base import BaseProvider
from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider


def get_provider(config: dict[str, object]) -> BaseProvider:
    """Create a provider instance from merged configuration.

    Args:
        config: Merged configuration dictionary.

    Returns:
        A provider instance.
    """

    name = str(config.get("default_provider", "claude"))
    providers = dict(config.get("providers", {}))
    provider_config = dict(providers.get(name, {}))

    if name == "openai":
        return OpenAIProvider(
            api_key=str(provider_config.get("api_key", "")),
            model=str(provider_config.get("model", "gpt-4o")),
            base_url=provider_config.get("base_url") if provider_config.get("base_url") else None,
        )
    if name == "gemini":
        return GeminiProvider(
            api_key=str(provider_config.get("api_key", "")),
            model=str(provider_config.get("model", "gemini-1.5-pro")),
        )
    return ClaudeProvider(
        api_key=str(provider_config.get("api_key", "")),
        model=str(provider_config.get("model", "claude-sonnet-4-6")),
    )


__all__ = ["BaseProvider", "ClaudeProvider", "GeminiProvider", "OpenAIProvider", "get_provider"]
