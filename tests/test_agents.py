from __future__ import annotations

import json
import unittest
from typing import Any
from unittest.mock import MagicMock, call, patch

from dataviz.agents.base import (
    BaseAgent,
    AgentResult,
    LLMMaxTurnsError,
    PipelineContext,
)
from dataviz.providers.claude_provider import ClaudeProvider
from dataviz.providers.openai_provider import OpenAIProvider
from dataviz.providers.gemini_provider import GeminiProvider
from dataviz.tools.loader import ToolRegistry


# ---------------------------------------------------------------------------
# Minimal concrete agent so we can instantiate BaseAgent
# ---------------------------------------------------------------------------

class _DummyAgent(BaseAgent):
    def run(self, context: PipelineContext) -> AgentResult:
        return AgentResult()


# ---------------------------------------------------------------------------
# Fake tool registry that exposes one tool: echo_tool
# ---------------------------------------------------------------------------

def _make_registry() -> ToolRegistry:
    registry = ToolRegistry.__new__(ToolRegistry)
    registry._tools = {
        "echo_tool": lambda text="": f"echoed:{text}",
    }
    registry._registry = [
        {
            "name": "echo_tool",
            "description": "Echoes its input.",
            "agent": "report",
            "args": ["text"],
            "arg_types": {"text": "str"},
        }
    ]
    return registry


# ---------------------------------------------------------------------------
# Fake provider helper
# ---------------------------------------------------------------------------

