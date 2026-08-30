# Video script (≤ 5 minutes)

A shot list for the submission video. Times are targets; keep it under five minutes. Show a
terminal and the repo — no slides needed.

## 0:00–0:25 — The problem
"When a bug report lands, the slow part isn't writing the patch — it's the reviewing. Did
you actually reproduce it? Does the fix break anything else? Is it a real fix or a bandaid
that special-cases the one input in the report?" State the persona: a maintainer of a busy
Python library. Frame the goal: a fix you can *prove*, delivered as evidence, not just a
diff.

## 0:25–1:00 — The baseline, and why "looks right" fails
Show the single-shot baseline on one bug: feed the report + module, get a plausible patch.
Run it against the held-out oracle → it fails (or breaks the suite). "Convincing, not
correct. With no ground-truth check, that's all you get."

## 1:00–1:20 — The thesis
"An agent satisfies whatever verifier you show it. So the verifier that *grades* the fix has
to be one the agent never saw." Introduce the four gates and the held-out oracle in one
breath, pointing at the diagram in the README.

## 1:20–3:20 — One full agent run, live
Run the agent on a task and narrate the trajectory as it streams:
- Reproducer writes a test; run it; it goes **red** (fail-first gate passes).
- Fixer edits the module; the reproduction goes **green** and the existing suite stays green.
- Reviewer inspects the diff; show a case where the static scan flags a special-case attempt
  and bounces it back; the Fixer recovers.
- Show the final verdict: VERIFIED_FIX, and open the JSONL trajectory to show it reads top to
  bottom.

## 3:20–4:05 — The result that carries the argument
Run `make smoke` (or point at `make test`). Show the three-way contrast: the `hack`
candidate passes fail-first + repro + regression and is caught *only* by the oracle, which
names the five cases it gets wrong. "Same candidate, passes its own test, caught by the
verifier it never saw." Then show `results/report.md` and the two-bar chart from your live
`make eval`: verified-fix rate up, reward-hack rate down.

## 4:05–4:35 — The benchmark and reproducibility
Flash `bench/tasks/` — ten realistic archetypes, each with a held-out oracle, all validated
by the integrity test. "The benchmark is part of the contribution: it exists to *measure*
reward-hacking." Show `make test` going green and mention CI.

## 4:35–5:00 — Human-in-the-loop and close
"redgreen proposes a patch and its evidence; a human approves it. It never commits." One
sentence on the transferable lesson: separate the verifier the agent sees from the one that
grades it, and keep the objective read-only. End on the passing test count and the repo URL.
