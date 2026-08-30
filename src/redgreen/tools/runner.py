"""Run pytest against a workspace and return a structured result.

This is the one place the whole project touches the ground truth. It shells out to
``pytest`` in a subprocess (so a hanging or crashing candidate can be killed on a
timeout without taking the agent down) and parses the JUnit XML report rather than
scraping stdout, so per-test outcomes are reliable across pytest versions. JUnit XML is
built into pytest, which keeps our dependency surface at exactly one package.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

# pytest exit codes we care about (see `pytest --help`): 0 = all passed, 1 = tests
# failed, 5 = no tests collected. Anything else is a collection/usage error.
_TIMEOUT_RC = 124


@dataclass(frozen=True)
class TestOutcome:
    nodeid: str
    outcome: str  # "passed" | "failed" | "error" | "skipped"
    message: str = ""


@dataclass
class PytestRun:
    returncode: int
    outcomes: list[TestOutcome] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration_s: float = 0.0

    @property
    def collected(self) -> bool:
        return bool(self.outcomes)

    @property
    def all_passed(self) -> bool:
        """True only if pytest ran at least one test and every one passed."""
        return self.returncode == 0 and self.collected

    def failures(self) -> list[TestOutcome]:
        return [o for o in self.outcomes if o.outcome in ("failed", "error")]


def run_pytest(workdir: Path, targets: list[str], timeout_s: int = 60) -> PytestRun:
    """Run the given test files inside ``workdir`` and return the parsed result."""
    workdir = Path(workdir)
    report = workdir / "_redgreen_junit.xml"
    cmd = [
        sys.executable, "-m", "pytest",
        "-q", "-p", "no:cacheprovider",
        f"--junit-xml={report}",
        *targets,
    ]
    # Put the workspace on the import path and never write bytecode into the read-only
    # source tree; both keep runs hermetic and repeatable.
    env = {**os.environ, "PYTHONPATH": str(workdir), "PYTHONDONTWRITEBYTECODE": "1"}

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, cwd=workdir, env=env,
            capture_output=True, text=True, timeout=timeout_s,
        )
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc = _TIMEOUT_RC
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")) + "\n[redgreen] pytest timed out"

    return PytestRun(
        returncode=rc,
        outcomes=_parse_junit(report),
        stdout=out,
        stderr=err,
        duration_s=time.perf_counter() - start,
    )


def _parse_junit(path: Path) -> list[TestOutcome]:
    if not path.exists():
        return []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return []

    outcomes: list[TestOutcome] = []
    for case in root.iter("testcase"):
        name = case.get("name", "")
        classname = case.get("classname", "")
        nodeid = f"{classname}::{name}" if classname else name

        error = case.find("error")
        failure = case.find("failure")
        skipped = case.find("skipped")
        if error is not None:
            outcome, message = "error", error.get("message", "")
        elif failure is not None:
            outcome, message = "failed", failure.get("message", "")
        elif skipped is not None:
            outcome, message = "skipped", skipped.get("message", "")
        else:
            outcome, message = "passed", ""
        outcomes.append(TestOutcome(nodeid, outcome, message))
    return outcomes
