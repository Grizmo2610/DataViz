from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from .base import BaseProvider

logger = logging.getLogger(__name__)

_OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

_PYTHON_TO_JSON_TYPE: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "Any": "string",
}


class OpenAIProvider(BaseProvider):
    """Provider that calls the OpenAI Chat Completions API.

    Also compatible with any OpenAI-compatible endpoint (Ollama, Azure, etc.)
    by passing a custom ``base_url``.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
    ) -> None:
        super().__init__(api_key, model)
        # Allow overriding the endpoint (Ollama, Azure, LM Studio, ...)
        self._url = (base_url.rstrip("/") + "/chat/completions") if base_url else _OPENAI_API_URL

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send a request to the OpenAI Chat Completions API.

        Args:
            messages: Conversation history in OpenAI format.
            tools: Optional list of function definitions.
            tool_choice: ``"auto"``, ``"none"``, or a specific function name dict.

        Returns:
            Normalised response dict with keys ``content``, ``tool_calls``,
            ``finish_reason``.

        Raises:
            RuntimeError: On non-2xx HTTP responses.
        """
        if not self.api_key:
            raise RuntimeError(
                "OpenAIProvider: no api_key configured. "
                "Run: dataviz config set --provider openai --key <your_key>"
            )

        # Translate provider-agnostic tool_result messages to OpenAI wire format.
        # BaseAgent.run_agentic emits {"role": "tool_result", "tool_call_id": ...,
        # "tool_name": ..., "content": ...}.  OpenAI expects role="tool".
        wire_messages: list[dict[str, Any]] = []
        for msg in messages:
            if msg.get("role") == "tool_result":
                wire_messages.append({
                    "role": "tool",
                    "tool_call_id": msg["tool_call_id"],
                    "content": msg["content"],
                })
            elif msg.get("role") == "assistant" and msg.get("tool_calls"):
                # Reconstruct the OpenAI assistant message with tool_calls list.
                oai_calls = []
                for call in msg["tool_calls"]:
                    oai_calls.append({
                        "id": call.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": call.get("name", ""),
                            "arguments": json.dumps(call.get("input", {})),
                        },
                    })
                wire_messages.append({
                    "role": "assistant",
                    "content": msg.get("content") or None,
                    "tool_calls": oai_calls,
                })
            else:
                wire_messages.append(msg)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": wire_messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            self._url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode(errors="replace")
            raise RuntimeError(f"OpenAI API error {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Network error reaching OpenAI API: {exc.reason}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenAI API returned invalid JSON: {raw[:200]}") from exc

        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message", {})

        text_content = message.get("content") or ""
        # tool_calls is a list of {id, type, function: {name, arguments}}
        raw_tool_calls = message.get("tool_calls") or []
        tool_calls = [
            {
                "id":   tc.get("id"),
                "name": tc["function"]["name"],
                "input": json.loads(tc["function"].get("arguments", "{}")),
            }
            for tc in raw_tool_calls
            if tc.get("function")
        ]

        logger.debug(
            "OpenAIProvider.chat: model=%s finish=%s text_len=%d tool_calls=%d",
            self.model,
            choice.get("finish_reason"),
            len(text_content),
            len(tool_calls),
        )

        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "finish_reason": choice.get("finish_reason", "stop"),
        }

    def format_tools(self, registry_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert tool registry entries to OpenAI function definitions.

        Args:
            registry_entries: Tool registry entries.

        Returns:
            List of OpenAI-format tool dicts.
        """
        formatted: list[dict[str, Any]] = []
        for entry in registry_entries:
            arg_types: dict[str, str] = entry.get("arg_types", {})
            arg_item_types: dict[str, str] = entry.get("arg_item_types", {})
            # Skip Any-typed args -- injected via context_data, not from LLM.
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
            formatted.append({
                "type": "function",
                "function": {
                    "name": entry["name"],
                    "description": entry["description"],
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": exposed_args,
                    },
                },
            })
        return formatted