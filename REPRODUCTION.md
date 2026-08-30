# Reproduction

Everything here runs from a clean checkout. The parts that need no API key are fully
deterministic; the live evaluation needs a Claude API key and one environment variable.

## 1. Environment

- Python 3.10 or newer (developed on 3.12).
- No system dependencies beyond Python. The only hard runtime dependency is `pytest`;
  `matplotlib` is optional and only used to render the results chart.

```bash
git clone https://github.com/adityaalleshwaram508-sys/redgreen.git
cd redgreen
python -m venv .venv && source .venv/bin/activate
pip install -e .            # installs redgreen + pytest
pip install -e ".[report]"  # optional: adds matplotlib for the chart
```

## 2. Reproduce the core result — no API key

```bash
make test     # 39 tests: verification core, agent loop (scripted model), benchmark integrity
make smoke     # runs the full baseline+agent pipeline on one task with a scripted model
```

`make test` proves, deterministically, the claim the whole project rests on: a patch that
special-cases the reported input passes the fail-first, repro-green, and regression gates
but is caught by the held-out oracle. `make smoke` exercises the entire evaluation pipeline
(grading, metrics, report, trajectory logging) and writes results to `results/smoke/`. No
network, no key.

## 3. Reproduce the head-to-head — live model

```bash
export ANTHROPIC_API_KEY=sk-...
export REDGREEN_MODEL=claude-sonnet-4-5   # set to a Claude model your key can access
make eval                  # baseline vs. agent over all 10 tasks
make eval-no-reviewer      # ablation: the agent with the Reviewer phase disabled
```

Outputs, written under `results/`:

- `results.json` — every per-task record plus the two summaries.
- `report.md` — the comparison table.
- `metrics.png` — the two-bar chart (if `matplotlib` is installed).
- `trajectories/<system>/<task>.jsonl` — one structured trajectory per solve, readable top
  to bottom.

### Pinning the model

`REDGREEN_MODEL` is the single knob that determines which model runs. It is read at
runtime; nothing is hardcoded. Record the exact value you used alongside your results so a
reviewer can reproduce them.

## 4. Approximate runtime and cost

Deterministic paths (`make test`, `make smoke`) finish in well under a minute on a laptop
and cost nothing.

The live evaluation runs two systems over ten tasks. The baseline is a single call per
task; the agent makes a handful of calls per task across its three phases (typically on the
order of five to ten). That puts a full `make eval` in the low hundreds of model calls at
most — a few minutes of wall-clock and, on a mid-tier model, well under a US dollar. Treat
these as estimates and confirm against your own provider dashboard; actual figures depend
on the model you pin and how many phases each task needs.

## 5. Adding a benchmark task

Tasks are plain directories under `bench/tasks/`. Copy an existing one, follow
[bench/SCHEMA.md](bench/SCHEMA.md), and run `make test` — `tests/test_benchmark_integrity.py`
will tell you immediately if the existing suite isn't green on the bug, the oracle isn't
red on it, or the gold fix doesn't satisfy both.
