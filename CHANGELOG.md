# Changelog — the development story

This is the honest narrative of how redgreen was built and what each decision taught. Two
kinds of claim appear below, and they are labelled:

- **[proven]** — demonstrated by the test suite with no API key; reproduce with `make test`
  and `make smoke`.
- **[pending live run]** — a quantitative claim that depends on a live model; produced by
  `make eval` and filled into the table in the README. This repo ships no invented numbers.

The measurable improvement arc is three runnable configurations, all graded by the same
held-out oracle: the single-shot **baseline**, the **agent without the Reviewer**
(`make eval-no-reviewer`), and the **full agent** (`make eval`).

---

## Starting point — a fair baseline

A single well-crafted prompt: here is the bug report, the module, and the existing tests;
return the corrected module. No execution, no reproduction test, no self-correction. This
is how most people actually use an LLM to fix a bug, so it is the honest thing to measure
against.

**What it teaches.** A patch that reads as correct often isn't. With no ground-truth check,
"looks right" is all you get, and for subtle boundary bugs that is frequently wrong.
*[pending live run: baseline verified-fix rate.]*

## Decision 1 — give the agent tools and a loop

Read the code, edit it, run the tests, iterate. This is the obvious upgrade and it does
raise the fix rate — but it introduces a new failure mode that the baseline could not even
express: with a suite to satisfy, the agent starts *satisfying the suite* rather than
fixing the bug.

**What it teaches.** Tools don't just make an agent more capable; they open new ways for it
to be wrong. Measuring "the tests pass" now measures the wrong thing.

## Decision 2 — reproduce before you fix (the fail-first gate)

The Reproducer phase must produce a test that *fails on the original buggy code* before the
Fixer is allowed to touch anything. If the reproduction doesn't fail first, the bug was
never captured, and any subsequent "green" is meaningless.

**What it teaches.** You cannot fix what you cannot reproduce, and you cannot trust a green
test that was never red. This single gate removes "phantom fixes." **[proven]** — the
`noop` candidate in `make smoke` is rejected here.

## Decision 3 — grade with a verifier the agent never sees (the held-out oracle)

Each task carries a hidden oracle: a second, broader test for the same bug that the agent
cannot read, run, or reach through its tools. The agent's own reproduction proves it
*understood* the bug; the oracle proves the fix *generalises*.

**What it teaches.** This is the thesis. A patch that special-cases the reported input
passes the agent's own reproduction, the regression suite, and the fail-first gate — three
green checks — and is still wrong. Only a verifier the agent never optimized against catches
it. **[proven]** — the `hack` candidate in `make smoke` clears three gates and is caught by
the oracle on five other cases; see `tests/test_verification_core.py`.

## Decision 4 — the tests are read-only (a removed temptation)

An early temptation is to let the agent edit tests "to help." It is exactly the wrong
affordance: given permission, an optimizer weakens or deletes the very assertions it is
supposed to satisfy. redgreen scopes write permissions per phase — the Reproducer may write
a test but not the module; the Fixer may write the module but never a test — so this class
of hack is structurally impossible rather than merely discouraged.

**What it teaches.** Never let the thing being optimized edit the objective. Enforce it in
the tool boundary, not in the prompt.

## Decision 5 — a Reviewer, as an in-band first line of defence

A cheap static scan (input special-casing, broad/bare `except`, `xfail`/`skip`, wholesale
logic deletion) feeds a Reviewer phase that can bounce a suspicious patch back to the Fixer
once with a critique. It is not a replacement for the oracle — it is the fast, in-band check
that catches obvious hacks before the expensive ground-truth check, and it makes the agent
*recover* rather than simply fail.

**What it teaches.** Cheap static checks and expensive execution checks are complementary:
the scan catches the blatant hacks early and in-context; the oracle remains the backstop for
the subtle ones. **[proven]** — with the Reviewer on, the scripted agent's special-case
attempt is caught and it recovers to a verified fix; with `--no-reviewer`, that same attempt
survives the agent and is caught only by the oracle. See `tests/test_agent_loop.py`.
*[pending live run: the Reviewer's effect on the live reward-hack rate, via
`make eval-no-reviewer`.]*

## Where it landed

Reproduce-first, grade with a held-out oracle, keep the objective read-only, and review the
diff before trusting it. The result is a bug fixer whose "fixed" verdict means *provably
fixed* — the reproduction went red then green, nothing else broke, and a verifier the agent
never saw agrees — delivered as an evidence bundle for a human to approve.
