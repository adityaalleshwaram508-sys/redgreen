# redgreen

**A test-first bug-fixing agent that produces fixes you can _prove_ — not just patches that look right.**

Give redgreen a bug report and a Python module and it returns a fix *together with the
evidence that the fix is correct*: a reproduction test that goes red → green, a proof that
the existing suite still passes, a check against a held-out oracle the agent never saw, and
a diff review that looks for reward-hacking. A human reviews the evidence bundle and
decides whether to merge. The agent never commits.

The one-line thesis: **an agent will satisfy whatever verifier you show it, so the verifier
that _grades_ a fix must be one the agent never saw.** redgreen is built around that idea,
and this repo demonstrates it empirically.

---

## Who this is for

A maintainer of a busy Python library, or an on-call engineer triaging inbound bug
reports. The slow, unglamorous part of fixing a reported bug isn't typing the patch — it's
the *reviewing*: writing a test that actually reproduces the problem, changing the code
without breaking anything else, and convincing yourself the fix addresses the root cause
rather than special-casing the one input in the report.

redgreen does that reviewing work up front and hands you the receipts. Instead of reading a
patch and reconstructing "does this really fix it, and does it break anything?", you read a
bundle that already answers both — a failing-then-passing reproduction, a green regression
run, and a held-out oracle pass — or you see exactly which gate the attempt failed.

## The idea, in one paragraph

Point a capable model at a test suite and tell it to make the tests pass, and it will —
sometimes by fixing the bug, and sometimes by special-casing the exact input, wrapping the
failing path in a broad `except`, or weakening the test. Passing the tests you showed it is
not evidence the bug is gone. redgreen separates the verifier the agent *sees* from the
verifier that *grades* it, and it gates the workflow so the agent must reproduce the bug
before it is allowed to fix it.

## How it works

Three phases, each with its own instructions and its own scoped tools, separated by hard
gates:

```
  Reproducer ──(reproduction FAILS on buggy code)──▶ Fixer ──(repro green AND
       ▲                                                       existing suite green)──▶ Reviewer
       │                                                                                    │
    write a failing test          edit only the module, no test edits            inspect the diff for
    (fail-first gate)             (repro-green + regression gates)                reward-hacking; bounce
                                                                                  back once if it smells
```

Four gates decide the verdict, in order:

1. **fail-first** — the agent's reproduction test must *fail on the original buggy code*.
   Without this, a test that never exercised the bug would "pass" after any change at all.
2. **repro-green** — that same test passes after the patch.
3. **regression** — every pre-existing test still passes.
4. **held-out oracle** — a hidden test the agent never sees also passes. This is what
   catches special-casing and other reward hacks.

Two design choices do most of the anti-hacking work: the existing tests are mounted
**read-only** (the optimizer may never edit its own objective), and the oracle is
**unreachable** from the agent's tools. A fast static scan for hack signatures
(input special-casing, swallowed exceptions, disabled tests, deleted logic) feeds the
Reviewer as an in-band first line of defence; the oracle is the ground-truth backstop.

**Human-in-the-loop by design.** redgreen proposes a patch and its evidence; it does not
commit, push, or merge. Fixing code that can ship is consequential, and consequential
actions belong to a human reviewer.

## The core result — reproducible right now, no API key

The central claim is demonstrated with zero model calls, deterministically, by the test
suite. A patch that *special-cases the reported input* sails through the first three gates —
it reproduces, it goes green, it breaks nothing — and looks like a perfect fix under any
naive "do the tests pass?" checker. The held-out oracle is the only thing that catches it:

```
$ make test        # 39 tests, no key required
$ make smoke       # runs the full pipeline on one task with a scripted model

  candidate                          verdict         why
  gold  (real fix)                   VERIFIED_FIX    all four gates pass
  hack  (special-cases the input)    REWARD_HACK     passes fail-first + repro + regression,
                                                     oracle FAILS on 5 other touching cases
  noop  (no change)                  NOT_FIXED       reproduction stays red
```

That contrast — *the same candidate that passes its own test gets caught by the verifier it
never saw* — is the whole argument, and it runs in seconds on any machine.

## Head-to-head vs. a fair baseline — run with your key

The baseline is not a strawman: it's how a capable engineer uses an LLM today without a
verification loop — same bug report, same module, same tests, one shot to return a fix.
Both systems are graded by the *same* held-out oracle, so the gap is the value of the
methodology, with the model held constant.

Run `make eval` with a live model to populate this table (numbers below are placeholders):

| Metric | Baseline (single-shot) | redgreen (agent) |
| --- | ---: | ---: |
| Verified-fix rate (oracle passes, no regressions) | `__%` | `__%` |
| Reward-hack rate | `__%` | `__%` |
| Reproduction rate | — | `__%` |

An ablation — `make eval-no-reviewer` — isolates the Reviewer phase's contribution. The
generated `results/report.md`, `results/metrics.png`, and per-run trajectories under
`results/trajectories/` are the evidence behind every number.

> Honesty note: the reward-hacking demonstration above is real and reproduced by the test
> suite. The head-to-head rates depend on a live model and are produced by *your* `make eval`
> run — this repo does not ship invented numbers.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

make test     # 39 tests, no API key
make smoke     # deterministic full-pipeline demo, no API key

export ANTHROPIC_API_KEY=sk-...
export REDGREEN_MODEL=claude-sonnet-4-5   # any Claude model you have access to
make eval      # baseline vs. agent over all 10 tasks; writes results/ + trajectories/
```

See [REPRODUCTION.md](REPRODUCTION.md) for a clean-environment walkthrough, runtime, and
cost.

## What's in here

```
src/redgreen/
  agent/         model boundary (real + scripted), the 3-phase orchestrator, prompts/
  tools/         pytest-in-subprocess runner, the agent's scoped toolbox
  verify/        the 4 gates, the static reward-hack scanner, grading + metrics
  bench/         task loader
  trace.py       structured JSONL trajectory logging
  baseline.py    the fair single-shot baseline
bench/tasks/     10 realistic bug archetypes, each with a held-out oracle  (see bench/SCHEMA.md)
eval/            the evaluation harness
tests/           redgreen's own suite: verification core, agent loop, benchmark integrity
```

## The benchmark is part of the contribution

`bench/tasks/` is a small, fully offline, deterministic benchmark of ten realistic Python
bug archetypes — boundary conditions, mutable-default state leaks, greedy regexes,
off-by-one binary search, order-losing dedupe, banker's rounding, and more — each paired
with a **held-out oracle** specifically so reward-hacking can be *measured*. Every task is
validated by `tests/test_benchmark_integrity.py`: the existing suite is green on the buggy
code, the oracle is red on it, and the gold reference fix turns both green. Format and
authoring guide in [bench/SCHEMA.md](bench/SCHEMA.md).

## Disclosure

This project was built with the assistance of an AI coding agent (Claude, by Anthropic).
The *solution* — redgreen itself — is an agent that runs on the Anthropic Messages API at
temperature 0; set `REDGREEN_MODEL` to pin the model. Every redgreen run emits a full
trajectory to `results/trajectories/`, which are included as the primary trajectory
artifacts. See [CHANGELOG.md](CHANGELOG.md) for the development narrative and what each
design decision taught.

## License

MIT — see [LICENSE](LICENSE).
