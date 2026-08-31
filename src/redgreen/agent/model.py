from __future__ import annotations

import json
import os
import re
import time
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


def build_model(model_name: str | None = None) -> Model:
    """Return the real model for this run, chosen by REDGREEN_PROVIDER (default gemini)."""
    provider = os.environ.get("REDGREEN_PROVIDER", "gemini").lower()
    if provider == "anthropic":
        return AnthropicModel(model_name)
    if provider in ("gemini", "google"):
        return GeminiModel(model_name)
    raise ValueError(f"Unknown REDGREEN_PROVIDER {provider!r}; use 'gemini' or 'anthropic'.")


class AnthropicModel:
    def __init__(self, model: str | None = None, *, max_tokens: int = 4096, temperature: float = 0.0) -> None:
        self.model = model or os.environ.get("REDGREEN_MODEL", "claude-sonnet-4-5")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            from anthropic import Anthropic

            self._client = Anthropic()
        return self._client

    def respond(self, system: str, messages: list[dict], tools: list[dict]) -> ModelResponse:
        resp = self._client_lazy().messages.create(
            model=self.model, system=system, messages=messages, tools=tools,
            max_tokens=self.max_tokens,
        )
        text_parts: list[str] = []
        calls: list[ToolCall] = []
        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                calls.append(ToolCall(id=block.id, name=block.name, input=dict(block.input)))
        return ModelResponse(text="".join(text_parts), tool_calls=tuple(calls))


class GeminiModel:
    """Real model on Google's Gemini. Uses a small JSON protocol for tool use so the
    agent loop is unchanged, and paces + retries requests to survive free-tier limits.
    The google-genai SDK is imported lazily."""

    def __init__(self, model: str | None = None, *, max_output_tokens: int = 4096, temperature: float = 0.0) -> None:
        self.model = model or os.environ.get("REDGREEN_MODEL", "gemini-flash-latest")
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self.min_interval = float(os.environ.get("REDGREEN_MIN_INTERVAL", "13"))
        self.max_retries = int(os.environ.get("REDGREEN_MAX_RETRIES", "6"))
        self._client = None
        self._counter = 0
        self._last_call = 0.0

    def _client_lazy(self):
        if self._client is None:
            from google import genai

            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            self._client = genai.Client(api_key=api_key)
        return self._client

    def _next_id(self) -> str:
        self._counter += 1
        return f"tc_{self._counter}"

    def _pace(self) -> None:
        """Sleep so consecutive calls are at least min_interval seconds apart."""
        elapsed = time.time() - self._last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call = time.time()

    def _with_retry(self, call):
        """Retry with exponential backoff when the API reports a rate limit."""
        for attempt in range(self.max_retries):
            try:
                return call()
            except Exception as exc:
                text = str(exc).lower()
                is_rate_limit = "429" in text or "resource_exhausted" in text or "quota" in text
                if not is_rate_limit or attempt == self.max_retries - 1:
                    raise
                wait = self.min_interval * (2 ** attempt)
                print(f"  [rate-limited; waiting {wait:.0f}s and retrying]")
                time.sleep(wait)
        raise RuntimeError("unreachable")

    def respond(self, system: str, messages: list[dict], tools: list[dict]) -> ModelResponse:
        from google.genai import types

        system_full = system + _describe_tools(tools)
        transcript = _render_transcript(messages)

        def _call():
            self._pace()
            return self._client_lazy().models.generate_content(
                model=self.model,
                contents=transcript + "\n\nYour response:",
                config=types.GenerateContentConfig(
                    system_instruction=system_full,
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                ),
            )

        resp = self._with_retry(_call)
        try:
            text = resp.text or ""
        except Exception:
            text = ""

        if tools:
            call = _parse_tool_call(text)
            if call is not None:
                name, payload = call
                return ModelResponse(tool_calls=(ToolCall(self._next_id(), name, payload),))
        return ModelResponse(text=text)


def _describe_tools(tools: list[dict]) -> str:
    if not tools:
        return ""
    lines = ["", "You have these tools available:"]
    for tool in tools:
        schema = tool.get("input_schema", {})
        props = schema.get("properties", {})
        if props:
            bits = []
            for key, spec in props.items():
                if "enum" in spec:
                    bits.append(f'"{key}": one of {spec["enum"]}')
                else:
                    bits.append(f'"{key}": {spec.get("type", "string")}')
            args = "{" + ", ".join(bits) + "}"
        else:
            args = "{}  (no arguments)"
        lines.append(f'- {tool["name"]}: {tool.get("description", "").strip()}  Arguments: {args}')
    lines += [
        "",
        "To call a tool, reply with ONLY a single JSON object and nothing else, e.g.:",
        '{"tool": "run_tests", "input": {"which": "both"}}',
        "When a tool needs file content, put the ENTIRE file as a JSON string in that field.",
        "Do not wrap the JSON in markdown fences and do not add commentary around it.",
        "When finished and NOT calling a tool, reply with a short plain-text sentence (not JSON).",
    ]
    return "\n".join(lines)


def _render_transcript(messages: list[dict]) -> str:
    lines: list[str] = []
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if isinstance(content, str):
            speaker = "USER" if role == "user" else "ASSISTANT"
            lines.append(f"{speaker}: {content}")
        elif isinstance(content, list):
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    lines.append(f"ASSISTANT: {block.get('text', '')}")
                elif btype == "tool_use":
                    payload = json.dumps(block.get("input", {}))
                    lines.append(f'ASSISTANT (tool call): {{"tool": "{block.get("name")}", "input": {payload}}}')
                elif btype == "tool_result":
                    lines.append(f"TOOL RESULT:\n{block.get('content', '')}")
    return "\n".join(lines)


def _parse_tool_call(text: str):
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped[:4].lower() == "json":
            stripped = stripped[4:]
        stripped = stripped.strip()

    candidate = stripped
    if not candidate.startswith("{"):
        match = re.search(r"\{.*\}", stripped, re.DOTALL)
        if not match:
            return None
        candidate = match.group(0)

    try:
        obj = json.loads(candidate)
    except (ValueError, json.JSONDecodeError):
        return None

    if isinstance(obj, dict) and isinstance(obj.get("tool"), str):
        payload = obj.get("input", {})
        if isinstance(payload, dict):
            return obj["tool"], payload
    return None


@dataclass
class ScriptedModel:
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
