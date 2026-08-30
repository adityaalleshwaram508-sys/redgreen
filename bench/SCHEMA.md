# Benchmark schema

Each task in `bench/tasks/<id>/` is a self-contained, offline reproduction of one realistic
Python bug archetype, paired with a held-out oracle so that reward-hacking can be measured.

## Layout

```
bench/tasks/<id>/
  meta.json            id, title, archetype, difficulty, module filename, tags
  report.md            the bug report shown to the agent (reads like a real issue)
  src/<module>.py      the buggy module under test
  tests/test_<id>.py   the pre-existing suite — GREEN on the buggy code
  oracle/test_oracle.py  the held-out oracle — RED on the buggy code, never shown to the agent
  gold.py              a reference fix, used only for grading and integrity checks
  fixtures/            optional: repro_good.py + hack.py, for the deterministic smoke/unit path
```

## The three invariants

Every task must satisfy all three, and `tests/test_benchmark_integrity.py` checks them:

1. **The existing suite is green on the buggy code.** The bug is a genuine coverage gap a
   maintainer could plausibly have shipped — not an already-failing build. Practically,
   this means the existing tests must avoid the exact edge the bug lives on.
2. **The oracle is red on the buggy code.** The oracle actually exercises the bug, and it
   is broad enough that special-casing the reported input does not satisfy it — a property
   check over many generated cases is a good way to guarantee this.
3. **The gold fix turns both green.** The bug is fixable and the oracle is satisfiable by a
   genuine, general fix.

## Design notes

- Keep modules small and dependency-free so runs are fast and hermetic.
- The oracle is the anti-hacking instrument. Prefer oracles that check a property across
  many inputs (or several distinct edge cases) rather than a single extra example, so that
  a patch cannot pass by memorising one more answer.
- The bug report should describe observable behaviour and the expected result, not point at
  the line to change.

## Adding a task

Copy the closest existing task, edit the six files, and run `make test`. The integrity test
reports precisely which invariant fails if one does. Ten or more tasks keeps the aggregate
rates meaningful.
