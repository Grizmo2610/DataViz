from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from .base import BaseProvider

logger = logging.getLogger(__name__)

# Gemini uses a different URL shape: /v1beta/models/{model}:generateContent
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_PYTHON_TO_JSON_TYPE: dict[str, str] = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
    "Any": "string",
}

# Map OpenAI-style role names -> Gemini role names
_ROLE_MAP = {"user": "user", "assistant": "model", "system": "user"}


class GeminiProvider(BaseProvider):
    """Provider that calls the Google Gemini generateContent API."""

    def __init__(self, api_key: str, model: str) -> None:
        super().__init__(api_key, model)

    def _url(self) -> str:
        return f"{_GEMINI_API_BASE}/{self.model}:generateContent?key={self.api_key}"

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Send a request to the Gemini generateContent API.

        Gemini uses a different message format than OpenAI/Anthropic:
        - roles are ``"user"`` / ``"model"`` (not ``"assistant"``)
        - system messages are prepended as user turns
        - content is ``[{"text": "..."}]`` not a plain string

        Args:
            messages: Conversation history (OpenAI-style, converted internally).
            tools: Optional function declarations.
            tool_choice: Ignored for Gemini (always auto).

        Returns:
            Normalised response dict with keys ``content``, ``tool_calls``,
            ``finish_reason``.

        Raises:
            RuntimeError: On non-2xx HTTP responses.
        """
        if not self.api_key:
            raise RuntimeError(
                "GeminiProvider: no api_key configured. "
                "Run: dataviz config set --provider gemini --key <your_key>"
            )

        # Convert provider-agnostic messages -> Gemini contents.
        # Handles tool_result turns (functionResponse) and assistant turns with
        # tool_calls (functionCall parts).
        contents: list[dict[str, Any]] = []
        for msg in messages:
            role = msg.get("role", "user")

            if role == "tool_result":
                # Gemini expects functionResponse as a user-role part.
                part = {
                    "functionResponse": {
                        "name": msg.get("tool_name", ""),
                        "response": {"content": msg["content"]},
                    }
                }
                if contents and contents[-1]["role"] == "user":
                    contents[-1]["parts"].append(part)
                else:
                    contents.append({"role": "user", "parts": [part]})
                continue

            if role == "assistant" and msg.get("tool_calls"):
                # Replay the model turn verbatim using raw parts when available.
                # Gemini thinking models embed a thought_signature in functionCall
                # parts; if we reconstruct from scratch the signature is lost and
                # the API returns 400 INVALID_ARGUMENT.
                raw_parts = msg.get("_raw_parts")
                if raw_parts is not None:
                    contents.append({"role": "model", "parts": raw_parts})
                else:
                    rebuilt: list[dict[str, Any]] = []
                    if msg.get("content"):
                        rebuilt.append({"text": msg["content"]})
                    for call in msg["tool_calls"]:
                        raw_part = call.get("_raw_part")
                        if raw_part is not None:
                            rebuilt.append(raw_part)
                        else:
                            rebuilt.append({
                                "functionCall": {
                                    "name": call.get("name", ""),
                                    "args": call.get("input", {}),
                                }
                            })
                    contents.append({"role": "model", "parts": rebuilt})
                continue

            gemini_role = _ROLE_MAP.get(role, "user")
            text = msg.get("content", "")
            # Gemini requires alternating user/model turns; merge same-role
            # consecutive messages into one part.
            if contents and contents[-1]["role"] == gemini_role:
                contents[-1]["parts"].append({"text": text})
            else:
                contents.append({"role": gemini_role, "parts": [{"text": text}]})

        payload: dict[str, Any] = {"contents": contents}

        if tools:
            payload["tools"] = [{"function_declarations": tools}]

        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            self._url(),
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode()
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode(errors="replace")
            raise RuntimeError(f"Gemini API error {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Network error reaching Gemini API: {exc.reason}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Gemini API returned invalid JSON: {raw[:200]}") from exc

        # Extract text and function calls from the response
        candidate = (data.get("candidates") or [{}])[0]
        parts = candidate.get("content", {}).get("parts") or []

        text_parts = [p["text"] for p in parts if "text" in p]
        text_content = " ".join(text_parts)

        tool_calls = [
            {
                "name":   p["functionCall"]["name"],
                "input":  p["functionCall"].get("args", {}),
                # Preserve the raw part so we can replay it verbatim in
                # the model turn -- Gemini thinking models require the
                # thought_signature to be present in the history.
                "_raw_part": p,
            }
            for p in parts
            if "functionCall" in p
        ]

        finish = candidate.get("finishReason", "STOP").lower()

        logger.debug(
            "GeminiProvider.chat: model=%s finish=%s text_len=%d tool_calls=%d",
            self.model, finish, len(text_content), len(tool_calls),
        )

        return {
            "content":    text_content,
            "tool_calls": tool_calls,
            "finish_reason": finish,
            # Raw parts from the model turn -- used by run_agentic to preserve
            # thought_signature when replaying Gemini thinking-model history.
            "_raw_parts": parts,
        }

    def format_tools(self, registry_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert tool registry entries to Gemini function declarations.

        Args:
            registry_entries: Tool registry entries.

        Returns:
            List of Gemini-format function declaration dicts.
        """
        formatted: list[dict[str, Any]] = []
        for entry in registry_entries:
            arg_types: dict[str, str] = entry.get("arg_types", {})
            arg_item_types: dict[str, str] = entry.get("arg_item_types", {})

            # Args injected via context_data (e.g. df) are not exposed to the
            # LLM -- skip them so the schema only contains what the model can
            # actually supply.  'Any' typed args are always injected objects.
            exposed_args = [
                arg for arg in entry["args"]
                if arg_types.get(arg, "Any") != "Any"
            ]

            properties: dict[str, Any] = {}
            for arg in exposed_args:
                python_type = arg_types.get(arg, "str")
                json_type = _PYTHON_TO_JSON_TYPE.get(python_type, "string")
                prop: dict[str, Any] = {"type": json_type}
                # Gemini requires 'items' on array-typed parameters.
                if json_type == "array":
                    item_python_type = arg_item_types.get(arg, "object")
                    item_json_type = _PYTHON_TO_JSON_TYPE.get(item_python_type, "object") \
                        if item_python_type != "object" else "object"
                    prop["items"] = {"type": item_json_type}
                properties[arg] = prop

            formatted.append({
                "name": entry["name"],
                "description": entry["description"],
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": exposed_args,
                },
            })
        return formatted