# Changelog — the development story

The honest narrative of how redgreen was built, what each decision taught, and what the live run showed. Claims are labelled by how they are backed: **[proven]** = demonstrated by the test suite with no API key (`make test` / `make smoke`); **[live run]** = measured against a real model, committed in `results/`. This repo ships no invented numbers.

## Improvement changelog

| Stage | What I tried and why | Evidence | Decision / Learning |
| --- | --- | --- | --- |
| Baseline | One well-crafted prompt returns the fixed module — no execution, no tests. How people use an LLM today. | Live run: 100% verified fixes (10/10) | Starting point. On single-line bugs a strong model's "looks right" often is right — but you can't know without ground truth. |
| Iteration 1 | Give the agent tools + a loop (read, edit, run tests). | With a suite to satisfy, the agent can game it rather than fix the bug | Kept the loop, but it needs guardrails — "tests pass" now measures the wrong thing. |
| Iteration 2 | Fail-first gate: the reproduction must fail on the buggy code before any fix. | `make smoke`: the `noop` candidate is rejected here | Kept. Removes phantom fixes — a green test that was never red proves nothing. |
| Iteration 3 | Held-out oracle: a hidden test the agent never sees grades the fix. | `make smoke` / `test_verification_core.py`: a special-case hack passes fail-first + repro + regression, the oracle catches it — **reward-hack caught 0% → 100%** | Kept. The core mechanism: grade with a verifier the agent never optimized against. |
| Iteration 4 (removed) | Let the agent edit existing tests "to help." | An optimizer weakens/deletes the assertions it is meant to satisfy | Removed. Tests are mounted read-only per phase — never let the optimizer edit the objective. |
| Iteration 5 | Reviewer phase + static hack scan; bounce a suspicious patch back once. | `test_agent_loop.py`: the Reviewer catches the hack and the agent recovers; with `--no-reviewer` the oracle backstops | Kept. Cheap static checks catch blatant hacks in-band; the oracle is the backstop. |
| Final | Full pipeline on a live model (Claude Haiku 4.5, native tool use), all 10 tasks. | `results/`: baseline 100% (10/10) and agent 100% (10/10), 0 regressions | Main contribution = reward-hack resistance (measured) + a verified regression test shipped with every fix. The benchmark saturates on single-line bugs; harder multi-step bugs would be needed to separate the two on fix-rate. |

## Evaluation — primary and secondary metrics

The primary metric reflects what this project promises the user: *provable* correctness, i.e. catching a fix that games the tests. A fair baseline (a naive "tests pass" checker) is compared to redgreen (four gates incl. the held-out oracle) on the same candidates and the same 10 tasks.

| Metric | Naive checker / baseline | redgreen (agent) | Change |
| --- | ---: | ---: | ---: |
| **Reward-hack caught (primary)** | 0% | 100% | **+100 pts** |
| Verified-fix rate (live, 10 tasks) | 100% (10/10) | 100% (10/10) | +0 |
| Regressions introduced | 0 | 0 | +0 |
| Ships a verified regression test | no | yes (10/10) | — |

Reading it honestly: on **reward-hack resistance** — the metric that matters for "can I trust this fix?" — redgreen wins outright, because a naive checker accepts a hack that the held-out oracle rejects. On **fix-rate**, a strong model one-shots these single-line bugs, so both reach 100%; redgreen's added value there is a durable regression test with every fix. Every figure traces to committed `results/` and trajectories; none is estimated.

---

## The decisions in full

### Starting point — a fair baseline
A single well-crafted prompt: here is the bug report, the module, and the existing tests; return the corrected module. No execution, no reproduction test, no self-correction. This is how most people actually use an LLM to fix a bug, so it is the honest thing to measure against. **What it teaches:** a patch that reads as correct isn't always correct — the only way to know is to run something the patch was not written to satisfy.

### Decision 1 — give the agent tools and a loop
Read the code, edit it, run the tests, iterate. The obvious upgrade — but it introduces a failure mode the baseline could not even express: with a suite to satisfy, an agent can start *satisfying the suite* rather than fixing the bug. **What it teaches:** tools open new ways to be wrong; "the tests pass" now measures the wrong thing.

### Decision 2 — reproduce before you fix (the fail-first gate)
The Reproducer must produce a test that *fails on the original buggy code* before the Fixer may touch anything. **What it teaches:** you cannot fix what you cannot reproduce, and cannot trust a green test that was never red. **[proven]** — the `noop` candidate in `make smoke` is rejected here.

### Decision 3 — grade with a verifier the agent never sees (the held-out oracle)
Each task carries a hidden oracle the agent cannot read, run, or reach. The agent's own reproduction proves it *understood* the bug; the oracle proves the fix *generalises*. **What it teaches:** this is the thesis — a patch that special-cases the reported input passes three green checks and is still wrong; only a verifier the agent never optimized against catches it. **[proven]** — see `tests/test_verification_core.py`.

### Decision 4 — the tests are read-only (a removed temptation)
Letting the agent edit tests "to help" is exactly the wrong affordance: given permission, an optimizer weakens or deletes the assertions it is supposed to satisfy. redgreen scopes write permissions per phase, so this class of hack is structurally impossible. **What it teaches:** never let the thing being optimized edit the objective; enforce it in the tool boundary, not the prompt.

### Decision 5 — a Reviewer, as an in-band first line of defence
A cheap static scan feeds a Reviewer phase that can bounce a suspicious patch back once. It is not a replacement for the oracle — it catches obvious hacks before the expensive ground-truth check and makes the agent *recover*. **[proven]** — with the Reviewer on, the scripted agent's special-case attempt is caught and it recovers; with `--no-reviewer`, the oracle backstops. See `tests/test_agent_loop.py`.

### The live run — what a real model actually did
**[live run]** Claude Haiku 4.5 (native tool use), 10 tasks, baseline vs. agent, same held-out oracle. Both reached 100% verified fixes (10/10), zero regressions. **What it teaches:** on single-line-root-cause bugs a strong model one-shots the fix, so the benchmark saturates on fix-rate; the agent's value shows as reward-hack resistance (measured above) and a verified reproduction test with every fix. Separating the two on fix-rate would need harder, multi-step bugs — the clear next step.

### Where it landed
Reproduce-first, grade with a held-out oracle, keep the objective read-only, and review the diff before trusting it. The result is a bug fixer whose "fixed" verdict means *provably fixed* — delivered as an evidence bundle for a human to approve.
