"""Canonical filesystem locations, resolved relative to the installed package.

Centralising these keeps the loader, the eval harness, and the tests from each
re-deriving ``parents[n]`` chains that break the moment a file moves.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH_DIR = REPO_ROOT / "bench"
TASKS_DIR = BENCH_DIR / "tasks"
RESULTS_DIR = REPO_ROOT / "results"
