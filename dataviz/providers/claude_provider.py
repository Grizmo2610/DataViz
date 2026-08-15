from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from .base import BaseProvider

logger = logging.getLogger(__name__)

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"

# Map Python type names to JSON Schema types
_PYTHON_TO_JSON_TYPE: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "Any": "string",  # fall back to string for untyped args
}


class ClaudeProvider(BaseProvider):
    """Provider that calls the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize the provider.

        Args:
            api_key: Anthropic API key (``sk-ant-...``).
            model: Claude model identifier (e.g. ``claude-sonnet-4-6``).
        """

        super().__init__(api_key, model)

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send a chat request to the Anthropic Messages API.

        Args:
            messages: Conversation history in Anthropic format.
            tools: Optional list of tool definitions (Claude input_schema format).
            tool_choice: ``"auto"``, ``"any"``, or ``"none"``.

        Returns:
            Normalised response dict with keys:
            - ``content`` (str): First text block from the response, or ``""``.
            - ``tool_calls`` (list): Any ``tool_use`` blocks from the response.
            - ``finish_reason`` (str): Stop reason from the API.

        Raises:
            RuntimeError: On non-2xx HTTP responses or JSON parse failures.
        """

        if not self.api_key:
            raise RuntimeError(
                "ClaudeProvider: no api_key configured. "
                "Run: dataviz config set --provider claude --key <your_key>"
            )

        # Translate provider-agnostic tool_result messages to Anthropic wire format.
        # BaseAgent.run_agentic emits {"role": "tool_result", "tool_call_id": ...,
        # "tool_name": ..., "content": ...}.  Anthropic expects tool results as a
        # user turn containing a content block of type "tool_result".
        wire_messages: list[dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "tool_result":
                wire_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": msg["content"],
                    }],
                })
            elif msg.get("role") == "assistant" and msg.get("tool_calls"):
                # Assistant turn that contains tool_use blocks -- reconstruct the
                # content list so the API sees both text and tool_use blocks.
                content_blocks: list[dict[str, Any]] = []
                if msg.get("content"):
                    content_blocks.append({"type": "text", "text": msg["content"]})
                for call in msg["tool_calls"]:
                    content_blocks.append(call)  # already in tool_use block shape
                wire_messages.append({"role": "assistant", "content": content_blocks})
            else:
                wire_messages.append(msg)

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": wire_messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = {"type": tool_choice}

        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            _ANTHROPIC_API_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": _ANTHROPIC_VERSION,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode(errors="replace")
            raise RuntimeError(
                f"Anthropic API error {exc.code}: {error_body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Network error reaching Anthropic API: {exc.reason}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Anthropic API returned invalid JSON: {raw[:200]}") from exc

        content_blocks: list[dict[str, Any]] = data.get("content", [])
        text_content = " ".join(
            block["text"] for block in content_blocks if block.get("type") == "text"
        )
        tool_calls = [
            block for block in content_blocks if block.get("type") == "tool_use"
        ]

        logger.debug(
            "ClaudeProvider.chat: model=%s stop_reason=%s text_len=%d tool_calls=%d",
            self.model,
            data.get("stop_reason"),
            len(text_content),
            len(tool_calls),
        )

        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "finish_reason": data.get("stop_reason", "stop"),
        }

    def format_tools(self, registry_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert tool registry entries to Anthropic tool definitions.

        Each entry is expected to have:
        - ``name`` (str)
        - ``description`` (str)
        - ``args`` (list[str]) -- positional arg names
        - ``arg_types`` (dict[str, str], optional) -- maps arg name -> Python type name

        Args:
            registry_entries: Tool registry entries.

        Returns:
            List of Anthropic-format tool dicts with ``input_schema``.
        """

        formatted: list[dict[str, Any]] = []
        for entry in registry_entries:
            arg_types: dict[str, str] = entry.get("arg_types", {})
            arg_item_types: dict[str, str] = entry.get("arg_item_types", {})
            # Skip Any-typed args -- they are injected via context_data,
            # not supplied by the LLM.
            exposed_args = [
                arg for arg in entry["args"]
                if arg_types.get(arg, "Any") != "Any"
            ]
            properties: dict[str, Any] = {}
            for arg in exposed_args:
                python_type = arg_types.get(arg, "str")
                json_type = _PYTHON_TO_JSON_TYPE.get(python_type, "string")
                prop: dict[str, Any] = {"type": json_type}
                if json_type == "array":
                    item_python_type = arg_item_types.get(arg, "object")
                    item_json_type = _PYTHON_TO_JSON_TYPE.get(item_python_type, "object") \
                        if item_python_type != "object" else "object"
                    prop["items"] = {"type": item_json_type}
                properties[arg] = prop

            formatted.append(
                {
                    "name": entry["name"],
                    "description": entry["description"],
                    "input_schema": {
                        "type": "object",
                        "properties": properties,
                        "required": exposed_args,
                    },
                }
            )
        return formatted