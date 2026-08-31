# redgreen — evaluation results

> gemini model (gemini-3.6-flash) over the full benchmark.

| Metric | Baseline (single-shot) | redgreen (agent) | Change |
| --- | ---: | ---: | ---: |
| Verified-fix rate | 100% | 0% | ▼ -100% |
| Reward-hack rate | 0% | 0% | — +0% |
| Regression rate | 0% | 0% | — +0% |
| Not-fixed rate | 0% | 50% | ▲ +50% |
| Reproduction rate (agent) | — | 50% | — |

Cases graded: 2 per system.

## Verdict breakdown

- **baseline**: VERIFIED_FIX=2
- **agent**: NOT_FIXED=1, NOT_REPRODUCED=1