def _make_provider(turn_responses: list[dict[str, Any]]) -> MagicMock:
    """Return a mock provider whose chat() cycles through turn_responses."""
    provider = MagicMock()
    provider.api_key = "sk-fake-key"
    provider.model = "fake-model"
    provider.chat = MagicMock(side_effect=turn_responses)
    provider.format_tools = MagicMock(return_value=[
        {
            "name": "echo_tool",
            "description": "Echoes its input.",
            "input_schema": {
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        }
    ])
    return provider


# ---------------------------------------------------------------------------
# AC-4: two-turn loop — tool call on turn 1, final answer on turn 2
# ---------------------------------------------------------------------------

class TestRunAgenticTwoTurn(unittest.TestCase):

    def setUp(self) -> None:
        self.registry = _make_registry()

    def test_tool_executed_and_result_fed_back(self) -> None:
        """run_agentic should call echo_tool and return the turn-2 text."""
        turn1 = {
            "content": "",
            "tool_calls": [{
                "type": "tool_use",
                "id": "call_001",
                "name": "echo_tool",
                "input": {"text": "hello"},
            }],
            "finish_reason": "tool_use",
        }
        turn2 = {
            "content": "Final answer after seeing echoed:hello",
            "tool_calls": [],
            "finish_reason": "end_turn",
        }
        provider = _make_provider([turn1, turn2])
        agent = _DummyAgent(tool_registry=self.registry, provider=provider)

        result = agent.run_agentic(
            initial_prompt="Please echo 'hello'.",
            system="You are a test agent.",
            agent_name="report",
            max_turns=6,
        )

        self.assertEqual(result, "Final answer after seeing echoed:hello")

        # Provider must have been called twice
        self.assertEqual(provider.chat.call_count, 2)

        # Second call's messages must include the tool result
        second_call_messages = provider.chat.call_args_list[1][0][0]
        tool_result_msgs = [m for m in second_call_messages if m.get("role") == "tool_result"]
        self.assertEqual(len(tool_result_msgs), 1)
        self.assertIn("echoed:hello", tool_result_msgs[0]["content"])

    def test_tool_call_id_propagated(self) -> None:
        """The tool_call_id from the model response should appear in the result message."""
        turn1 = {
            "content": "",
            "tool_calls": [{
                "type": "tool_use",
                "id": "toolu_xyz",
                "name": "echo_tool",
                "input": {"text": "world"},
            }],
            "finish_reason": "tool_use",
        }
        turn2 = {
            "content": "done",
            "tool_calls": [],
            "finish_reason": "end_turn",
        }
        provider = _make_provider([turn1, turn2])
        agent = _DummyAgent(tool_registry=self.registry, provider=provider)
        agent.run_agentic("prompt", "system", "report", max_turns=4)

        second_call_messages = provider.chat.call_args_list[1][0][0]
        tool_result = next(m for m in second_call_messages if m.get("role") == "tool_result")
        self.assertEqual(tool_result["tool_call_id"], "toolu_xyz")


# ---------------------------------------------------------------------------
# AC-5: max_turns exceeded raises LLMMaxTurnsError
# ---------------------------------------------------------------------------

class TestRunAgenticMaxTurns(unittest.TestCase):

    def setUp(self) -> None:
        self.registry = _make_registry()

    def _infinite_tool_response(self) -> dict[str, Any]:
        return {
            "content": "",
            "tool_calls": [{
                "type": "tool_use",
                "id": "call_inf",
                "name": "echo_tool",
                "input": {"text": "loop"},
            }],
            "finish_reason": "tool_use",
        }

    def test_raises_after_max_turns(self) -> None:
        """If the model always returns tool_calls, LLMMaxTurnsError must be raised."""
        provider = _make_provider([self._infinite_tool_response()] * 20)
        agent = _DummyAgent(tool_registry=self.registry, provider=provider)

        with self.assertRaises(LLMMaxTurnsError) as ctx:
            agent.run_agentic("loop forever", "system", "report", max_turns=3)

        self.assertEqual(ctx.exception.reason, "MAX_TURNS_EXCEEDED")
        # Provider was called exactly max_turns times
        self.assertEqual(provider.chat.call_count, 3)

    def test_max_turns_one_succeeds(self) -> None:
        """A single-turn conversation that returns immediately should not raise."""
        turn1 = {"content": "done", "tool_calls": [], "finish_reason": "end_turn"}
        provider = _make_provider([turn1])
        agent = _DummyAgent(tool_registry=self.registry, provider=provider)

        result = agent.run_agentic("quick", "system", "report", max_turns=1)
        self.assertEqual(result, "done")


# ---------------------------------------------------------------------------
# AC-6: providers raise RuntimeError when api_key is missing
# ---------------------------------------------------------------------------

class TestProviderRaisesOnMissingKey(unittest.TestCase):

    def test_claude_provider_raises_without_key(self) -> None:
        provider = ClaudeProvider(api_key="", model="claude-sonnet-4-6")
        with self.assertRaises(RuntimeError) as ctx:
            provider.chat([{"role": "user", "content": "hi"}])
        self.assertIn("api_key", str(ctx.exception).lower())

    def test_openai_provider_raises_without_key(self) -> None:
        provider = OpenAIProvider(api_key="", model="gpt-4o")
        with self.assertRaises(RuntimeError) as ctx:
            provider.chat([{"role": "user", "content": "hi"}])
        self.assertIn("api_key", str(ctx.exception).lower())

    def test_gemini_provider_raises_without_key(self) -> None:
        provider = GeminiProvider(api_key="", model="gemini-1.5-pro")
        with self.assertRaises(RuntimeError) as ctx:
            provider.chat([{"role": "user", "content": "hi"}])
        self.assertIn("api_key", str(ctx.exception).lower())


# ---------------------------------------------------------------------------
# Tool error is fed back to model rather than crashing the loop
# ---------------------------------------------------------------------------

class TestRunAgenticToolError(unittest.TestCase):

    def test_tool_exception_becomes_error_content(self) -> None:
        """When a tool raises, the error is serialised and fed to the model."""
        registry = _make_registry()
        registry._tools["echo_tool"] = lambda **_: (_ for _ in ()).throw(ValueError("boom"))

        turn1 = {
            "content": "",
            "tool_calls": [{"id": "c1", "name": "echo_tool", "input": {"text": "x"}}],
            "finish_reason": "tool_use",
        }
        turn2 = {"content": "handled error", "tool_calls": [], "finish_reason": "end_turn"}
        provider = _make_provider([turn1, turn2])
        agent = _DummyAgent(tool_registry=registry, provider=provider)

        result = agent.run_agentic("go", "sys", "report", max_turns=4)
        self.assertEqual(result, "handled error")

        # Error message must appear in the tool_result fed back to the model
        second_messages = provider.chat.call_args_list[1][0][0]
        tool_result = next(m for m in second_messages if m.get("role") == "tool_result")
        self.assertIn("error", tool_result["content"].lower())


if __name__ == "__main__":
    unittest.main()