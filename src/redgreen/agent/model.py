"""The model boundary.

The agent talks to a ``Model`` through one method, ``respond``. Two implementations sit
behind it: ``AnthropicModel`` for real runs, and ``ScriptedModel`` — a deterministic
stand-in that lets the entire agent loop be unit-tested with no API key and no network.
Keeping this boundary narrow is what makes the orchestration testable; everything above
it is provably exercised in CI.

The message and tool shapes mirror the Anthropic Messages API tool-use protocol, so the
real and fake paths run through the identical loop in ``agent.solver``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass(frozen=True)
class ModelResponse:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


@runtime_checkable
class Model(Protocol):
    def respond(self, system: str, messages: list[dict], tools: list[dict]) -> ModelResponse:
        ...


class AnthropicModel:
    """Real model. The ``anthropic`` SDK is imported lazily so the package stays
    importable (and testable) in environments without it or without a key.
    """

    def __init__(
        self,
        model: str | None = None,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> None:
        # Never hardcode a model into the logic — read it from the environment so a run
        # is pinned by config, and document the knob in REPRODUCTION.md.
        self.model = model or os.environ.get("REDGREEN_MODEL", "claude-sonnet-4-5")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            from anthropic import Anthropic  # imported here on purpose

            self._client = Anthropic()
        return self._client

    def respond(self, system: str, messages: list[dict], tools: list[dict]) -> ModelResponse:
        resp = self._client_lazy().messages.create(
            model=self.model,
            system=system,
            messages=messages,
            tools=tools,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        text_parts: list[str] = []
        calls: list[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name, input=dict(block.input)))
        return ModelResponse(text="".join(text_parts), tool_calls=tuple(calls))


@dataclass
class ScriptedModel:
    """A deterministic model for tests and for the fake-model smoke run.

    Rather than replaying a brittle fixed transcript, it conditions on the conversation
    so far (exactly like a real model would) and applies a small, legible policy per
    phase. That makes it robust to incidental changes in the loop while still being
    fully deterministic.

    Parameters let a single instance play different characters:
      * ``reproduction`` — the test it writes in the Reproducer phase.
      * ``fix`` — the patch it writes once it decides to fix properly.
      * ``hack`` — an optional first-attempt patch that games the reproduction; if set,
        the model tries it before falling back to ``fix`` after a reviewer push-back.
    """

    reproduction: str
    fix: str
    hack: str | None = None
    baseline_output: str | None = None
    _counter: int = field(default=0, init=False)

    def _next_id(self) -> str:
        self._counter += 1
        return f"tc_{self._counter}"

    def respond(self, system: str, messages: list[dict], tools: list[dict]) -> ModelResponse:
        phase = _phase_of(system)
        used = _tool_names_used(messages)

        if phase == "baseline":
            # The baseline returns the whole corrected module as plain text.
            return ModelResponse(text=self.baseline_output if self.baseline_output is not None else self.fix)

        if phase == "reproducer":
            if "write_reproduction_test" not in used:
                return self._call("write_reproduction_test", {"content": self.reproduction})
            if "run_tests" not in used:
                return self._call("run_tests", {"which": "reproduction"})
            return ModelResponse(text="Reproduction fails on the current code as expected.")

        if phase == "fixer":
            if "write_module" not in used:
                patch = self.fix
                if self.hack is not None and not _reviewer_pushed_back(messages):
                    patch = self.hack
                return self._call("write_module", {"content": patch})
            if "run_tests" not in used:
                return self._call("run_tests", {"which": "both"})
            return ModelResponse(text="Reproduction passes and the existing suite is green.")

        # reviewer phase: no tools, just a verdict. The phase feeds the static scan into
        # the prompt; the fake mirrors a competent reviewer by trusting a non-empty scan.
        if _scan_flagged(messages):
            return ModelResponse(text="REQUEST_CHANGES the patch special-cases the test inputs")
        return ModelResponse(text="APPROVE the change addresses the root cause and generalises")

    def _call(self, name: str, payload: dict) -> ModelResponse:
        return ModelResponse(tool_calls=(ToolCall(self._next_id(), name, payload),))


def _phase_of(system: str) -> str:
    head = system.strip().splitlines()[0].lower() if system.strip() else ""
    if "baseline" in head:
        return "baseline"
    if "reproducer" in head:
        return "reproducer"
    if "fixer" in head:
        return "fixer"
    return "reviewer"


def _tool_names_used(messages: list[dict]) -> set[str]:
    names: set[str] = set()
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    names.add(block.get("name", ""))
    return names


def _reviewer_pushed_back(messages: list[dict]) -> bool:
    first = messages[0].get("content", "") if messages else ""
    return isinstance(first, str) and "REQUEST_CHANGES" in first


def _scan_flagged(messages: list[dict]) -> bool:
    first = messages[0].get("content", "") if messages else ""
    return isinstance(first, str) and "SUSPICIOUS PATTERNS FOUND" in first
