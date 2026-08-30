"""Load a benchmark task from disk into an immutable ``Task``.

Each task directory has a fixed shape::

    <task>/
        meta.json           # id, module filename, difficulty, tags, ...
        report.md           # the bug report shown to the agent
        src/<module>.py     # the buggy module
        tests/test_*.py     # the pre-existing suite (green on buggy code)
        oracle/*.py         # the held-out oracle (never shown to the agent)
        gold.py             # reference fix, for grading only
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Task:
    id: str
    root: Path
    meta: dict
    module_name: str
    report: str
    buggy_module: str
    existing_tests: dict[str, str]
    oracle_test: str
    gold_module: str

    @property
    def title(self) -> str:
        return self.meta.get("title", self.id)


def load_task(root: str | Path) -> Task:
    root = Path(root)
    meta = json.loads((root / "meta.json").read_text())
    module_name = meta["module"]

    existing = {
        path.name: path.read_text()
        for path in sorted((root / "tests").glob("test_*.py"))
    }
    oracle_files = sorted((root / "oracle").glob("*.py"))
    if not oracle_files:
        raise ValueError(f"task {root} has no held-out oracle")

    return Task(
        id=meta["id"],
        root=root,
        meta=meta,
        module_name=module_name,
        report=(root / "report.md").read_text(),
        buggy_module=(root / "src" / module_name).read_text(),
        existing_tests=existing,
        oracle_test=oracle_files[0].read_text(),
        gold_module=(root / "gold.py").read_text(),
    )


def load_all(tasks_dir: str | Path) -> list[Task]:
    tasks_dir = Path(tasks_dir)
    return [
        load_task(child)
        for child in sorted(tasks_dir.iterdir())
        if (child / "meta.json").exists()
    ]
