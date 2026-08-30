"""The orchestrator: reproduce, then fix, then review — with hard gates between.

The three phases are separate on purpose. Each has its own instructions, its own scoped
tools, and a success criterion that must hold before the next phase may run:

    reproduce  --(the reproduction must FAIL on the buggy code)-->  fix
    fix        --(reproduction green AND existing suite green)-->    review
    review     --(no reward-hack signature)-->                       done

If the reviewer requests changes, the fix phase runs again with the critique in hand, up
to a small bounce limit. The held-out oracle is *not* consulted here — the agent never
sees it. The orchestrator returns the candidate (patched module + reproduction test); the
final graded verdict, including the oracle, is computed by the eval harness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..bench.loader import Task
from ..trace import Tracer
from ..tools.toolbox import RUN_TESTS, ToolBox
from ..verify import antihack, gates
from .model import Model, ModelResponse

_PROMPTS = Path(__file__).parent / "prompts"


@dataclass
class SolverConfig:
    max_steps_per_phase: int = 6
    reviewer_enabled: bool = True
    max_review_bounces: int = 1


@dataclass
class Solution:
    task_id: str
    reproduction: str | None
    patched_module: str
    reproduced: bool
    review_decisions: list[str] = field(default_factory=list)
    trajectory_path: Path | None = None


def solve(task: Task, model: Model, tracer: Tracer, config: SolverConfig | None = None) -> Solution:
    config = config or SolverConfig()

    # --- Phase 1: reproduce ---------------------------------------------------------
    repro_box = ToolBox(task, can_write_module=False, can_write_repro=True)
    tracer.phase_start("reproducer", "write a test that fails on the buggy code")
    _run_phase("reproducer", _prompt("reproducer"), _reproducer_kickoff(task), model, repro_box, tracer, config)

    reproduction = repro_box.reproduction
    ff = gates.fail_first(task.module_name, task.buggy_module, reproduction or "def test_noop():\n    assert True\n")
    tracer.gate("reproducer", ff)
    if not ff.ok:
        # No valid reproduction: stop here. The harness will grade this NOT_REPRODUCED.
        return Solution(task.id, reproduction, task.buggy_module, reproduced=False, trajectory_path=tracer.path)

    # --- Phase 2/3: fix, then review (with a bounce) --------------------------------
    fix_box = ToolBox(task, can_write_module=True, can_write_repro=False, reproduction=reproduction)
    review_decisions: list[str] = []
    critique = ""

    for attempt in range(config.max_review_bounces + 1):
        tracer.phase_start("fixer", f"attempt {attempt + 1}: make both suites green")
        _run_phase("fixer", _prompt("fixer"), _fixer_kickoff(task, critique), model, fix_box, tracer, config)

        if not config.reviewer_enabled:
            break

        decision, findings = _review(task, fix_box.module, model, tracer)
        review_decisions.append(decision)
        if decision.startswith("APPROVE"):
            break
        critique = f"A prior attempt was rejected by review. {decision}\nRewrite it as a genuine, general fix."

    return Solution(
        task.id,
        reproduction,
        fix_box.module,
        reproduced=True,
        review_decisions=review_decisions,
        trajectory_path=tracer.path,
    )


def _review(task: Task, patched: str, model: Model, tracer: Tracer) -> tuple[str, list]:
    tracer.phase_start("reviewer", "inspect the diff for reward-hacking")
    findings = antihack.scan_patch(task.buggy_module, patched)
    diff = antihack.unified_diff(task.buggy_module, patched, task.module_name)
    scan_block = (
        "SUSPICIOUS PATTERNS FOUND:\n" + "\n".join(f"- {f.rule}: {f.detail}" for f in findings)
        if findings
        else "Automated scan found no suspicious patterns."
    )
    user = f"Diff under review:\n\n{diff}\n\n{scan_block}"
    resp: ModelResponse = model.respond(_prompt("reviewer"), [{"role": "user", "content": user}], [])
    decision = resp.text.strip() or "APPROVE (no reviewer output)"
    tracer.review("reviewer", findings, decision)
    return decision, findings


def _run_phase(phase, system, kickoff, model: Model, box: ToolBox, tracer: Tracer, config: SolverConfig) -> None:
    messages: list[dict] = [{"role": "user", "content": kickoff}]
    for _ in range(config.max_steps_per_phase):
        resp = model.respond(system, messages, box.schemas())
        tracer.model_turn(phase, resp)

        assistant_content: list[dict] = []
        if resp.text:
            assistant_content.append({"type": "text", "text": resp.text})
        for call in resp.tool_calls:
            assistant_content.append({"type": "tool_use", "id": call.id, "name": call.name, "input": call.input})
        messages.append({"role": "assistant", "content": assistant_content})

        if not resp.wants_tools:
            return

        results: list[dict] = []
        for call in resp.tool_calls:
            output = box.dispatch(call.name, call.input)
            tracer.tool(phase, call.name, call.input, output)
            results.append({"type": "tool_result", "tool_use_id": call.id, "content": output})
        messages.append({"role": "user", "content": results})


def _prompt(name: str) -> str:
    return (_PROMPTS / f"{name}.md").read_text()


def _reproducer_kickoff(task: Task) -> str:
    return (
        f"Reproduce this bug as a failing pytest test. The module is imported as "
        f"`{task.module_name.removesuffix('.py')}`.\n\n"
        f"Start by calling {RUN_TESTS} or read_repo if you need the source.\n\n"
        f"{task.report}"
    )


def _fixer_kickoff(task: Task, critique: str) -> str:
    base = (
        "A reproduction test currently fails against the module. Fix the module so it "
        "passes while keeping the existing suite green. Call read_repo to see the current "
        "state, then edit and verify with run_tests(\"both\")."
    )
    return f"{critique}\n\n{base}" if critique else base
