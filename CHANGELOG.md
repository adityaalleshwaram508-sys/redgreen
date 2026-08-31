# Changelog — the development story

The honest narrative of how redgreen was built, what each decision taught, and what the
live run showed. Claims are labelled by how they are backed:

- **[proven]** — demonstrated by the test suite with no API key; reproduce with `make test`
  and `make smoke`.
- **[live run]** — measured against a real model; the committed numbers are in `results/`
  and summarised in the README. This repo ships no invented numbers.

---

## Starting point — a fair baseline

A single well-crafted prompt: here is the bug report, the module, and the existing tests;
return the corrected module. No execution, no reproduction test, no self-correction. This
is how most people actually use an LLM to fix a bug, so it is the honest thing to measure
against.

**What it teaches.** A patch that reads as correct isn't always correct. With no
ground-truth check, "looks right" is all you get — and the only way to know is to run
something the patch was not written to satisfy.

## Decision 1 — give the agent tools and a loop

Read the code, edit it, run the tests, iterate. This is the obvious upgrade — but it
introduces a failure mode the baseline could not even express: with a suite to satisfy, an
agent can start *satisfying the suite* rather than fixing the bug.

**What it teaches.** Tools don't just make an agent more capable; they open new ways for it
to be wrong. Measuring "the tests pass" now measures the wrong thing.

## Decision 2 — reproduce before you fix (the fail-first gate)

The Reproducer phase must produce a test that *fails on the original buggy code* before the
Fixer may touch anything. If the reproduction doesn't fail first, the bug was never
captured, and any later "green" is meaningless.

**What it teaches.** You cannot fix what you cannot reproduce, and you cannot trust a green
test that was never red. This gate removes "phantom fixes." **[proven]** — the `noop`
candidate in `make smoke` is rejected here.

## Decision 3 — grade with a verifier the agent never sees (the held-out oracle)

Each task carries a hidden oracle: a broader test for the same bug that the agent cannot
read, run, or reach through its tools. The agent's own reproduction proves it *understood*
the bug; the oracle proves the fix *generalises*.

**What it teaches.** This is the thesis. A patch that special-cases the reported input
passes the agent's own reproduction, the regression suite, and the fail-first gate — three
green checks — and is still wrong. Only a verifier the agent never optimized against catches
it. **[proven]** — the `hack` candidate in `make smoke` clears three gates and is caught by
the oracle; see `tests/test_verification_core.py`.

## Decision 4 — the tests are read-only (a removed temptation)

An early temptation is to let the agent edit tests "to help." It is exactly the wrong
affordance: given permission, an optimizer weakens or deletes the very assertions it is
supposed to satisfy. redgreen scopes write permissions per phase — the Reproducer may write
a test but not the module; the Fixer may write the module but never a test — so this class
of hack is structurally impossible, not merely discouraged.

**What it teaches.** Never let the thing being optimized edit the objective. Enforce it in
the tool boundary, not in the prompt.

## Decision 5 — a Reviewer, as an in-band first line of defence

A cheap static scan (input special-casing, broad/bare `except`, `xfail`/`skip`, wholesale
logic deletion) feeds a Reviewer phase that can bounce a suspicious patch back to the Fixer
once with a critique. It is not a replacement for the oracle — it is the fast, in-band check
that catches obvious hacks before the expensive ground-truth check, and it makes the agent
*recover* rather than simply fail.

**What it teaches.** Cheap static checks and expensive execution checks are complementary.
**[proven]** — with the Reviewer on, the scripted agent's special-case attempt is caught and
it recovers to a verified fix; with `--no-reviewer`, that same attempt survives the agent
and is caught only by the oracle. See `tests/test_agent_loop.py`.

## The live run — what a real model actually did

**[live run]** The full benchmark was run against Claude Haiku 4.5 (native tool use), 10
tasks, baseline vs. agent, graded by the same held-out oracle. Result: **both reached 100%
verified fixes (10/10), with zero regressions.**

**What it teaches.** On single-line-root-cause bugs, a strong model one-shots the fix, so
the fix-rate does not separate the two systems — the benchmark saturates. The agent's value
shows up in two places the raw rate doesn't capture: (1) it delivers a *verified reproduction
test* with every fix (red → green, committed under `results/trajectories/`), a durable
artifact the baseline never produces; and (2) the reward-hack resistance proven
deterministically above — the guardrail that matters the moment a model tries to game the
tests. A harder benchmark (multi-step bugs, or bugs whose obvious fix regresses another
behaviour) would be needed to separate the two on fix-rate alone; that is the clear next
step.

## Where it landed

Reproduce-first, grade with a held-out oracle, keep the objective read-only, and review the
diff before trusting it. The result is a bug fixer whose "fixed" verdict means *provably
fixed* — the reproduction went red then green, nothing else broke, and a verifier the agent
never saw agrees — delivered as an evidence bundle for a human to approve.
