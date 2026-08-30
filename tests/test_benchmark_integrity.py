"""Every benchmark task must satisfy the same invariants, or the whole eval is invalid.

For a task to be a fair test of a bug fixer, three things must hold:

  1. the pre-existing suite passes on the buggy code — the bug is a real coverage gap a
     maintainer could plausibly have shipped, not an already-red build;
  2. the held-out oracle fails on the buggy code — it actually exercises the bug;
  3. the gold reference fix turns both green — the bug is fixable and the oracle is
     satisfiable.

This parametrised test asserts all three for each task, so a mistake in authoring a task
shows up here rather than silently skewing the results.
"""
import pytest

from redgreen.bench.loader import load_all, load_task
from redgreen.verify import gates
from redgreen.paths import TASKS_DIR

TASKS = load_all(TASKS_DIR)
IDS = [t.id for t in TASKS]


@pytest.mark.parametrize("task", TASKS, ids=IDS)
def test_existing_suite_is_green_on_buggy_code(task):
    result = gates.regression(task.module_name, task.buggy_module, task.existing_tests)
    assert result.ok, f"{task.id}: existing suite is not green on buggy code — {result.detail}"


@pytest.mark.parametrize("task", TASKS, ids=IDS)
def test_oracle_is_red_on_buggy_code(task):
    result = gates.oracle(task.module_name, task.buggy_module, task.oracle_test)
    assert not result.ok, f"{task.id}: oracle unexpectedly passes on buggy code (it doesn't exercise the bug)"


@pytest.mark.parametrize("task", TASKS, ids=IDS)
def test_gold_fix_makes_everything_green(task):
    reg = gates.regression(task.module_name, task.gold_module, task.existing_tests)
    orc = gates.oracle(task.module_name, task.gold_module, task.oracle_test)
    assert reg.ok, f"{task.id}: gold fix breaks the existing suite — {reg.detail}"
    assert orc.ok, f"{task.id}: gold fix does not satisfy the oracle — {orc.detail}"


def test_benchmark_has_enough_tasks():
    assert len(TASKS) >= 10, f"expected 10+ tasks, found {len(TASKS)}"
