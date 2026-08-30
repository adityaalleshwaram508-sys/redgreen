"""Trajectory capture.

The challenge treats agent trajectories as a first-class, required deliverable, so they
are not reconstructed after the fact — every phase, model turn, tool call, tool result,
gate outcome and final verdict is appended to a JSONL file as it happens. One file per
solve. The format is deliberately flat and greppable: each line is a self-contained event
with a monotonically increasing sequence number and a phase, so a reviewer can read a run
top to bottom or filter to a single phase without special tooling.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Tracer:
    path: Path
    _seq: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("")  # truncate any previous run

    def _emit(self, phase: str, event: str, **data: Any) -> None:
        self._seq += 1
        record = {"seq": self._seq, "t": round(time.time(), 3), "phase": phase, "event": event, **data}
        with self.path.open("a") as handle:
            handle.write(json.dumps(record, default=str) + "\n")

    # -- event helpers ---------------------------------------------------------------
    def phase_start(self, phase: str, note: str = "") -> None:
        self._emit(phase, "phase_start", note=note)

    def model_turn(self, phase: str, response) -> None:
        self._emit(
            phase,
            "model_turn",
            text=response.text,
            tool_calls=[{"name": c.name, "input": c.input} for c in response.tool_calls],
        )

    def tool(self, phase: str, name: str, payload: dict, result: str) -> None:
        self._emit(phase, "tool_call", tool=name, input=_trim(payload), result=_trim_str(result))

    def gate(self, phase: str, gate) -> None:
        self._emit(phase, "gate", gate=gate.name, ok=gate.ok, detail=gate.detail)

    def review(self, phase: str, findings: list, decision: str) -> None:
        self._emit(phase, "review", findings=[asdict(f) for f in findings], decision=decision)

    def verdict(self, label: str) -> None:
        self._emit("grade", "verdict", label=label)


def _trim(payload: dict, limit: int = 4000) -> dict:
    return {k: _trim_str(v, limit) if isinstance(v, str) else v for k, v in payload.items()}


def _trim_str(text: str, limit: int = 4000) -> str:
    text = str(text)
    return text if len(text) <= limit else text[:limit] + f"\n… [{len(text) - limit} more chars]"
