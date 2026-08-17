from __future__ import annotations

import inspect
import json
import logging
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from dataviz.tools.loader import ToolRegistry

log = logging.getLogger("dataviz")


def _fmt(v: Any, max_len: int = 120) -> str:
    s = repr(v)
    return s if len(s) <= max_len else s[:max_len] + "…"


class LLMError(RuntimeError):
    """Raised when a provider call fails or returns unusable content.

    Attributes:
        reason: Short machine-readable reason tag.
        detail: Full error detail for logging.
        finish_reason: stop_reason / finishReason from the API, if available.
    """
    def __init__(self, reason: str, detail: str, finish_reason: str = "") -> None:
        super().__init__(f"[{reason}] {detail}")
        self.reason = reason
        self.detail = detail
        self.finish_reason = finish_reason


class LLMEmptyResponseError(LLMError):
    """Provider returned a successful response but content was empty."""


class LLMAPIError(LLMError):
    """Provider HTTP / network call failed."""


class LLMMaxTurnsError(LLMError):
    """Agent loop did not converge within the allowed number of turns."""


@dataclass
class PipelineContext:
    file_paths: list[str]
    output_format: str
    mode: str = "default"
    focus: str | None = None
    lang: str = "auto"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    output: dict[str, Any] = field(default_factory=dict)
    context_updates: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):

    def __init__(
        self,
        tool_registry: ToolRegistry | None = None,
        provider: Any | None = None,
    ) -> None:
        self.tool_registry = tool_registry or ToolRegistry()
        self.provider = provider
        agent_name = type(self).__name__
        provider_label = (
            f"{type(provider).__name__}/{getattr(provider, 'model', '?')}"
            if provider else "none"
        )
        log.debug("[%s] __init__  provider=%s  registry_tools=%d",
                  agent_name, provider_label,
                  len(getattr(self.tool_registry, '_tools', {})))

    @abstractmethod
    def run(self, context: PipelineContext) -> AgentResult: ...

    def call_tool(self, tool_name: str, *args: Any, **kwargs: Any) -> Any:
        agent = type(self).__name__
        log.debug("[%s] call_tool → %s  kwargs=%s",
                  agent, tool_name, {k: _fmt(v) for k, v in kwargs.items()})
        t0 = time.monotonic()
        try:
            result = self.tool_registry.get(tool_name)(*args, **kwargs)
            elapsed = time.monotonic() - t0
            if hasattr(result, "shape"):
                result_repr = f"DataFrame{result.shape}"
            elif isinstance(result, (list, dict)):
                result_repr = f"{type(result).__name__}(len={len(result)})"
            else:
                result_repr = _fmt(result)
            log.debug("[%s] call_tool ← %s  %.3fs  result=%s",
                      agent, tool_name, elapsed, result_repr)
            return result
        except Exception as exc:
            elapsed = time.monotonic() - t0
            log.error("[%s] call_tool  %s  %.3fs  %s: %s\n%s",
                      agent, tool_name, elapsed,
                      type(exc).__name__, exc, traceback.format_exc())
            raise

    def ask_llm(self, prompt: str, system: str | None = None) -> str:
        """Call the LLM provider and return non-empty content.

        Raises:
            LLMEmptyResponseError: Provider responded but content is empty.
            LLMAPIError: Network or HTTP failure from the provider.
            RuntimeError: Provider not configured (no api_key).
        """
        agent = type(self).__name__

        if self.provider is None:
            # No provider at all — caller must not call ask_llm in this case.
            raise RuntimeError(
                f"[{agent}] ask_llm called but no provider is configured. "
                "Set a provider via 'dataviz config set --provider <name> --key <key>'."
            )

        provider_name = type(self.provider).__name__
        model         = getattr(self.provider, "model", "?")
        api_key       = getattr(self.provider, "api_key", "")
        api_key_preview = (api_key[:8] + "…") if api_key else "(empty)"

        if not api_key:
            raise RuntimeError(
                f"[{agent}] ask_llm: provider {provider_name} has no api_key set. "
                "Run 'dataviz config set --provider <name> --key <key>'."
            )

        log.debug("[%s] ask_llm  provider=%s  model=%s  api_key=%s  prompt_len=%d  system_len=%d",
                  agent, provider_name, model, api_key_preview,
                  len(prompt), len(system) if system else 0)
        log.debug("[%s] ask_llm  prompt_preview=%s", agent, _fmt(prompt, 300))

        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "user",      "content": f"[System] {system}"})
            messages.append({"role": "assistant",  "content": "Understood."})
        messages.append({"role": "user", "content": prompt})

        log.debug("[%s] ask_llm  → provider.chat()  messages=%d", agent, len(messages))
        t0 = time.monotonic()
        try:
            response = self.provider.chat(messages)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            log.error("[%s] ask_llm   provider.chat() raised  %.3fs  %s: %s\n%s",
                      agent, elapsed, type(exc).__name__, exc, traceback.format_exc())
            raise LLMAPIError(
                reason="API_EXCEPTION",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc

        elapsed   = time.monotonic() - t0
        content   = response.get("content", "")
        finish    = response.get("finish_reason", "?")
        n_tools   = len(response.get("tool_calls", []))

        log.debug("[%s] ask_llm  ← provider.chat()  %.3fs  finish=%s  content_len=%d  tool_calls=%d",
                  agent, elapsed, finish, len(content), n_tools)

        if not content:
            log.error("[%s] ask_llm   empty content  finish=%s  tool_calls=%d  full_response=%s",
                      agent, finish, n_tools, response)
            raise LLMEmptyResponseError(
                reason="EMPTY_CONTENT",
                detail=(
                    f"Provider {provider_name}/{model} returned empty content "
                    f"(finish_reason={finish!r}, tool_calls={n_tools}). "
                    "Possible causes: rate-limit, content filter, wrong model name, "
                    "or API quota exceeded."
                ),
                finish_reason=finish,
            )

        log.debug("[%s] ask_llm  content_preview=%s", agent, _fmt(content, 300))
        return content

    def ask_llm_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        """Call the LLM provider with a tool list and return the full response.

        Unlike ``ask_llm``, this method returns the raw normalised response dict
        (``content``, ``tool_calls``, ``finish_reason``) so the caller can inspect
        and dispatch tool calls.  It does NOT raise on empty content — a turn where
        the model only emits tool calls (no text) is valid.

        Args:
            messages:    Full conversation history in provider-agnostic format.
            tools:       Provider-formatted tool schemas (from ``provider.format_tools``).
            tool_choice: ``"auto"`` | ``"any"`` | ``"none"``.

        Returns:
            Dict with keys ``content`` (str), ``tool_calls`` (list), ``finish_reason`` (str).

        Raises:
            LLMAPIError:  Network or HTTP failure from the provider.
            RuntimeError: Provider not configured or missing api_key.
        """
        agent = type(self).__name__

        if self.provider is None:
            raise RuntimeError(
                f"[{agent}] ask_llm_with_tools called but no provider is configured."
            )

        api_key = getattr(self.provider, "api_key", "")
        if not api_key:
            provider_name = type(self.provider).__name__
            raise RuntimeError(
                f"[{agent}] ask_llm_with_tools: provider {provider_name} has no api_key set."
            )

        provider_name = type(self.provider).__name__
        model = getattr(self.provider, "model", "?")
        log.debug(
            "[%s] ask_llm_with_tools  provider=%s  model=%s  messages=%d  tools=%d  tool_choice=%s",
            agent, provider_name, model, len(messages), len(tools), tool_choice,
        )

        t0 = time.monotonic()
        try:
            response = self.provider.chat(messages, tools=tools, tool_choice=tool_choice)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            log.error(
                "[%s] ask_llm_with_tools provider.chat() raised  %.3fs  %s: %s\n%s",
                agent, elapsed, type(exc).__name__, exc, traceback.format_exc(),
            )
            raise LLMAPIError(
                reason="API_EXCEPTION",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc

        elapsed = time.monotonic() - t0
        content = response.get("content", "")
        tool_calls = response.get("tool_calls", [])
        finish = response.get("finish_reason", "?")

        log.debug(
            "[%s] ask_llm_with_tools  ← %.3fs  finish=%s  content_len=%d  tool_calls=%d",
            agent, elapsed, finish, len(content), len(tool_calls),
        )
        return response

    def run_agentic(
        self,
        initial_prompt: str,
        system: str,
        agent_name: str,
        max_turns: int = 6,
        context_data: dict[str, Any] | None = None,
        trace_sink: list[dict[str, Any]] | None = None,
    ) -> str:
        """Run a real LLM-driven agent loop for the given agent.

        The loop works as follows:
        1. Load the tool list for ``agent_name`` from the registry.
        2. Format tools for the current provider.
        3. Send the initial prompt to the LLM together with the tool schemas.
        4. If the model requests tool calls, execute each via ``call_tool`` and
           append results to the conversation.
        5. Repeat until the model returns a final answer (no tool calls) or
           ``max_turns`` is exceeded.

        Each provider normalises tool-result messages differently.  This method
        uses the provider-agnostic shape ``{"role": "tool_result", ...}`` and
        relies on each provider's ``chat()`` to translate it to the wire format.
        (Currently only ``ClaudeProvider`` is fully wired; extend the others as
        needed.)

        Args:
            initial_prompt: User-side prompt describing the task.
            system:         System instruction for the model.
            agent_name:     Registry agent name (e.g. ``"report"``).
            max_turns:      Hard cap on LLM turns before raising.
            trace_sink:     If provided, each dispatched tool call is appended
                             to this list as ``{"tool": name, "input": args}``
                             (LLM-supplied args only, not injected context
                             objects like ``df``). Lets callers reconstruct
                             what the agent actually did -- e.g. so exporters
                             can render real code cells instead of narrative
                             text.

        Returns:
            The model's final text response.

        Raises:
            LLMMaxTurnsError: Loop did not converge within ``max_turns``.
            LLMAPIError:      Provider call failed.
            RuntimeError:     No provider / missing api_key or tool failure.
        """
        agent = type(self).__name__
        _ctx = context_data or {}

        # -- Build tool list from registry ------------------------------------
        tool_entries = self.tool_registry.list_for_agent(agent_name)
        tools = self.provider.format_tools(tool_entries)
        log.debug(
            "[%s] run_agentic  agent_name=%s  tools=%d  max_turns=%d",
            agent, agent_name, len(tools), max_turns,
        )

        # -- Seed conversation ------------------------------------------------
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "user", "content": f"[System] {system}"})
            messages.append({"role": "assistant", "content": "Understood."})
        messages.append({"role": "user", "content": initial_prompt})

        # -- Agent loop -------------------------------------------------------
        for turn in range(1, max_turns + 1):
            log.debug("[%s] run_agentic  turn=%d/%d  messages=%d", agent, turn, max_turns, len(messages))

            response = self.ask_llm_with_tools(messages, tools=tools, tool_choice="auto")
            content = response.get("content", "")
            tool_calls = response.get("tool_calls", [])
            finish = response.get("finish_reason", "?")

            # Append assistant turn to history.
            # Also stash raw_parts from Gemini responses so the provider can
            # replay them verbatim (needed for thought_signature continuity).
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            raw_parts = response.get("_raw_parts")
            if raw_parts is not None:
                assistant_msg["_raw_parts"] = raw_parts
            messages.append(assistant_msg)

            if not tool_calls:
                # Model produced a final answer — return it.
                log.debug(
                    "[%s] run_agentic final answer  turn=%d  finish=%s  content_len=%d",
                    agent, turn, finish, len(content),
                )
                if not content:
                    raise LLMEmptyResponseError(
                        reason="EMPTY_CONTENT",
                        detail=(
                            f"[{agent}] run_agentic: model returned no tool calls and "
                            f"no content on turn {turn} (finish_reason={finish!r})."
                        ),
                        finish_reason=finish,
                    )
                return content

            # Execute each requested tool call and feed results back.
            log.debug("[%s] run_agentic  dispatching %d tool call(s)", agent, len(tool_calls))
            for call in tool_calls:
                tool_name = call.get("name", "")
                tool_input = call.get("input", {})
                call_id = call.get("id", "")

                log.debug(
                    "[%s] run_agentic  → tool=%s  id=%s  input=%s",
                    agent, tool_name, call_id, _fmt(tool_input),
                )

                if trace_sink is not None:
                    trace_sink.append({"tool": tool_name, "input": dict(tool_input)})

                # Inject non-serializable context objects (e.g. DataFrames).
                # The LLM cannot pass these -- agent supplies them transparently.
                # Only inject context keys that the tool function actually accepts,
                # so tools with different signatures don't receive unexpected kwargs.
                _tool_fn = self.tool_registry.get(tool_name)
                _tool_params = inspect.signature(_tool_fn).parameters
                _accepts_var_keyword = any(
                    p.kind == inspect.Parameter.VAR_KEYWORD
                    for p in _tool_params.values()
                )
                if _accepts_var_keyword:
                    _filtered_ctx = _ctx
                else:
                    _filtered_ctx = {k: v for k, v in _ctx.items() if k in _tool_params}
                merged_input = {**_filtered_ctx, **tool_input}

                try:
                    result = self.call_tool(tool_name, **merged_input)
                    # Serialise to string so it fits cleanly in the message content.
                    if isinstance(result, (dict, list)):
                        result_content = json.dumps(result, default=str)
                    else:
                        result_content = str(result)
                except Exception as exc:
                    log.error(
                        "[%s] run_agentic  tool %s failed -- aborting: %s",
                        agent, tool_name, exc,
                    )
                    raise RuntimeError(
                        f"[{agent}] Tool '{tool_name}' failed: {type(exc).__name__}: {exc}"
                    ) from exc

                log.debug(
                    "[%s] run_agentic  ← tool=%s  result_len=%d",
                    agent, tool_name, len(result_content),
                )

                # Provider-agnostic tool-result shape.
                # ClaudeProvider.chat() translates this to the Anthropic wire format.
                messages.append({
                    "role": "tool_result",
                    "tool_call_id": call_id,
                    "tool_name": tool_name,
                    "content": result_content,
                })

        # -- Max turns exceeded -----------------------------------------------
        log.error(
            "[%s] run_agentic did not converge in %d turns — aborting.",
            agent, max_turns,
        )
        raise LLMMaxTurnsError(
            reason="MAX_TURNS_EXCEEDED",
            detail=(
                f"[{agent}] run_agentic for agent_name={agent_name!r} did not produce "
                f"a final answer within {max_turns} turns."
            ),
        )