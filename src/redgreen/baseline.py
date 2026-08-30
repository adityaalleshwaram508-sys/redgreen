"""The baseline the agent is measured against.

A fair, competent baseline — not a strawman. It is how a capable engineer uses an LLM
today without wiring up a verification loop: it sees the same bug report, module, and
pre-existing tests as the agent, and gets one shot — read the problem, return the whole
fixed module. No test execution, no reproduction test, no self-correction.

The gap between this and the agent is exactly the value of the *methodology*, because the
model, the task, and the grading are all held constant. The baseline writes no
reproduction test, so when the harness scores it, it supplies a canonical reproduction
derived from the task — the baseline is judged on whether it actually fixed the bug
(oracle + regression), which is all it was asked to do.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .agent.model import Model
from .bench.loader import Task
from .trace import Tracer

_PROMPT = Path(__file__).parent / "agent" / "prompts" / "baseline.md"


@dataclass
class BaselineResult:
    task_id: str
    patched_module: str


def run_baseline(task: Task, model: Model, tracer: Tracer) -> BaselineResult:
    tracer.phase_start("baseline", "single-shot patch, no verification loop")
    existing = "\n\n".join(f"# {name}\n{src}" for name, src in task.existing_tests.items())
    user = (
        f"# Bug report\n{task.report}\n\n"
        f"# Module: {task.module_name}\n{task.buggy_module}\n\n"
        f"# Existing tests\n{existing}\n\n"
        f"Return the complete corrected `{task.module_name}`."
    )
    resp = model.respond(_PROMPT.read_text(), [{"role": "user", "content": user}], [])
    tracer.model_turn("baseline", resp)
    patched = _strip_fences(resp.text) or task.buggy_module
    return BaselineResult(task.id, patched)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]  # drop opening fence (possibly ```python)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip() + "\n" if text.strip() else ""
