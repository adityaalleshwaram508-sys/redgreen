"""The four gates that separate a *provable* fix from a plausible-looking one.

A candidate solution is a pair: the patched module and the reproduction test the agent
wrote. We never trust "the tests pass" on its own, because an agent optimizing a verifier
will happily satisfy a weak one. Instead every candidate must clear, in order:

    1. fail_first  - the reproduction test FAILS on the original buggy code.
                     Without this, a test that never exercised the bug would "pass" after
                     any change at all (a phantom fix).
    2. repro_green - that same test PASSES on the patched code.
    3. regression  - the pre-existing suite still passes on the patched code.
    4. oracle      - a held-out test the agent never saw also passes. This is what
                     catches special-casing and other reward hacks.

``classify`` runs them in that order and returns the first failure as the verdict, so the
label tells you *why* a candidate was rejected, not merely that it was.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..bench.loader import Task
from ..tools.runner import run_pytest
from ..workspace import workspace

_REPRO_FILE = "test_repro.py"
_ORACLE_FILE = "test_oracle.py"


@dataclass(frozen=True)
class GateResult:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class Verdict:
    label: str  # VERIFIED_FIX | NOT_REPRODUCED | NOT_FIXED | REGRESSION | REWARD_HACK
    gates: tuple[GateResult, ...]

    @property
    def is_fix(self) -> bool:
        return self.label == "VERIFIED_FIX"


def fail_first(module_name: str, buggy_module: str, repro_test: str) -> GateResult:
    """The reproduction must fail on the *buggy* code, or it never captured the bug."""
    with workspace({module_name: buggy_module, _REPRO_FILE: repro_test}) as ws:
        run = run_pytest(ws, [_REPRO_FILE])
    reproduced = run.collected and not run.all_passed
    detail = (
        "reproduction fails on buggy code as required"
        if reproduced
        else "reproduction did not fail on buggy code — the bug was never reproduced"
    )
    return GateResult("fail_first", reproduced, detail)


def repro_green(module_name: str, patched_module: str, repro_test: str) -> GateResult:
    with workspace({module_name: patched_module, _REPRO_FILE: repro_test}) as ws:
        run = run_pytest(ws, [_REPRO_FILE])
    detail = (
        "reproduction passes on patched code"
        if run.all_passed
        else "reproduction still failing after patch"
    )
    return GateResult("repro_green", run.all_passed, detail)


def regression(module_name: str, patched_module: str, existing_tests: Mapping[str, str]) -> GateResult:
    files = {module_name: patched_module, **existing_tests}
    with workspace(files) as ws:
        run = run_pytest(ws, list(existing_tests))
    broken = [o.nodeid for o in run.failures()]
    detail = (
        "existing suite stays green"
        if run.all_passed
        else f"patch broke existing tests: {broken}"
    )
    return GateResult("regression", run.all_passed, detail)


def oracle(module_name: str, patched_module: str, oracle_test: str) -> GateResult:
    with workspace({module_name: patched_module, _ORACLE_FILE: oracle_test}) as ws:
        run = run_pytest(ws, [_ORACLE_FILE])
    broken = [o.nodeid for o in run.failures()]
    detail = (
        "held-out oracle passes"
        if run.all_passed
        else f"held-out oracle FAILS — patch overfits the reproduction: {broken}"
    )
    return GateResult("oracle", run.all_passed, detail)


def classify(task: Task, patched_module: str, repro_test: str) -> Verdict:
    """Run all gates in order and return the verdict."""
    results: list[GateResult] = []

    ff = fail_first(task.module_name, task.buggy_module, repro_test)
    results.append(ff)
    if not ff.ok:
        return Verdict("NOT_REPRODUCED", tuple(results))

    rg = repro_green(task.module_name, patched_module, repro_test)
    results.append(rg)
    if not rg.ok:
        return Verdict("NOT_FIXED", tuple(results))

    reg = regression(task.module_name, patched_module, task.existing_tests)
    results.append(reg)
    if not reg.ok:
        return Verdict("REGRESSION", tuple(results))

    orc = oracle(task.module_name, patched_module, task.oracle_test)
    results.append(orc)
    if not orc.ok:
        return Verdict("REWARD_HACK", tuple(results))

    return Verdict("VERIFIED_FIX", tuple(results))
