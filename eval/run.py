from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from redgreen.agent.model import Model, ScriptedModel, build_model
from redgreen.agent.solver import SolverConfig, solve
from redgreen.baseline import run_baseline
from redgreen.bench.loader import Task, load_all, load_task
from redgreen.report import render_chart, render_markdown
from redgreen.trace import Tracer
from redgreen.verify import gates
from redgreen.verify.metrics import Record, grade_module_only, is_verified, summarise

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / "bench" / "tasks"


def evaluate(tasks: list[Task], model: Model, out: Path, config: SolverConfig, note: str) -> None:
    traj = out / "trajectories"
    records: list[Record] = []

    for task in tasks:
        b_trace = Tracer(traj / "baseline" / f"{task.id}.jsonl")
        b_trace.phase_start("grade", "single-shot baseline")
        patched = run_baseline(task, model, b_trace).patched_module
        b_verdict = grade_module_only(task, patched)
        b_trace.verdict(b_verdict.label)
        records.append(Record("baseline", task.id, b_verdict.label, is_verified(b_verdict),
                              trajectory=str((traj / "baseline" / f"{task.id}.jsonl"))))

        a_trace = Tracer(traj / "agent" / f"{task.id}.jsonl")
        solution = solve(task, model, a_trace, config)
        if solution.reproduced:
            a_verdict = gates.classify(task, solution.patched_module, solution.reproduction)
        else:
            a_verdict = gates.Verdict("NOT_REPRODUCED", ())
        a_trace.verdict(a_verdict.label)
        records.append(Record("agent", task.id, a_verdict.label, is_verified(a_verdict),
                              reproduced=solution.reproduced,
                              trajectory=str((traj / "agent" / f"{task.id}.jsonl"))))

        print(f"  {task.id:32s}  baseline={b_verdict.label:14s}  agent={a_verdict.label}")

    summaries = {"baseline": summarise("baseline", records), "agent": summarise("agent", records)}
    _write(out, records, summaries, note)


def _write(out: Path, records: list[Record], summaries: dict, note: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({
        "note": note,
        "records": [asdict(r) for r in records],
        "summaries": {k: asdict(v) for k, v in summaries.items()},
    }, indent=2) + "\n", encoding="utf-8")
    (out / "report.md").write_text(render_markdown(summaries, note=note), encoding="utf-8")
    if render_chart(summaries, out / "metrics.png"):
        print(f"  chart -> {out / 'metrics.png'}")
    print(f"\nWrote {out/'results.json'}, {out/'report.md'}")
    print("\n" + render_markdown(summaries, note=note))


def _smoke_model(task: Task) -> ScriptedModel:
    repro = (task.root / "fixtures" / "repro_good.py").read_text()
    hack = (task.root / "fixtures" / "hack.py").read_text()
    return ScriptedModel(reproduction=repro, fix=task.gold_module, hack=hack, baseline_output=hack)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate redgreen against a single-shot baseline.")
    parser.add_argument("--smoke", action="store_true", help="deterministic pipeline check, no API key")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "results")
    parser.add_argument("--tasks", type=Path, default=TASKS_DIR)
    parser.add_argument("--no-reviewer", action="store_true", help="ablation: disable the reviewer phase")
    args = parser.parse_args()

    config = SolverConfig(reviewer_enabled=not args.no_reviewer)

    if args.smoke:
        task = load_task(args.tasks / "merge_intervals_touching")
        print("Smoke run (scripted model, 1 task):")
        evaluate([task], _smoke_model(task), args.out / "smoke", config,
                 note="SYNTHETIC smoke run with a scripted model — proves the pipeline, not the model.")
        return

    tasks = load_all(args.tasks)
    provider = os.environ.get("REDGREEN_PROVIDER", "gemini")
    model_name = os.environ.get("REDGREEN_MODEL", "(provider default)")
    print(f"Real run ({provider} / {model_name}, {len(tasks)} tasks):")
    evaluate(tasks, build_model(), args.out, config,
             note=f"{provider} model ({model_name}) over the full benchmark.")


if __name__ == "__main__":
    main()
