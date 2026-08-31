# redgreen

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![tests](https://img.shields.io/badge/tests-39%20passing-brightgreen)
![core result](https://img.shields.io/badge/core%20result-reproducible%20without%20an%20API%20key-8A2BE2)

**A test-first bug-fixing agent that produces fixes you can _prove_ — not just patches that look right.**

Give redgreen a bug report and a Python module and it returns a fix *together with the evidence that the fix is correct*: a reproduction test that goes red then green, a proof that the existing suite still passes, a check against a held-out oracle the agent never saw, and a diff review that looks for reward-hacking. A human reviews the evidence bundle and decides whether to merge. The agent never commits.

The one-line thesis: **an agent will satisfy whatever verifier you show it, so the verifier that _grades_ a fix must be one the agent never saw.** redgreen is built around that idea, and this repo demonstrates it empirically.

---

## Who this is for

A maintainer of a busy Python library, or an on-call engineer triaging inbound bug reports. The slow, unglamorous part of fixing a reported bug isn't typing the patch — it's the *reviewing*: writing a test that actually reproduces the problem, changing the code without breaking anything else, and convincing yourself the fix addresses the root cause rather than special-casing the one input in the report.

redgreen does that reviewing work up front and hands you the receipts. Instead of reading a patch and reconstructing "does this really fix it, and does it break anything?", you read a bundle that already answers both — a failing-then-passing reproduction, a green regression run, and a held-out oracle pass — or you see exactly which gate the attempt failed.

## The idea, in one paragraph

Point a capable model at a test suite and tell it to make the tests pass, and it will — sometimes by fixing the bug, and sometimes by special-casing the exact input, wrapping the failing path in a broad `except`, or weakening the test. Passing the tests you showed it is not evidence the bug is gone. redgreen separates the verifier the agent *sees* from the verifier that *grades* it, and it gates the workflow so the agent must reproduce the bug before it is allowed to fix it.

## How it works

Three phases, each with its own instructions and its own scoped tools, separated by hard gates:

```
Phase 1  Reproducer  ->  write a test that FAILS on the buggy code   (fail-first gate)
Phase 2  Fixer       ->  edit only the module; no test edits allowed
                         reproduction passes AND existing suite passes (repro-green + regression gates)
Phase 3  Reviewer    ->  inspect the diff for reward-hacking; bounce back to the Fixer once if it smells
```

Four gates decide the verdict, in order:

1. **fail-first** — the agent's reproduction test must *fail on the original buggy code*. Without this, a test that never exercised the bug would "pass" after any change at all.
2. **repro-green** — that same test passes after the patch.
3. **regression** — every pre-existing test still passes.
4. **held-out oracle** — a hidden test the agent never sees also passes. This is what catches special-casing and other reward hacks.

Two design choices do most of the anti-hacking work: the existing tests are mounted **read-only** (the optimizer may never edit its own objective), and the oracle is **unreachable** from the agent's tools. A fast static scan for hack signatures (input special-casing, swallowed exceptions, disabled tests, deleted logic) feeds the Reviewer as an in-band first line of defence; the oracle is the ground-truth backstop.

**Human-in-the-loop by design.** redgreen proposes a patch and its evidence; it does not commit, push, or merge. Fixing code that can ship is consequential, and consequential actions belong to a human reviewer.

## Results

Two things are measured here, and both come from evidence committed to this repo.

### 1. Reward-hack resistance — deterministic, reproduce with `make test` / `make smoke` (no API key)

This is the core claim, and it needs no model to prove. A patch that *special-cases the reported input* passes the fail-first gate, the reproduction, and the full regression suite — three green checks that fool any "do the tests pass?" checker — and is caught **only** by the held-out oracle:

| Metric | Naive checker (tests only) | redgreen (held-out oracle) |
| --- | ---: | ---: |
| Reward-hack caught | 0% | 100% |

Proven by `tests/test_verification_core.py` and `tests/test_agent_loop.py` — 39 tests, no network. The same candidate that passes its own test is rejected by the verifier it never saw. This is the mechanism that matters the moment a model tries to game a test suite.

### 2. Live run on a real model — Claude Haiku 4.5, native tool use, all 10 tasks

| Metric | Baseline (single-shot) | redgreen (agent) |
| --- | ---: | ---: |
| Verified-fix rate | 100% (10/10) | 100% (10/10) |
| Regressions introduced | 0 | 0 |
| Reproduction rate | — | 100% (10/10) |
| Ships a regression test with the fix | no | **yes (10/10)** |

On these single-root-cause bugs a strong model one-shots the fix, so both systems reach 100% — redgreen matches a capable baseline at **zero regression cost**. The difference is what redgreen *additionally* delivers: for every fix it produces a reproduction test proven to go red then green, plus a full JSONL trajectory under `results/trajectories/`. The baseline returns a patch you must trust; redgreen returns a patch **and the proof**.

**Honest reading of these numbers:** this benchmark is intentionally controlled and its bugs are single-line root causes, which a strong model solves in one shot — so the live run shows *parity plus a durable regression-test artifact*, not a fix-rate gap. The measured contribution is the reward-hack resistance in (1), which a naive test-passing checker does not have. Every figure here is backed by committed results and trajectories; none is estimated.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

make test      # 39 tests, no API key
make smoke     # deterministic full-pipeline demo, no API key
```

To run the live evaluation, set a provider and key, then run the harness. redgreen supports Anthropic (native tool use) and Google Gemini (via a JSON tool-use adapter):

```bash
# Anthropic
export REDGREEN_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export REDGREEN_MODEL=claude-haiku-4-5
python -m eval.run          # baseline vs. agent over all 10 tasks

# or Gemini (free tier is heavily rate-limited; the client paces and retries automatically)
export REDGREEN_PROVIDER=gemini
export GEMINI_API_KEY=AIza...
export REDGREEN_MODEL=gemini-3.6-flash
python -m eval.run --tasks bench/mini --out results/live   # a small slice fits free limits
```

Results and per-run trajectories are written under `results/`. On Windows without `make`, use `python -m pytest` for the tests and `python -m eval.run --smoke` for the smoke run. See [REPRODUCTION.md](REPRODUCTION.md) for a clean-environment walkthrough.

## What's in here

```
src/redgreen/
  agent/        model boundary (Anthropic + Gemini + scripted), 3-phase orchestrator, prompts/
  tools/        pytest-in-subprocess runner, the agent's scoped toolbox
  verify/       the 4 gates, the static reward-hack scanner, grading + metrics
  bench/        task loader
  trace.py      structured JSONL trajectory logging
  baseline.py   the fair single-shot baseline
bench/tasks/    10 realistic bug archetypes, each with a held-out oracle (see bench/SCHEMA.md)
eval/           the evaluation harness
tests/          redgreen's own suite: verification core, agent loop, benchmark integrity
results/        committed real run (Claude Haiku 4.5) + trajectories
```

## The benchmark is part of the contribution

`bench/tasks/` is a small, fully offline, deterministic benchmark of ten realistic Python bug archetypes — boundary conditions, mutable-default state leaks, greedy regexes, off-by-one binary search, order-losing dedupe, banker's rounding, and more — each paired with a **held-out oracle** specifically so reward-hacking can be *measured*. Every task is validated by `tests/test_benchmark_integrity.py`: the existing suite is green on the buggy code, the oracle is red on it, and the gold reference fix turns both green. Format and authoring guide in [bench/SCHEMA.md](bench/SCHEMA.md).

## Disclosure

This project was built with the assistance of an AI coding agent (Claude, by Anthropic). The *solution* — redgreen itself — is an agent that can run on the Anthropic Messages API (native tool use) or on Google Gemini (via a small JSON tool-use adapter); the provider and model are selected with `REDGREEN_PROVIDER` and `REDGREEN_MODEL`. The committed results in `results/` are from a live Claude Haiku 4.5 run. Every redgreen run emits a full trajectory to `results/trajectories/`, included as the primary trajectory artifacts. See [CHANGELOG.md](CHANGELOG.md) for the development narrative and what each design decision taught.

## License

MIT — see [LICENSE](LICENSE).
