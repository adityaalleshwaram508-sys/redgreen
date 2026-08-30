"""The tools the agent is allowed to use, and nothing else.

The toolbox holds the mutable working state for one solve — the current module source and
the reproduction test the agent has written — and exposes exactly four tools. Two design
choices matter:

* The held-out oracle is never reachable from here. The agent cannot see it, run it, or
  learn its contents, which is the whole point.
* Write permissions are scoped per phase. The Reproducer may write a test but not the
  module; the Fixer may write the module but never a test. That single constraint removes
  the most common reward hack — the agent "helping" by weakening the test it must pass.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..bench.loader import Task
from ..tools.runner import run_pytest
from ..workspace import workspace

_REPRO_FILE = "test_repro.py"

READ_REPO = "read_repo"
WRITE_MODULE = "write_module"
WRITE_REPRO = "write_reproduction_test"
RUN_TESTS = "run_tests"


@dataclass
class ToolBox:
    task: Task
    can_write_module: bool
    can_write_repro: bool
    module: str = ""
    reproduction: str | None = None

    def __post_init__(self) -> None:
        if not self.module:
            self.module = self.task.buggy_module

    # -- schemas advertised to the model --------------------------------------------
    def schemas(self) -> list[dict]:
        tools = [
            {
                "name": READ_REPO,
                "description": (
                    "Return the bug report, the current source of the module under test, "
                    "and the pre-existing test suite (read-only)."
                ),
                "input_schema": {"type": "object", "properties": {}},
            },
            {
                "name": RUN_TESTS,
                "description": (
                    "Run pytest and return per-test results. 'reproduction' runs your "
                    "reproduction test; 'existing' runs the pre-existing suite; 'both' "
                    "runs both."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "which": {"type": "string", "enum": ["reproduction", "existing", "both"]}
                    },
                    "required": ["which"],
                },
            },
        ]
        if self.can_write_repro:
            tools.append(
                {
                    "name": WRITE_REPRO,
                    "description": "Create or overwrite the reproduction test file.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"content": {"type": "string"}},
                        "required": ["content"],
                    },
                }
            )
        if self.can_write_module:
            tools.append(
                {
                    "name": WRITE_MODULE,
                    "description": "Overwrite the module under test with new source.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"content": {"type": "string"}},
                        "required": ["content"],
                    },
                }
            )
        return tools

    # -- dispatch --------------------------------------------------------------------
    def dispatch(self, name: str, payload: dict) -> str:
        if name == READ_REPO:
            return self._read_repo()
        if name == WRITE_REPRO:
            if not self.can_write_repro:
                return "ERROR: writing a reproduction test is not permitted in this phase."
            self.reproduction = payload["content"]
            return "Reproduction test written."
        if name == WRITE_MODULE:
            if not self.can_write_module:
                return "ERROR: editing the module is not permitted in this phase."
            self.module = payload["content"]
            return "Module updated."
        if name == RUN_TESTS:
            return self._run_tests(payload.get("which", "both"))
        return f"ERROR: unknown tool {name!r}."

    def _read_repo(self) -> str:
        existing = "\n\n".join(
            f"# --- {fname} (read-only) ---\n{src}"
            for fname, src in self.task.existing_tests.items()
        )
        return (
            f"## Bug report\n{self.task.report}\n\n"
            f"## Module: {self.task.module_name}\n{self.module}\n\n"
            f"## Pre-existing tests (read-only)\n{existing}"
        )

    def _run_tests(self, which: str) -> str:
        files: dict[str, str] = {self.task.module_name: self.module}
        targets: list[str] = []
        if which in ("reproduction", "both"):
            if self.reproduction is None:
                return "No reproduction test has been written yet."
            files[_REPRO_FILE] = self.reproduction
            targets.append(_REPRO_FILE)
        if which in ("existing", "both"):
            files.update(self.task.existing_tests)
            targets.extend(self.task.existing_tests)

        with workspace(files) as ws:
            run = run_pytest(ws, targets)
        return _summarise(run)


def _summarise(run) -> str:
    lines = [f"exit={run.returncode}  {'all passed' if run.all_passed else 'FAILURES PRESENT'}"]
    for outcome in run.outcomes:
        tag = outcome.outcome.upper()
        msg = f"  ({outcome.message.splitlines()[0]})" if outcome.message else ""
        lines.append(f"  [{tag}] {outcome.nodeid}{msg}")
    if not run.collected:
        lines.append("  (no tests collected — check imports and file names)")
    return "\n".join(lines)
