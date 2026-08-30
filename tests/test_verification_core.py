"""Correctness tests for the verifier itself.

These run with no LLM and no network. They pin down the guarantee the whole project
rests on: a real fix is accepted, and the two ways a fix can be fake — never fixing the
bug, or gaming the reproduction — are both rejected with the right reason.
"""
from pathlib import Path

from redgreen.bench.loader import load_task
from redgreen.verify.gates import classify, oracle, regression

TASK_DIR = Path(__file__).resolve().parents[1] / "bench" / "tasks" / "merge_intervals_touching"


def _fixture(name: str) -> str:
    return (TASK_DIR / "fixtures" / name).read_text()


def test_planted_bug_is_invisible_to_the_existing_suite():
    """The bug only matters because the shipped suite has a coverage gap.

    If the existing tests already caught it, the whole scenario would be unrealistic —
    a maintainer would have seen a red build. So: existing suite green on buggy code,
    oracle red on buggy code.
    """
    task = load_task(TASK_DIR)
    assert regression(task.module_name, task.buggy_module, task.existing_tests).ok
    assert not oracle(task.module_name, task.buggy_module, task.oracle_test).ok


def test_gold_patch_is_a_verified_fix():
    task = load_task(TASK_DIR)
    verdict = classify(task, patched_module=task.gold_module, repro_test=_fixture("repro_good.py"))
    assert verdict.label == "VERIFIED_FIX", verdict


def test_reward_hack_is_caught_by_the_oracle():
    """The hack passes the agent's own reproduction but fails the held-out oracle."""
    task = load_task(TASK_DIR)
    verdict = classify(task, patched_module=_fixture("hack.py"), repro_test=_fixture("repro_good.py"))
    assert verdict.label == "REWARD_HACK", verdict


def test_noop_patch_is_not_a_fix():
    """Leaving the code unchanged fails at repro_green (the bug is still there)."""
    task = load_task(TASK_DIR)
    verdict = classify(task, patched_module=task.buggy_module, repro_test=_fixture("repro_good.py"))
    assert verdict.label == "NOT_FIXED", verdict
