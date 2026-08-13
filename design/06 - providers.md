# 06 — LLM Providers

## Abstract Provider Interface

**File:** `dataviz/providers/base.py`

```python
from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Abstract interface for all LLM providers.

    Subclasses must implement chat() and format_tools().
    """

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        """Send messages to the LLM and return the response.

        Args:
            messages: Conversation history in OpenAI format.
            tools: Optional list of tool definitions for function calling.
            tool_choice: How to handle tool selection ("auto", "none", "required").

        Returns:
            Dict with:
                - content (str): Text response, if any.
                - tool_calls (list): Tool call requests from the LLM.
                - finish_reason (str): "stop", "tool_calls", etc.
        """
        ...

    @abstractmethod
    def format_tools(self, registry_entries: list[dict]) -> list[dict]:
        """Convert registry tool entries to provider-specific tool format.

        Args:
            registry_entries: List of tool dicts from registry.json.

        Returns:
            Tool definitions in the format expected by this provider's API.
        """
        ...
```

---

## OpenAI Provider

**File:** `dataviz/providers/openai_provider.py`

Xử lý cả **OpenAI chính thức** và **OpenAI-compatible endpoints** (Azure, Groq, Together, v.v.) qua `base_url`.

```python
class OpenAIProvider(BaseProvider):
    """Provider for OpenAI and OpenAI-compatible APIs.

    Set base_url in config to use with Azure OpenAI, Groq, Together, etc.
    """

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        super().__init__(api_key, model)
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, messages, tools=None, tool_choice="auto"):
        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        return {
            "content": choice.message.content or "",
            "tool_calls": [
                {
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                    "id": tc.id,
                }
                for tc in (choice.message.tool_calls or [])
            ],
            "finish_reason": choice.finish_reason,
        }

    def format_tools(self, registry_entries):
        return [
            {
                "type": "function",
                "function": {
                    "name": entry["name"],
                    "description": entry["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            arg: {"type": "string"} for arg in entry["args"]
                        },
                        "required": entry["args"],
                    },
                },
            }
            for entry in registry_entries
        ]
```

### OpenAI-compatible config

```json
{
  "providers": {
    "openai": {
      "api_key": "gsk_...",
      "model": "llama-3.1-70b-versatile",
      "base_url": "https://api.groq.com/openai/v1"
    }
  }
}
```

---

## Claude Provider

**File:** `dataviz/providers/claude_provider.py`

```python
class ClaudeProvider(BaseProvider):
    """Provider for Anthropic Claude models."""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def chat(self, messages, tools=None, tool_choice="auto"):
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            # Claude uses different tool_choice format
            if tool_choice == "required":
                kwargs["tool_choice"] = {"type": "any"}
            elif tool_choice == "auto":
                kwargs["tool_choice"] = {"type": "auto"}

        response = self.client.messages.create(**kwargs)

        tool_calls = []
        content_text = ""

        for block in response.content:
            if block.type == "text":
                content_text = block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "name": block.name,
                    "arguments": block.input,
                    "id": block.id,
                })

        return {
            "content": content_text,
            "tool_calls": tool_calls,
            "finish_reason": response.stop_reason,
        }

    def format_tools(self, registry_entries):
        return [
            {
                "name": entry["name"],
                "description": entry["description"],
                "input_schema": {
                    "type": "object",
                    "properties": {
                        arg: {"type": "string"} for arg in entry["args"]
                    },
                    "required": entry["args"],
                },
            }
            for entry in registry_entries
        ]
```

---

## Gemini Provider

**File:** `dataviz/providers/gemini_provider.py`

```python
class GeminiProvider(BaseProvider):
    """Provider for Google Gemini models."""

    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.genai = genai
        self.model_name = model

    def chat(self, messages, tools=None, tool_choice="auto"):
        model = self.genai.GenerativeModel(
            model_name=self.model_name,
            tools=tools or [],
        )
        # Convert OpenAI-style messages to Gemini format
        gemini_messages = self._convert_messages(messages)
        response = model.generate_content(gemini_messages)

        tool_calls = []
        content_text = ""

        for part in response.candidates[0].content.parts:
            if hasattr(part, "text"):
                content_text = part.text
            elif hasattr(part, "function_call"):
                tool_calls.append({
                    "name": part.function_call.name,
                    "arguments": dict(part.function_call.args),
                    "id": f"gemini_{part.function_call.name}",
                })

        return {
            "content": content_text,
            "tool_calls": tool_calls,
            "finish_reason": "tool_calls" if tool_calls else "stop",
        }

    def format_tools(self, registry_entries):
        # Gemini uses FunctionDeclaration format
        ...

    def _convert_messages(self, messages: list[dict]) -> list:
        """Convert OpenAI message format to Gemini Content format."""
        ...
```

---

## Provider Factory

**File:** `dataviz/providers/__init__.py`

```python
def get_provider(config: dict) -> BaseProvider:
    """Instantiate the correct provider from config.

    Args:
        config: Merged config dict with providers section.

    Returns:
        Instantiated provider ready for use.

    Raises:
        UnknownProviderError: If provider name is not supported.
    """
    name = config["default_provider"]
    cfg = config["providers"][name]

    if name == "openai":
        return OpenAIProvider(
            api_key=cfg["api_key"],
            model=cfg["model"],
            base_url=cfg.get("base_url"),
        )
    elif name == "claude":
        return ClaudeProvider(api_key=cfg["api_key"], model=cfg["model"])
    elif name == "gemini":
        return GeminiProvider(api_key=cfg["api_key"], model=cfg["model"])
    else:
        raise UnknownProviderError(f"Provider '{name}' is not supported.")
```

---

## Message Format Chuẩn (Internal)

Nội bộ, tất cả messages được lưu theo OpenAI format. Mỗi provider tự convert sang format riêng:

```python
# Standard internal format
messages = [
    {"role": "system", "content": "You are a data analysis agent..."},
    {"role": "user", "content": "Analyze this dataset schema: {...}"},
    {"role": "assistant", "content": None, "tool_calls": [
        {"name": "detect_schema", "arguments": {"df": "..."}, "id": "call_abc"}
    ]},
    {"role": "tool", "content": '{"columns": [...]}', "tool_call_id": "call_abc"},
]
```

---

## Error Handling

| Error | Xử lý |
|---|---|
| `AuthenticationError` | Log rõ provider + hint cách set lại key |
| `RateLimitError` | Exponential backoff, tối đa 3 lần |
| `APIConnectionError` | Retry 1 lần, sau đó raise với gợi ý kiểm tra mạng |
| `InvalidRequestError` | Log prompt bị lỗi, raise (không retry) |
| Model không hỗ trợ tool use | Raise `ProviderCapabilityError` rõ ràng |