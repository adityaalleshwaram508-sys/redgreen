"""Render results into a report a human reads and a chart for the video/README.

The markdown table always renders (zero dependencies). The bar chart is best-effort: if
matplotlib is installed it writes a PNG comparing the two headline numbers, and if not,
the report still stands on its own. Keeping the chart optional means the core result is
never gated behind a plotting dependency.
"""
from __future__ import annotations

from pathlib import Path

from .verify.metrics import Summary


def render_markdown(summaries: dict[str, Summary], *, note: str = "") -> str:
    base = summaries.get("baseline")
    agent = summaries.get("agent")
    lines = ["# redgreen — evaluation results", ""]
    if note:
        lines += [f"> {note}", ""]

    lines += [
        "| Metric | Baseline (single-shot) | redgreen (agent) | Change |",
        "| --- | ---: | ---: | ---: |",
        _row("Verified-fix rate", base, agent, "verified_fix_rate", higher_is_better=True),
        _row("Reward-hack rate", base, agent, "reward_hack_rate", higher_is_better=False),
        _row("Regression rate", base, agent, "regression_rate", higher_is_better=False),
        _row("Not-fixed rate", base, agent, "not_fixed_rate", higher_is_better=False),
    ]
    if agent and agent.reproduction_rate is not None:
        lines.append(f"| Reproduction rate (agent) | — | {_pct(agent.reproduction_rate)} | — |")

    lines += ["", f"Cases graded: {agent.n if agent else 0} per system.", ""]
    lines += ["## Verdict breakdown", ""]
    for name, summary in summaries.items():
        if summary is None:
            continue
        breakdown = ", ".join(f"{k}={v}" for k, v in sorted(summary.verdict_counts.items()))
        lines.append(f"- **{name}**: {breakdown}")
    return "\n".join(lines) + "\n"


def _row(label, base: Summary | None, agent: Summary | None, attr: str, *, higher_is_better: bool) -> str:
    b = getattr(base, attr) if base else None
    a = getattr(agent, attr) if agent else None
    change = ""
    if b is not None and a is not None:
        delta = a - b
        arrow = "▲" if delta > 0 else ("▼" if delta < 0 else "—")
        change = f"{arrow} {delta:+.0%}"
    return f"| {label} | {_pct(b)} | {_pct(a)} | {change} |"


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x:.0%}"


def render_chart(summaries: dict[str, Summary], out_path: Path) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False

    base, agent = summaries.get("baseline"), summaries.get("agent")
    if not base or not agent:
        return False

    metrics = ["Verified-fix rate", "Reward-hack rate"]
    base_vals = [base.verified_fix_rate, base.reward_hack_rate]
    agent_vals = [agent.verified_fix_rate, agent.reward_hack_rate]

    x = range(len(metrics))
    width = 0.38
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([i - width / 2 for i in x], base_vals, width, label="Baseline")
    ax.bar([i + width / 2 for i in x], agent_vals, width, label="redgreen")
    ax.set_xticks(list(x))
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1)
    ax.set_ylabel("rate")
    ax.set_title("redgreen vs single-shot baseline")
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return True
