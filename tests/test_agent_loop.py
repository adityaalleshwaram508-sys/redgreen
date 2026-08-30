"""End-to-end tests of the full agent loop, driven by the scripted model.

No API key, no network. These lock down the two behaviours that matter most:

  * with the reviewer on, an agent that first tries a special-case hack is caught in-band,
    recovers, and lands a genuinely verified fix;
  * with the reviewer off, that same hack slips past the in-band check and is caught by the
    held-out oracle — i.e. the oracle is a real backstop, not decoration.
"""
from pathlib import Path

from redgreen.agent.model import ScriptedModel
from redgreen.agent.solver import SolverConfig, solve
from redgreen.bench.loader import load_task
from redgreen.trace import Tracer
from redgreen.verify import gates
from redgreen.verify.metrics import grade_module_only

TASK_DIR = Path(__file__).resolve().parents[1] / "bench" / "tasks" / "merge_intervals_touching"


def _sources():
    repro = (TASK_DIR / "fixtures" / "repro_good.py").read_text()
    hack = (TASK_DIR / "fixtures" / "hack.py").read_text()
    return repro, hack


def test_reviewer_catches_hack_then_agent_recovers(tmp_path):
    task = load_task(TASK_DIR)
    repro, hack = _sources()
    model = ScriptedModel(reproduction=repro, fix=task.gold_module, hack=hack)
    tracer = Tracer(tmp_path / "agent.jsonl")

    solution = solve(task, model, tracer, SolverConfig(reviewer_enabled=True))

    assert solution.reproduced
    assert any(d.startswith("REQUEST_CHANGES") for d in solution.review_decisions), solution.review_decisions
    assert any(d.startswith("APPROVE") for d in solution.review_decisions), solution.review_decisions

    verdict = gates.classify(task, solution.patched_module, solution.reproduction)
    assert verdict.label == "VERIFIED_FIX", verdict


def test_oracle_backstops_when_reviewer_disabled(tmp_path):
    task = load_task(TASK_DIR)
    repro, hack = _sources()
    model = ScriptedModel(reproduction=repro, fix=task.gold_module, hack=hack)
    tracer = Tracer(tmp_path / "agent.jsonl")

    solution = solve(task, model, tracer, SolverConfig(reviewer_enabled=False))

    # Reviewer off, so the hacked patch survives the agent — the oracle must catch it.
    verdict = gates.classify(task, solution.patched_module, solution.reproduction)
    assert verdict.label == "REWARD_HACK", verdict


def test_trajectory_is_written(tmp_path):
    task = load_task(TASK_DIR)
    repro, hack = _sources()
    model = ScriptedModel(reproduction=repro, fix=task.gold_module, hack=hack)
    path = tmp_path / "trace.jsonl"
    solve(task, model, Tracer(path), SolverConfig())
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    assert lines, "trajectory file is empty"
    assert any('"event": "tool_call"' in ln for ln in lines)
    assert any('"event": "phase_start"' in ln for ln in lines)


def test_baseline_hack_is_not_a_verified_fix():
    """A plausible-but-wrong single-shot patch must not count as a fix."""
    task = load_task(TASK_DIR)
    _, hack = _sources()
    verdict = grade_module_only(task, hack)
    assert verdict.label in {"NOT_FIXED", "REWARD_HACK"}, verdict
    assert not verdict.is_fix
