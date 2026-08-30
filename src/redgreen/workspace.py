"""Throwaway, isolated filesystem sandboxes for running candidate patches.

Every gate runs pytest against a *fresh* copy of the relevant files so that one gate can
never leak state into another (a stray ``.pyc`` or an in-place mutation of the module
would otherwise make results depend on execution order). Cheap to create, always cleaned
up.
"""
from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def workspace(files: Mapping[str, str]) -> Iterator[Path]:
    """Write ``{relative_path: contents}`` into a temp dir and yield its path.

    The directory (and everything under it) is deleted on exit, success or failure.
    """
    root = Path(tempfile.mkdtemp(prefix="redgreen_ws_"))
    try:
        for rel, contents in files.items():
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents)
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)
