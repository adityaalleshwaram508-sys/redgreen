# Voiceover script (≤ 5 minutes)

Spoken narration mapped to the shots in [VIDEO.md](VIDEO.md). Aim for a calm, confident
pace (~150 words/minute). `[Cue]` lines describe what's on screen. Replace `⟨FILL⟩` with
your live numbers from `results/report.md`.

## 0:00–0:25 — The problem
`[On screen: a bug report / GitHub issue open in an editor.]`

"When a bug report lands, the hard part isn't writing the patch — it's the reviewing. Did I
actually reproduce the bug? Does my fix break anything else? And is it a real fix, or did I
just special-case the one input in the report? I built redgreen to do that reviewing for
me, and to hand me the evidence that a fix is actually correct."

## 0:25–1:00 — The baseline
`[On screen: terminal. Run the single-shot baseline on one bug, show the patch, then run it against the oracle and show it fail.]`

"Here's how most of us fix a bug with an LLM today: give it the report and the file, get
back a patch. It looks reasonable. But when I check it against a hidden test the model never
saw, it fails. It's convincing. It's just not correct — and with no ground-truth check,
convincing is all you get."

## 1:00–1:20 — The thesis
`[On screen: the README diagram of the three phases and four gates.]`

"So here's the idea the whole project is built on: an agent will satisfy whatever verifier
you show it. Which means the verifier that *grades* the fix has to be one the agent never
saw. redgreen enforces that with three phases and four gates."

## 1:20–3:20 — One full agent run
`[On screen: run the agent on a task; let the trajectory stream; narrate as it happens.]`

"Watch a real run. First, the Reproducer writes a test for the reported behavior, and runs
it. It goes red. That's the fail-first gate — you can't trust a green test that was never
red.

Now the Fixer takes over. It can edit the module, but it is not allowed to touch any test.
It makes its change, runs everything, and the reproduction goes green while the existing
suite stays green.

Then the Reviewer inspects the diff. Here — the static scan flags a special-case: the patch
hardcoded the reported input. The Reviewer bounces it back, and the Fixer rewrites it as a
real, general fix.

Final verdict: verified fix. And every step I just described is written to a trajectory file
you can read top to bottom — instructions, tool calls, results, and decisions."

## 3:20–4:05 — The result that carries the argument
`[On screen: run make smoke (or make test); show the three-way verdict contrast, then the live results.]`

"This is the part that matters. Three candidate patches for the same bug. The real fix
passes. The no-op fails — the bug's still there. But look at the hack: it special-cases the
reported input, and it passes the fail-first gate, the reproduction, and the full regression
suite. Three green checks. Under any 'do the tests pass' checker, it's a perfect fix. The
held-out oracle is the only thing that catches it — and it names the exact cases it gets
wrong. Same patch, passes its own test, caught by the verifier it never saw.

Across the benchmark, against a fair baseline, verified-fix rate goes from ⟨FILL⟩ to ⟨FILL⟩,
and reward-hacking drops from ⟨FILL⟩ to ⟨FILL⟩."

## 4:05–4:35 — Benchmark and reproducibility
`[On screen: bench/tasks/ folder; then make test going green; the CI tab.]`

"The ten tasks here are a benchmark in their own right — realistic Python bug archetypes,
each with a held-out oracle, built specifically so reward-hacking can be measured. An
integrity test proves every one is well-formed. The core result reproduces with no API key,
and CI runs the whole thing on every push."

## 4:35–5:00 — Human-in-the-loop and close
`[On screen: back to the README top / the evidence bundle.]`

"One more thing: redgreen proposes a fix and its evidence. It never commits, never merges —
a human approves it, because code that can ship is a human's call. And the lesson
generalizes to any agent built on a test suite or a reward signal: separate the verifier the
agent sees from the one that grades it, and keep the objective read-only. That's redgreen.
Thanks for watching."

---

Total spoken length is roughly 4 minutes 15 seconds at a natural pace, leaving room for
pauses and on-screen action while staying under five minutes.
